import logging
import pandas as pd
from rest_framework import viewsets, mixins, response, exceptions

from linchfin.base.dataclasses.values import TimeSeries
from linchfin.common.calc import calc_daily_returns, calc_portfolio_return
from linchfin.core.portfolio.hierarchical import HierarchyRiskParityEngine
from pasture.assets.models import Asset, DailyPrice
from pasture.portfolio.models import Portfolio
from pasture.common.viewset import SerializerMapMixin, QuerysetMapMixin
from .serializers import (
    PortfolioInputSerializer, PortfolioOutputSerializer,
    PortfolioSerializer, DistanceListSerializer,
)

logger = logging.getLogger('pasture')


class DailyPriceMixin(viewsets.GenericViewSet):
    def get_prices(self, queryset, symbols):
        queryset = queryset.filter(symbol__in=symbols)
        return self.get_pivot(queryset=queryset)

    def get_pivot(self, queryset, values='close'):
        ts = TimeSeries(pd.DataFrame(queryset.values()))
        if not ts.empty:
            ts = ts.pivot(index='base_date', values=values, columns='symbol').astype(float)
            ts.index = pd.to_datetime(ts.index)
        return ts


class PortfolioViewSet(DailyPriceMixin, viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    queryset = Portfolio.objects.all()


class HierarchicalRiskParityViewSet(DailyPriceMixin, SerializerMapMixin, QuerysetMapMixin,
                                    mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = PortfolioSerializer
    queryset = DailyPrice.objects.all()
    _cluster = HierarchyRiskParityEngine(asset_universe=[])
    serializer_class_map = {
        'create': PortfolioInputSerializer
    }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        filter_kwargs = {
            'base_date__gte': serializer.validated_data['from_date'],
            'base_date__lte': serializer.validated_data['to_date']
        }
        queryset = self.filter_queryset(self.get_queryset()).filter(**filter_kwargs)

        ts = self.get_prices(queryset=queryset, symbols=serializer.validated_data['symbols'])
        corr = ts.calc_corr(periods=5)
        dist = self._cluster.distance_encoder.encode(corr=corr)
        linkage = self._cluster.calc_linkage(dist)
        diag_indices = self._cluster.get_quansi_diag(linkage)
        _sorted_dist = self._cluster.get_sorted_corr(corr=dist.value, indices=diag_indices)
        w = self._cluster.get_recursive_bisect(corr=corr, sort_ix=diag_indices)
        w.index = corr.columns[w.index]
        asset_description = {i['symbol']: i for i in Asset.objects.filter(symbol__in=w.index).values()}
        distance_serializer = DistanceListSerializer(data=list(_sorted_dist.iterrows()))
        asset_serializer =\
            PortfolioOutputSerializer(data={'rows': [{'symbol': i, 'weight': w} for i, w in w.iteritems()]})
        distance_serializer.is_valid(raise_exception=True)
        asset_serializer.is_valid(raise_exception=True)
        return response.Response({'distances': distance_serializer.data, 'portfolio': asset_serializer.data['rows']})
