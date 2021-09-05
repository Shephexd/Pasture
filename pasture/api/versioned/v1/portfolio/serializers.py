from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from pasture.portfolio.models import Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ('id', 'weights')

    def validate_weights(self, weights):
        if sum([w['weight'] for w in weights]) != 1:
            raise ValidationError("sum of weights must be 1")
        return weights


class PortfolioInputSerializer(serializers.Serializer):
    symbols = serializers.ListSerializer(child=serializers.CharField(), help_text="asset symbol")
    min_periods = serializers.IntegerField(default=5, help_text="min periods")
    from_date = serializers.DateField(help_text="from date")
    to_date = serializers.DateField(help_text="to date")


class CorrRowSerializer(serializers.Serializer):
    source = serializers.CharField()
    target = serializers.CharField()
    value = serializers.FloatField()


class DistanceListSerializer(serializers.ListSerializer):
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

    def to_internal_value(self, data):
        data['symbol'] = data['symbol'].upper()
        return data


class PortfolioOutputSerializer(serializers.Serializer):
    rows = PortfolioRowSerializer(many=True)

    def to_internal_value(self, data):
        data['rows'] = [{'symbol': r['symbol'], 'weight': round(r['weight'], 3)} for r in data['rows']]
        while sum([r['weight'] for r in data['rows']]) != 1:
            data['rows'][-1]['weight'] += round(1 - sum([r['weight'] for r in data['rows']]), 3)
        return data
