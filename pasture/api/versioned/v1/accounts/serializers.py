from rest_framework import serializers

from pasture.accounts.models import TradeHistory, OrderHistory


class AccountTradeHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeHistory
        fields = "__all__"


class AccountTradeAggSerializer(serializers.Serializer):
    trade_type = serializers.CharField(max_length=50)
    trade_amt = serializers.DecimalField(decimal_places=5, max_digits=20)
    settle_amt = serializers.DecimalField(decimal_places=5, max_digits=20)
    tax_amt = serializers.DecimalField(decimal_places=5, max_digits=20)
    vat_amt = serializers.DecimalField(decimal_places=5, max_digits=20)


class AccountHistoryOutputSerializer(serializers.Serializer):
    trade_date = serializers.DateTimeField(format="%Y-%m-%d")
    BASE = serializers.DecimalField(max_digits=20, decimal_places=1)
    DIVIDEND_INPUT_USD = serializers.DecimalField(max_digits=20, decimal_places=2)
    DEPOSIT_INTEREST = serializers.DecimalField(max_digits=20, decimal_places=1)


class AccountOrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = "__all__"


class AccountEvaluationHistorySerializer(serializers.Serializer):
    base_date = serializers.DateTimeField(format="%Y-%m-%d")
    # amount = serializers.DecimalField(max_digits=20, decimal_places=2)
    amount = serializers.FloatField()


class AssetsEvaluationHistorySerializer(serializers.Serializer):
    symbols = serializers.ListField(child=serializers.CharField(max_length=10))
    history = serializers.ListField(child=serializers.DictField())
