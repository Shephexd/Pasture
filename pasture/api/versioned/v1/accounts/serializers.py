from rest_framework import serializers

from pasture.accounts.models import Account, Settlement, TradeHistory, OrderHistory


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = "__all__"


class AccountSettlementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Settlement
        fields = ("base_date", "base_io_krw", "base_io_usd", "dividend_usd", "deposit_interest_krw", "base_amount_krw",
                  "account_evaluation_krw", "account_evaluation_usd", "stock_evaluation_krw", "stock_evaluation_usd",
                  "exchange_rate", "exchange_rate")


class AccountDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ("owner", "account_alias", "account_type", "is_active", "description", "settlement")

    settlement = serializers.SerializerMethodField(default={})

    def get_settlement(self, instance):
        if not isinstance(instance, Account):
            return {}

        account: Account = instance
        if not account.settlements.exists():
            return {}
        serializer = AccountSettlementSerializer(account.settlements.last())
        return serializer.data


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
    BASE_KRW = serializers.DecimalField(max_digits=20, decimal_places=1)
    BASE_USD = serializers.DecimalField(max_digits=20, decimal_places=1)
    BASE = serializers.DecimalField(max_digits=20, decimal_places=1)
    DIVIDEND_INPUT_USD = serializers.DecimalField(max_digits=20, decimal_places=2)
    DEPOSIT_INTEREST = serializers.DecimalField(max_digits=20, decimal_places=1)


class AccountOrderHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderHistory
        fields = "__all__"


class AccountEvaluationHistorySerializer(serializers.Serializer):
    class RowSerializer(serializers.Serializer):
        base_date = serializers.DateTimeField(format="%Y-%m-%d")
        eval_amount = serializers.DecimalField(decimal_places=3, max_digits=20)
        buy_amount = serializers.DecimalField(decimal_places=3, max_digits=20)

    history = RowSerializer(many=True)


class AccountHoldingsHistorySerializer(serializers.Serializer):
    class RowSerializer(serializers.Serializer):
        base_date = serializers.DateTimeField(format="%Y-%m-%d")
        symbol = serializers.CharField(max_length=10)
        qty = serializers.DecimalField(decimal_places=3, max_digits=20)

    history = RowSerializer(many=True)


class AssetsEvaluationHistorySerializer(serializers.Serializer):
    class RowSerializer(serializers.Serializer):
        base_date = serializers.DateTimeField(format="%Y-%m-%d")
        symbol = serializers.CharField(max_length=10)
        evaluation = serializers.FloatField()

    history = RowSerializer(many=True)
