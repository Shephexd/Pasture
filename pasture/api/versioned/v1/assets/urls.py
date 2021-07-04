from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetViewSet, DailyPriceViewSet, AssetUniverseViewSet

router = DefaultRouter()
router.register(r'prices', DailyPriceViewSet)
router.register(r'', AssetViewSet)


urlpatterns = [
    path('universe', AssetUniverseViewSet.as_view({'get': 'list'})),
    path('universe/<universe_id>', AssetUniverseViewSet.as_view({'get': 'list'})),
    path('', include(router.urls)),
]
