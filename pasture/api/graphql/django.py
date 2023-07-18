from graphene_django import DjangoObjectType
from graphene_django import DjangoObjectType

from pasture.accounts.models import Account, Settlement, TradeHistory, OrderHistory
from pasture.accounts.models import Holding
from pasture.assets.models import Asset, AssetUniverse, DailyPrice
from pasture.portfolio.models import Portfolio


class SettlementType(DjangoObjectType):
    class Meta:
        get_latest_by = "base_date"
        model = Settlement
        fields = "__all__"


class OrderHistoryType(DjangoObjectType):
    class Meta:
        model = OrderHistory
        fields = "__all__"


class TradeHistoryType(DjangoObjectType):
    class Meta:
        model = TradeHistory
        fields = "__all__"


class AccountType(DjangoObjectType):
    class Meta:
        model = Account
        fields = "__all__"


class PortfolioType(DjangoObjectType):
    class Meta:
        model = Portfolio
        fields = "__all__"


class AssetType(DjangoObjectType):
    class Meta:
        model = Asset
        fields = ("id", "name", "symbol")


class DailyPriceType(DjangoObjectType):
    class Meta:
        model = DailyPrice
        fields = "__all__"


class AssetUniverseType(DjangoObjectType):
    class Meta:
        model = AssetUniverse
        fields = ("id", "name", "symbols", "asset")


class HoldingType(DjangoObjectType):
    class Meta:
        model = Holding
        fields = ("id", "base_date", "account_alias", "symbol",
                  "eval_amt", "market_price", "holding_qty", "buy_qty", "sell_qty")
