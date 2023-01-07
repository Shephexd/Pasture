from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CorrelationViewSet, PerformanceViewSet

router = DefaultRouter()
router.register("corr", CorrelationViewSet)

urlpatterns = [
    path("backtest", PerformanceViewSet.as_view({"post": "backtest_portfolio"})),
    path("metric", PerformanceViewSet.as_view({"post": "calc_metric"})),
] + router.urls
