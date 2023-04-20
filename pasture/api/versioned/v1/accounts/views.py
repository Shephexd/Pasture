import datetime

import pandas as pd
from rest_framework import viewsets
from rest_framework.response import Response

from linchfin.value.objects import TimeSeries
from pasture.accounts.models import Settlement, OrderHistory, TradeHistory
from pasture.assets.models import DailyPrice
from pasture.common.viewset import (
    SerializerMapMixin,
    QuerysetMapMixin,
    DailyPriceMixin,
    ExchangeMixin,
)
from .filters import TradeFilterSet, OrderFilterSet
from .serializers import (
    AccountSettlementSerializer,
    AccountTradeHistorySerializer,
    AccountOrderHistorySerializer,
    AccountTradeAggSerializer,
    AccountHistoryOutputSerializer,
    AssetsEvaluationHistorySerializer,
    AccountEvaluationHistorySerializer,
    AccountHoldingsHistorySerializer,
)

ASK = "01"
BID = "02"
TRADE_TAX = 0.15 / 100


class AccountViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Settlement.objects.all()
    serializer_class = AccountSettlementSerializer
    lookup_field = "base_date"
    lookup_url_kwarg = "base_date"

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)
        return queryset.filter(account_alias=self.request.user)


class AccountTradeViewSet(
    ExchangeMixin, DailyPriceMixin, viewsets.ReadOnlyModelViewSet
):
    queryset = TradeHistory.objects.order_by("trade_date").all()
    serializer_class = AccountTradeHistorySerializer
    filterset_class = TradeFilterSet
    lookup_field = "account_alias"

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset=queryset)
        return queryset.filter(account_alias=self.request.user)

    def get_groupby(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = AccountTradeAggSerializer(queryset.get_groupby(), many=True)
        return Response(serializer.data)

    def get_history(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.queryset)
        ts = self.pivot_history(queryset=queryset)

        _base_krw = ts.DEPOSIT_KRW + ts.WITHDRAW_KRW
        _base_usd = ts.DEPOSIT_USD + ts.WITHDRAW_USD
        _dividend = ts.DIVIDEND_INPUT_USD
        _interest = ts.DEPOSIT_INTEREST

        _base_krw.name = "BASE_KRW"
        _base_usd.name = "BASE_USD"

        exchange_rates_ts = self.get_exchange_rates(
            currency_code="USD",
            start_date=ts.index.min(),
            end_date=datetime.datetime.now(),
        )
        history = TimeSeries.concat(
            [_base_krw, _base_usd, _dividend, _interest], axis=1
        )
        history_index = pd.date_range(
            history.index.min(), exchange_rates_ts.index.max()
        )
        exchange_rates_ts = exchange_rates_ts.reindex(history_index).bfill()

        history = TimeSeries(history, index=history_index)
        history["BASE"] = history["BASE_KRW"].fillna(0).cumsum(axis=0) + (
            history["BASE_USD"].fillna(0).cumsum(axis=0) * exchange_rates_ts.USD
        )
        history = history.fillna(0)
        history = history.round(2)
        history.index.name = "trade_date"
        serializer = AccountHistoryOutputSerializer(
            data=history.reset_index().to_dict(orient="records"), many=True
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @staticmethod
    def pivot_history(queryset):
        ts = TimeSeries(queryset.values("trade_date", "trade_type", "settle_amt"))
        ts = (
            ts.groupby(by=["trade_date", "trade_type"])
            .sum()
            .reset_index()
            .pivot(index="trade_date", values="settle_amt", columns="trade_type")
        )
        _amount_history = TimeSeries(
            ts, columns=TradeHistory.get_trade_types(), index=ts.index
        )
        _amount_history = _amount_history.fillna(0).resample("D").sum()
        return _amount_history


class AccountOrderViewSet(
    ExchangeMixin,
    DailyPriceMixin,
    SerializerMapMixin,
    QuerysetMapMixin,
    viewsets.ReadOnlyModelViewSet,
):
    queryset = OrderHistory.objects.all()
    serializer_class = AccountOrderHistorySerializer
    filterset_class = OrderFilterSet
    serializer_class_map = {
        "get_holding_history": AccountHoldingsHistorySerializer,
        "get_evaluation_history": AccountEvaluationHistorySerializer,
        "get_assets_evaluation_history": AssetsEvaluationHistorySerializer,
    }

    def get_holding_history(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        order_history: TimeSeries = self.pivot_orders(queryset=queryset)
        holding_history = self.calc_holdings(order_history=order_history)

        serializable_data = []
        records = holding_history.round(3).reset_index().to_dict(orient="records")
        for row in records:
            serializable_data += [
                {"base_date": row["index"], "symbol": k, "qty": v}
                for k, v in row.items()
                if k != "index"
            ]
        serializer = self.get_serializer(data={"history": serializable_data})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def get_evaluation_history(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        order_history: TimeSeries = self.pivot_orders(queryset=queryset)
        holding_history = self.calc_holdings(order_history=order_history)
        eval_history = self.calc_evaluation(holding_history=holding_history).sum(axis=1)

        exchange_rates_ts = self.get_exchange_rates(
            currency_code="USD",
            start_date=eval_history.index.min(),
            end_date=eval_history.index.max(),
        )
        eval_history = (eval_history * exchange_rates_ts.USD).ffill()
        eval_history.name = "eval_amount"
        eval_history = TimeSeries(eval_history)
        buy_history = self.pivot_orders(queryset=queryset, value="exec_amt")
        buy_history = (
            buy_history.cumsum().sum(axis=1).reindex(eval_history.index).ffill()
        )
        eval_history["buy_amount"] = (buy_history * exchange_rates_ts.USD).ffill()
        eval_history.index.name = "base_date"
        serializer = self.get_serializer(
            data={"history": eval_history.round(3).reset_index().to_dict(orient="records")}
        )
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    def get_assets_evaluation_history(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        order_history: TimeSeries = self.pivot_orders(queryset=queryset)
        holding_history = self.calc_holdings(order_history=order_history)
        eval_history = self.calc_evaluation(holding_history=holding_history)

        serializable_data = []
        records = eval_history.round(3).reset_index().to_dict(orient="records")
        for row in records:
            serializable_data += [
                {"base_date": row["index"], "symbol": k, "evaluation": v}
                for k, v in row.items()
                if k != "index"
            ]
        serializer = self.get_serializer(data={"history": serializable_data})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    @staticmethod
    def pivot_orders(queryset, value="exec_qty"):
        ts = TimeSeries(queryset.values("order_date", "symbol", "trade_type", value))
        order_history = (
            ts.groupby(by=["order_date", "symbol", "trade_type"])
            .sum()
            .reset_index()
            .pivot(index="order_date", columns=["trade_type", "symbol"], values=value)
            .fillna(0)
        )

        _indices = set(order_history[BID].index).union(set(order_history[ASK].index))
        _columns = set(order_history[BID].columns).union(
            set(order_history[ASK].columns)
        )
        _start, _end = min(_indices), max(_indices)
        order_index = pd.date_range(start=_start, end=_end)
        bid_table = TimeSeries(
            order_history[BID], index=order_index, columns=_columns
        ).fillna(0)
        ask_table = TimeSeries(
            order_history[ASK], index=order_index, columns=_columns
        ).fillna(0)
        return bid_table - ask_table

    def calc_evaluation(self, holding_history) -> TimeSeries:
        price_history: TimeSeries = self.get_prices(
            symbols=holding_history.columns, queryset=DailyPrice.objects.all()
        )
        index: pd.DatetimeIndex = pd.date_range(
            start=holding_history.index[0], end=price_history.index[-1]
        )
        holding_history: TimeSeries = holding_history.reindex(index).ffill()
        price_history: TimeSeries = price_history.reindex(index).ffill().bfill()
        eval_history = holding_history * price_history
        return eval_history

    @staticmethod
    def calc_holdings(order_history: TimeSeries):
        return order_history.cumsum(axis=0)
