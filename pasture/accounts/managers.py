from typing import List, Dict, TYPE_CHECKING

import pandas as pd
from django.db import models

from linchfin.value.objects import TimeSeries, TimeSeriesRow
from pasture.common.helpers import DailyPriceHelper

if TYPE_CHECKING:
    pass

ASK = "01"
BID = "02"
TRADE_TAX = 0.15 / 100


class TimeSeriesManager(models.Manager):
    pass


class PivotOrderQueryset(models.QuerySet):
    pass


class HoldingManager(TimeSeriesManager):
    def get_holding_qty_history(self, account_alias) -> TimeSeries:
        history = TimeSeries(self.filter(account_alias=account_alias).values("base_date", "symbol", "holding_qty"))
        history.pivot(index="base_date", columns="symbol", values="holding_qty").fillna(0)
        return history

    def to_timeseries(self, account_alias):
        ts = TimeSeries(self.filter(account_alias=account_alias).values("base_date", "symbol", "holding_qty"))
        return ts.pivot(index="base_date", columns="symbol", values="holding_qty").resample("D").first().fillna(0)

    def calc_daily_eval(self, account_alias) -> TimeSeries:
        history = TimeSeries(self.filter(account_alias=account_alias).values("base_date", "symbol", "eval_amt")).pivot(
            index="base_date", columns="symbol", values="eval_amt").resample("D").first().fillna(0).sum(axis=1)
        return history


class TradeHistoryManager(TimeSeriesManager):
    def get_pivoted_queryset(self, value: str = "exec_qty"):
        return PivotOrderQueryset(self.model, using=self._db)

    def get_pivot(self, value: str = "exec_qty"):
        ts = TimeSeries(self.values("order_date", "symbol", "trade_type", value))
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

    def pivot_history(self, queryset):
        ts = TimeSeries(queryset.values("trade_date", "trade_type", "settle_amt"))
        ts = (
            ts.groupby(by=["trade_date", "trade_type"])
                .sum()
                .reset_index()
                .pivot(index="trade_date", values="settle_amt", columns="trade_type")
        )
        _amount_history = TimeSeries(
            ts, columns=self.get_trade_types(), index=ts.index
        )
        _amount_history = _amount_history.fillna(0).resample("D").sum()
        return _amount_history

    def get_groupby(self):
        group_by = self.values("trade_type").annotate(
            trade_amt=models.Sum("trade_amt"),
            settle_amt=models.Sum("settle_amt"),
            tax_amt=models.Sum("tax"),
            vat_amt=models.Sum("vat"),
        )
        return group_by

    @classmethod
    def get_trade_types(cls):
        return [
            "DEPOSIT_INTEREST",
            "DEPOSIT_KRW",
            "WITHDRAW_KRW",
            "DEPOSIT_USD",
            "WITHDRAW_USD",
            "DIVIDEND_INPUT_USD",
            "EXCHANGE_USD",
        ]


class OrderHistoryManager(DailyPriceHelper, TimeSeriesManager):
    def get_order_qty_history(self, symbols: List[str] = None) -> TimeSeries:
        queryset = self.all()
        if symbols:
            queryset = self.filter(symbol__in=symbols)
        ts = TimeSeries(queryset.values("order_date", "symbol", "trade_type", "exec_qty"))
        if ts.empty:
            return ts

        order_qty_history = (
            ts.groupby(by=["order_date", "symbol", "trade_type"])
                .sum()
                .reset_index()
                .pivot(index="order_date", columns=["trade_type", "symbol"], values="exec_qty")
                .fillna(0)
        )

        _indices = pd.date_range(start=ts.order_date.min(), end=ts.order_date.max())
        _columns = pd.MultiIndex.from_product([(BID, ASK), ts.symbol.unique()], names=["trade_type", "symbol"])
        order_qty_history = order_qty_history.reindex(index=_indices, columns=_columns)
        return order_qty_history.fillna(0)

    def calc_daily_changes(self, symbols):
        _history = self.get_order_qty_history(symbols=symbols)
        bid_table = TimeSeries(_history[BID])
        ask_table = TimeSeries(_history[ASK])
        return bid_table - ask_table

    def calc_evaluation(self, holding_history) -> TimeSeries:
        price_history: TimeSeries = self.get_prices(symbols=holding_history.columns)
        index: pd.DatetimeIndex = pd.date_range(
            start=holding_history.index[0], end=price_history.index[-1]
        )
        price_history = price_history.reindex(index=index, columns=holding_history.columns).ffill().bfill()
        holding_history: TimeSeries = holding_history.reindex(index).ffill()
        eval_history = holding_history * price_history
        return eval_history

    def calc_holdings(self, symbols: List[str] = None):
        order_history = self.calc_daily_changes(symbols=symbols)
        return order_history.cumsum(axis=0)

    def to_holding_records(self, symbols: List[str] = None) -> List[Dict]:
        if symbols is None:
            symbols = list(self.values_list("symbol", flat=True).distinct())
        qty_history = self.get_order_qty_history(symbols=symbols)
        price_history: TimeSeries = self.get_prices(symbols=symbols)

        price_history = price_history.reindex(index=qty_history.index, columns=symbols).ffill().bfill()
        holdings = TimeSeriesRow(0, index=symbols)
        records = []

        for (i, _history_row), (j, _price_row) in zip(qty_history.iterrows(), price_history.iterrows()):
            for symbol, close_price in _price_row.iteritems():
                holdings[symbol] += (_history_row[BID, symbol] - _history_row[ASK, symbol])
                _row = {
                    "base_date": i, "symbol": symbol, "market_price": close_price,
                    "eval_amt": holdings[symbol] * close_price,
                    "holding_qty": holdings[symbol], "buy_qty": _history_row[BID, symbol],
                    "sell_qty": _history_row[ASK, symbol]
                }
                if _row["holding_qty"] or _row["buy_qty"] or _row["sell_qty"]:
                    records.append(_row)
        return records
