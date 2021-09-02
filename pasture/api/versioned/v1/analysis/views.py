import logging
import pandas as pd
from rest_framework import exceptions
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from pasture.common.viewset import SerializerMapMixin
from pasture.assets.models import Asset, DailyPrice, AssetUniverse
from pasture.api.versioned.v1.assets.serializers import AssetSerializer
from pasture.api.versioned.v1.assets.filters import DailyPriceFilterSet

from linchfin.base.dataclasses.entities import Portfolio, Weights
from linchfin.base.dataclasses.value_types import TimeSeries, Feature
from linchfin.core.portfolio.hierarchical import HierarchyRiskParityEngine
from linchfin.core.analysis.profiler import AssetProfiler
from linchfin.common.calc import calc_daily_returns, calc_corr, calc_portfolio_return
from .serializers import (
    CorrInputSerializer,
    DistanceListSerializer, PortfolioRowSerializer,
    BacktestInputSerializer
)

logger = logging.getLogger('pasture')


class UniverseLookupMixin:
    def get_universe(self, **kwargs):
        universe = AssetUniverse.objects.filter(**kwargs)
        universe_count = universe.count()
        if universe_count > 1:
            raise exceptions.ValidationError({"detail": "matched universe must be unique"})
        if universe_count == 0:
            raise exceptions.NotFound({"detail": "no matched universe"})
        return universe.get()

    def get_pivot(self, queryset, values='close'):
        ts = TimeSeries(pd.DataFrame(queryset.values()))
        if not ts.empty:
            ts = ts.pivot(index='base_date', values=values, columns='symbol').astype(float)
            ts.index = pd.to_datetime(ts.index)
        return ts


class CorrelationViewSet(SerializerMapMixin, UniverseLookupMixin,
                         mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = AssetSerializer
    queryset = DailyPrice.objects.all()
    filterset_class = DailyPriceFilterSet
    lookup_field = 'universe_id'
    _cluster = HierarchyRiskParityEngine(asset_universe=[])
    serializer_class_map = {
        'create': CorrInputSerializer
    }

    def get_prices(self, symbols):
        queryset = self.filter_queryset(self.queryset).filter(symbol__in=symbols)
        return self.get_pivot(queryset=queryset)

    def get(self, request, *args, **kwargs):
        universe = self.get_universe(**kwargs)
        ts = self.get_prices(symbols=universe.symbols)
        corr = ts.calc_corr(periods=5)
        dist = self._cluster.distance_encoder.encode(corr=corr)
        linkage = self._cluster.calc_linkage(dist)
        diag_indices = self._cluster.get_quansi_diag(linkage)
        _sorted_dist = self._cluster.get_sorted_corr(corr=dist.value, indices=diag_indices)
        w = self._cluster.get_recursive_bisect(corr=corr, sort_ix=diag_indices)
        w.index = corr.columns[w.index]
        asset_description = {i['symbol']: i for i in Asset.objects.filter(symbol__in=w.index).values()}
        distance_serializer = DistanceListSerializer(data=list(_sorted_dist.iterrows()))
        asset_serializer = PortfolioRowSerializer(data=[
            {'symbol': i, 'weight': round(w * 100, 3)} for i, w in w.iteritems()],
            context={'asset_description': asset_description}, many=True)
        distance_serializer.is_valid(raise_exception=True)
        asset_serializer.is_valid(raise_exception=True)
        return Response({'distances': distance_serializer.data, 'portfolio': asset_serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ts = self.get_prices(symbols=serializer.validated_data['symbols'])
        if ts.empty:
            raise exceptions.ValidationError("No TimeSeries for correlation")
        corr = ts.calc_corr(periods=serializer.validated_data['min_periods'])
        corr_serializer = DistanceListSerializer(data=list(corr.value.iterrows()))
        corr_serializer.is_valid(raise_exception=True)
        return Response({'corr': corr_serializer.data})


class PerformanceViewSet(SerializerMapMixin, UniverseLookupMixin, viewsets.ModelViewSet):
    serializer_class = AssetSerializer
    queryset = DailyPrice.objects.all()
    filterset_class = DailyPriceFilterSet
    lookup_field = 'universe_id'
    serializer_class_map = {
        'backtest_portfolio': BacktestInputSerializer
    }

    def calc_performance(self, request, *args, **kwargs):
        universe = self.get_universe(**kwargs)
        asset_profiler = AssetProfiler()
        queryset = self.filter_queryset(self.queryset).filter(symbol__in=universe.symbols + [asset_profiler.bm_ticker])
        time_series = self.get_pivot(queryset=queryset)
        profiled = asset_profiler.profile(prices=time_series, factors=['sharp_ratio', 'beta', 'cumulative_returns'])
        profiled = profiled.round(3)
        return Response(profiled.reset_index().to_dict(orient='records'))

    def backtest_universe(self, request, *args, **kwargs):
        universe = self.get_universe(**kwargs)
        queryset = self.filter_queryset(self.queryset).filter(symbol__in=universe.symbols)
        time_series = self.get_pivot(queryset=queryset).dropna(axis=0)
        daily_returns = calc_daily_returns(time_series)
        w = {row['symbol']: row['weight'] for row in request.data['portfolio']}
        port = Portfolio(weights=w)
        portfolio_returns = calc_portfolio_return(portfolio=port, daily_returns=daily_returns)
        return Response([{'x': i, 'y': row / 100} for i, row in portfolio_returns.iteritems()])

    def backtest_portfolio(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        port = Portfolio(weights=serializer.validated_data['weights'])

        filter_kwargs = {
            'base_date__gte': serializer.validated_data['from_date'],
            'base_date__lte': serializer.validated_data['to_date']
        }
        queryset = self.queryset.filter(symbol__in=port.symbols, **filter_kwargs)
        ts = self.get_pivot(queryset=queryset).dropna(axis=0)
        if ts.empty:
            raise exceptions.ValidationError("No TimeSeries for backtest")
        daily_returns = calc_daily_returns(ts)

        portfolio_returns = calc_portfolio_return(portfolio=port, daily_returns=daily_returns)
        return Response([{'x': i, 'y': row / 100} for i, row in portfolio_returns.iteritems()])
