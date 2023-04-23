import datetime

import pandas as pd

from linchfin.value.objects import TimeSeries, TimeSeriesRow
from pasture.assets.models import DailyPrice
from pasture.market.models import ExchangeRate


class DailyPriceHelper:
    price_queryset = DailyPrice.objects.all()

    @classmethod
    def get_prices(cls, symbols, start=None, end=None, **filter_kwargs) -> TimeSeries:
        if start:
            filter_kwargs["base_date__gte"] = start
        if end:
            filter_kwargs["base_date__lte"] = end
        queryset = cls.price_queryset.filter(symbol__in=symbols, **filter_kwargs)
        return cls.get_pivot(queryset=queryset)

    @classmethod
    def get_last_prices(cls, symbols) -> TimeSeriesRow:
        return cls.get_prices(symbols=symbols).iloc[-1]

    @classmethod
    def set_timeseries_index(cls, ts: TimeSeries):
        ts.index = pd.to_datetime(ts.index)
        return ts.resample("D").first().ffill().bfill()

    @classmethod
    def get_pivot(
            cls, queryset, value_keys="close", index_key="base_date", column_keys="symbol"
    ):
        ts = TimeSeries(pd.DataFrame(queryset.values()))
        if not ts.empty:
            ts = ts.pivot(
                index=index_key, values=value_keys, columns=column_keys
            ).astype(float)
            cls.set_timeseries_index(ts=ts)
        return ts


class ExchangeHelper:
    @staticmethod
    def get_exchange_rates(
            currency_code: str,
            start_date: datetime.datetime,
            end_date: datetime.datetime,
    ):
        _filter_kwargs = {"base_date__gte": start_date, "base_date__lte": end_date}
        exchange_rates = ExchangeRate.objects.filter(
            currency_code=currency_code, **_filter_kwargs
        )
        exchange_rates_ts = TimeSeries(
            exchange_rates.values("base_date", "currency_code", "trading_exchange_rate")
        ).pivot(
            columns="currency_code", values="trading_exchange_rate", index="base_date"
        )
        _index = pd.date_range(start=start_date, end=end_date)
        exchange_rates_ts.reindex(_index)
        return exchange_rates_ts.ffill().bfill()
