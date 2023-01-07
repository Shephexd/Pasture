from django.utils import timezone
from rest_framework import serializers


class CorrInputSerializer(serializers.Serializer):
    symbols = serializers.ListSerializer(
        child=serializers.CharField(), help_text="asset symbol"
    )
    min_periods = serializers.IntegerField(default=5, help_text="min periods")


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
    category = serializers.HiddenField(default="")
    sub_category = serializers.HiddenField(default="")

    def to_internal_value(self, data):
        data["symbol"] = data["symbol"].upper()
        return data

    def get_category(self, obj):
        _asset_description = self.get_asset_description(symbol=obj["symbol"])
        return _asset_description.get("category", "UNDEFINED")

    def get_sub_category(self, obj):
        _asset_description = self.get_asset_description(symbol=obj["symbol"])
        return _asset_description.get("sub_category", "UNDEFINED")

    def get_asset_description(self, symbol):
        _desc = self.context.get("asset_description", {})
        return _desc.get(symbol, {})

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["category"] = self.get_category(instance)
        representation["sub_category"] = self.get_sub_category(instance)
        return representation


class PerformanceInputSerializer(serializers.Serializer):
    portfolio = serializers.ListField(
        help_text="asset weights", child=PortfolioRowSerializer()
    )
    from_date = serializers.DateField(
        help_text="backtest start date",
        default=lambda: timezone.now().date() - timezone.timedelta(days=365),
    )
    to_date = serializers.DateField(
        help_text="backtest end date", default=timezone.now().date()
    )
    bench_marks = serializers.ListField(
        help_text="target bench mart assets", default=["SPY"]
    )

    def validate_portfolio(self, port):
        if sum([float(w["weight"]) for w in port]) != 1:
            raise ValueError("weight sum must be 1")
        return port


class MetricOutputSerializer(serializers.Serializer):
    metrics = serializers.ListField(
        help_text="metric", child=serializers.DictField(help_text="metric")
    )
    factor_keys = serializers.SerializerMethodField(help_text="metric keys")
    asset_keys = serializers.SerializerMethodField(help_text="metric keys")

    def get_factor_keys(self, attrs):
        return [m["index"] for m in attrs["metrics"]]

    def get_asset_keys(self, attrs):
        asset_keys = set(sum([list(m.keys()) for m in attrs["metrics"]], [])) - {
            "index"
        }
        return asset_keys
