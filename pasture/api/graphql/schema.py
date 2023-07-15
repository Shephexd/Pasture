from graphene import Field, List, ObjectType, Float, String, Schema

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from graphene import Field, List, ObjectType, Float, String, Schema

from pasture.accounts.models import Account, Settlement, TradeHistory, OrderHistory, Holding
from pasture.api.graphql.django import *
from pasture.assets.models import Asset, AssetUniverse, DailyPrice
from pasture.portfolio.models import Portfolio


class AssetUniverseDetailType(ObjectType):
    universe = Field(AssetUniverseType)
    asset = List(AssetType)


class PortfolioDetailType(ObjectType):
    portfolio = Field(PortfolioType)
    prices = List(DailyPriceType)


class DividendType(ObjectType):
    dividend_total = Field(Float)
    dividend_last_month = Field(Float)


class AccountDetailType(ObjectType):
    profile = Field(AccountType)
    settlement = Field(SettlementType)
    holdings = List(HoldingType)
    trades = List(TradeHistoryType)
    dividend = Field(DividendType)
    orders = List(OrderHistoryType)

    def resolve_orders(root, info):
        account_alias = root["account"].account_alias
        return OrderHistory.objects.filter(account_alias=account_alias)

    def resolve_trades(root, info):
        account_alias = root["account"].account_alias
        trades = TradeHistory.objects.filter(account_alias=account_alias)
        return trades

    def resolve_dividend(root, info):
        account_alias = root["account"].account_alias
        dividend_trades = TradeHistory.objects.filter(account_alias=account_alias, trade_type="DIVIDEND_INPUT_USD")
        dividend_last_month = list(dividend_trades.annotate(month=TruncMonth("trade_date")).values("month").annotate(
            dividend=Sum("settle_amt")))[-1]
        return {
            "dividend_total": sum(dividend_trades.values_list("settle_amt", flat=True)),
            "dividend_last_month": dividend_last_month["dividend"]
        }

    def resolve_holdings(root, info):
        account_alias = root["account"].account_alias
        holding_qs = Holding.objects.filter(account_alias=account_alias)
        return holding_qs.filter(base_date=holding_qs.latest("base_date").base_date)

    def resolve_settlement(root, info):
        account_alias = root["account"].account_alias
        settlement = Settlement.objects.filter(account_alias=account_alias).latest("base_date")
        return settlement


class Query(ObjectType):
    universe_detail = Field(AssetUniverseDetailType, name=String(required=True))
    portfolio_detail = Field(PortfolioDetailType)
    account_detail = Field(AccountDetailType, account_alias=String(required=True))

    def resolve_viewer(self, info, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            raise Exception("Authentication credentials were not provided")
        return user

    def resolve_universe_detail(root, info, name):
        _universe = AssetUniverse.objects.get(name=name)
        return {
            "universe": _universe,
            "asset": Asset.objects.filter(symbol__in=_universe.symbols)
        }

    def resolve_portfolio_detail(root, info):
        portfolio = Portfolio.objects.order_by("base_date").last()
        symbols = [w["symbol"] for w in portfolio.weights]
        lsat_price = DailyPrice.objects.order_by("-base_date").first()
        return {
            "portfolio": portfolio,
            "prices": DailyPrice.objects.filter(symbol__in=symbols, base_date=lsat_price.base_date)
        }

    def resolve_account_detail(root, info, account_alias):
        acct = Account.objects.get(account_alias=account_alias)
        return {"account": acct}


schema = Schema(query=Query)
