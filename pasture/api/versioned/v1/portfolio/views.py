import logging

from rest_framework import viewsets, response, exceptions

from linchfin.common.calc import calc_opt_shares
from linchfin.core.portfolio.rules import RuleEngine
from linchfin.models.hrp import (
    HierarchyRiskParityModel,
    AttentionHRPModel,
    SharpAttentionHRPModel,
)
from linchfin.services.portfolio import PortfolioService
from linchfin.value.objects import TimeSeriesRow
from pasture.assets.models import DailyPrice
from pasture.common.viewset import SerializerMapMixin, QuerysetMapMixin
from pasture.portfolio.models import Portfolio
from .filters import PortfolioAssetFilterSet
from .serializers import (
    PortfolioInputSerializer,
    PortfolioSerializer,
    SimulatePortfolioQtySerializer,
)

logger = logging.getLogger("pasture")


class PortfolioViewSet(
    SerializerMapMixin, QuerysetMapMixin, viewsets.ModelViewSet
):
    serializer_class = PortfolioSerializer
    queryset = Portfolio.objects.all()
    filterset_class = PortfolioAssetFilterSet

    serializer_class_map = {
        "run_model": PortfolioInputSerializer,
        "calc_shares": PortfolioInputSerializer,
    }
    queryset_map = {
        "run_model": DailyPrice.objects.all(),
        "calc_shares": DailyPrice.objects.all(),
    }
    model_class_map = {
        "HRP": HierarchyRiskParityModel,
        "AHRP": AttentionHRPModel,
        "SAHRP": SharpAttentionHRPModel,
    }

    def get_latest(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset()).order_by("-base_date")
        instance = qs.first()
        serializer = self.get_serializer(instance)
        return response.Response(serializer.data)

    def run_model(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        symbols = serializer.validated_data["symbols"]
        filter_kwargs = {
            "symbol__in": symbols,
            "base_date__gte": serializer.validated_data["from_date"],
            "base_date__lte": serializer.validated_data["to_date"],
        }

        queryset = self.get_queryset().filter(**filter_kwargs)
        port_service = PortfolioService(repo=queryset)
        model_class = self.model_class_map[serializer.validated_data["model"]]
        model_instance = model_class(asset_universe=symbols)

        ts = port_service.get_time_series(symbols=symbols)

        if ts.empty:
            raise exceptions.ValidationError(
                "Matched data is empty, check symbols and periods"
            )
        portfolio = port_service.run(model=model_instance, x=ts)
        portfolio.weights = RuleEngine.run(
            portfolio_weights=portfolio.weights, decimal_points=3
        )
        return response.Response(
            {"weights": portfolio.to_list(), "base_date": portfolio.base_date}
        )

    def calc_shares(self, request, *args, **kwargs):
        input_serializer = SimulatePortfolioQtySerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        weights = TimeSeriesRow(input_serializer.data["weights"])
        symbols = list(weights.index)

        queryset = self.get_queryset().filter(symbol__in=symbols)
        latest_date = queryset.latest("base_date").base_date
        queryset = queryset.filter(base_date=latest_date)

        current_prices = self.get_last_prices(queryset, symbols)
        opt_shares = calc_opt_shares(
            base=input_serializer.validated_data["base"],
            weights=weights,
            current_price=current_prices,
        )
        return response.Response({"shares": opt_shares.round(1).to_dict()})
