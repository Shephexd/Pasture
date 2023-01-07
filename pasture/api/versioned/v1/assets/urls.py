from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AssetViewSet,
    DailyPriceViewSet,
    DailyPriceChangeViewSet,
    AssetUniverseViewSet,
)

router = DefaultRouter()
router.register(r"prices", DailyPriceViewSet)
router.register(r"universe", AssetUniverseViewSet)
router.register(r"", AssetViewSet)


urlpatterns = [
    path(
        "prices/changes/", DailyPriceChangeViewSet.as_view({"get": "get_pct_changes"})
    ),
    path("universe", AssetUniverseViewSet.as_view({"get": "list"})),
    path("universe/<universe_id>", AssetUniverseViewSet.as_view({"get": "list"})),
] + router.urls
