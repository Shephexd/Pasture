from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AccountViewSet, AccountTradeViewSet, AccountOrderViewSet

router = DefaultRouter()
router.register("", AccountViewSet)
router.register("trades", AccountTradeViewSet)
router.register("orders", AccountOrderViewSet)

urlpatterns = [
                  path("trade/groupby", AccountTradeViewSet.as_view({"get": "get_groupby"})),
                  path("amount/history", AccountTradeViewSet.as_view({"get": "get_history"})),
                  path(
        "holdings/history", AccountOrderViewSet.as_view({"get": "get_holding_history"})
    ),
    path(
        "evaluation/history",
        AccountOrderViewSet.as_view({"get": "get_evaluation_history"}),
    ),
    path(
        "assets/evaluation/history",
        AccountOrderViewSet.as_view({"get": "get_assets_evaluation_history"}),
    ),
] + router.urls
