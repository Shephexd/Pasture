from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssetViewSet,
    DailyPriceViewSet, DailyPriceChangeViewSet,
    AssetUniverseViewSet, AssetNetworkViewSet
)

router = DefaultRouter()
router.register(r'prices', DailyPriceViewSet)
router.register(r'', AssetViewSet)


urlpatterns = [
    path('prices/changes/', DailyPriceChangeViewSet.as_view({'get': 'get_pct_changes'})),
    path('network', AssetNetworkViewSet.as_view({'get': 'list'})),
    path('network/cluster', AssetNetworkViewSet.as_view({'get': 'get_cluster'})),
    path('universe', AssetUniverseViewSet.as_view({'get': 'list'})),
    path('universe/<universe_id>', AssetUniverseViewSet.as_view({'get': 'list'})),
] + router.urls
