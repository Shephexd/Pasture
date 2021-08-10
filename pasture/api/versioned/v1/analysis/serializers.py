from rest_framework import serializers
from pasture.assets.models import Asset, DailyPrice, AssetUniverse


class CorrRowSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
    value = serializers.FloatField()


class CorrListSerializer(serializers.ListSerializer):
    child = CorrRowSerializer()

    def to_internal_value(self, data):
        data = [self.to_internal_row(row) for row in data]
        return super().to_internal_value(data=sum(data, []))

    def to_internal_row(self, data):
        source, targets = data
        values = []
        for _t, value in targets.iteritems():
            values.append({'source': source, 'target': _t, 'value': round(value, 2)})
        return values


class PortfolioRowSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    weight = serializers.DecimalField(max_digits=7, decimal_places=4)
