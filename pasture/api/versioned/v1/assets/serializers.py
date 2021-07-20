from rest_framework import serializers
from pasture.assets.models import Asset, DailyPrice, AssetUniverse


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = "__all__"


class DailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPrice
        fields = ('symbol', 'base_date', 'open', 'close', 'high', 'low', 'adj_close')


class AssetUniverseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetUniverse
        fields = '__all__'
