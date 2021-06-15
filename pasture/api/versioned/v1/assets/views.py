from rest_framework import views, viewsets
from pasture.api.base.assets.models import Asset, DailyPrice
from .serializers import AssetSerializer, DailyPriceSerializer


class AssetViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AssetSerializer
    queryset = Asset.objects.all()


class DailyPriceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = DailyPriceSerializer
    queryset = DailyPrice.objects.all()
