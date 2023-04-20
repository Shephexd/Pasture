from typing import TYPE_CHECKING

import pandas as pd
from django.db import models

from linchfin.value.objects import TimeSeries

if TYPE_CHECKING:
    pass

ASK = "01"
BID = "02"
TRADE_TAX = 0.15 / 100


class TimeSeriesManager(models.Manager):
    pass


class PivotOrderQueryset(models.QuerySet):
    pass


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
