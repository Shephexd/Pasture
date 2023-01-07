from typing import List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from pasture.portfolio.models import Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Portfolio
        fields = ("id", "weights")

    def validate_weights(self, weights):
        if sum([w["weight"] for w in weights]) != 1:
            raise ValidationError("sum of weights must be 1")
        return weights


class PortfolioInputSerializer(serializers.Serializer):
    symbols = serializers.ListSerializer(
        child=serializers.CharField(), help_text="asset symbol"
    )
    model = serializers.ChoiceField(
        default="HRP",
        help_text="min periods",
        choices=[
            ("HRP", "HRP"),
            ("AHRP", "AHRP"),
            ("SAHRP", "SAHRP"),
        ],
    )
    from_date = serializers.DateField(help_text="from date")
    to_date = serializers.DateField(help_text="to date")

    def validate_symbols(self, symbols: List[str]):
        if len(symbols) < 2:
            raise ValidationError("symbols must be more than 2")
        return symbols


class SimulatePortfolioQtySerializer(serializers.Serializer):
    base = serializers.DecimalField(max_digits=20, decimal_places=3)
    weights = serializers.ListField()

    def validate_weights(self, weights):
        if round(sum([w["weight"] for w in weights]), 5) != 1:
            raise ValidationError("Sum of weights must be 1")
        return weights

    def to_representation(self, instance):
        representation = super().to_representation(instance=instance)
        weights = dict()

        for row in representation["weights"]:
            weights[row["symbol"]] = row["weight"]
        representation["weights"] = weights
        return representation


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
            values.append({"source": source, "target": _t, "value": round(value, 2)})
        return values


class PortfolioRowSerializer(serializers.Serializer):
    symbol = serializers.CharField()
    weight = serializers.DecimalField(max_digits=7, decimal_places=4)

    def to_internal_value(self, data):
        data["symbol"] = data["symbol"].upper()
        return data


class PortfolioOutputSerializer(serializers.Serializer):
    rows = PortfolioRowSerializer(many=True)

    def to_internal_value(self, data):
        data["rows"] = [
            {"symbol": r["symbol"], "weight": round(r["weight"], 3)}
            for r in data["rows"]
        ]
        while sum([r["weight"] for r in data["rows"]]) != 1:
            data["rows"][-1]["weight"] += round(
                1 - sum([r["weight"] for r in data["rows"]]), 3
            )
        return data
