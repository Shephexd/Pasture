from rest_framework import serializers

from pasture.assets.models import Asset, DailyPrice, AssetUniverse


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = "__all__"


class SimpleAssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = ("asset_type", "symbol", "category", "sub_category", "description")


class DailyPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyPrice
        fields = ("symbol", "base_date", "open", "close", "high", "low", "adj_close")


class AssetUniverseSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetUniverse
        fields = "__all__"

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        asset_map = {s: {"symbol": s} for s in representation["symbols"]}
        assets = Asset.objects.filter(symbol__in=representation["symbols"])
        asset_serializer = SimpleAssetSerializer(assets, many=True)
        for _asset in asset_serializer.data:
            asset_map[_asset["symbol"]] = _asset
        representation["assets"] = list(asset_map.values())
        return representation
