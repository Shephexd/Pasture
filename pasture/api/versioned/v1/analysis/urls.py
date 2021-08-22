from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CorrelationViewSet,
    PerformanceViewSet
)

router = DefaultRouter()

urlpatterns = [
    path('corr/<universe_id>', CorrelationViewSet.as_view({'get': 'get'})),
    path('backtest', PerformanceViewSet.as_view({'post': 'backtest_portfolio'})),
    path('backtest/<universe_id>', PerformanceViewSet.as_view({'post': 'backtest_universe'})),
    path('profile/<universe_id>', PerformanceViewSet.as_view({'get': 'calc_performance'})),
] + router.urls
