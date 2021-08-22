from rest_framework import serializers


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
    category = serializers.HiddenField(default='')
    sub_category = serializers.HiddenField(default='')

    def to_internal_value(self, data):
        data['symbol'] = data['symbol'].upper()
        return data

    def get_category(self, obj):
        _asset_description = self.get_asset_description(symbol=obj['symbol'])
        return _asset_description.get('category', 'UNDEFINED')

    def get_sub_category(self, obj):
        _asset_description = self.get_asset_description(symbol=obj['symbol'])
        return _asset_description.get('sub_category', 'UNDEFINED')

    def get_asset_description(self, symbol):
        _desc = self.context.get('asset_description', {})
        return _desc.get(symbol, {})

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['category'] = self.get_category(instance)
        representation['sub_category'] = self.get_sub_category(instance)
        return representation
