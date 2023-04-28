import datetime

import pandas as pd

from linchfin.value.objects import TimeSeries
from pasture.accounts.models import Settlement, TradeHistory
from pasture.common.helpers import ExchangeHelper
from pasture.configs.celery import app

number_fields = ["base_io_krw", "base_io_usd", "dividend_usd", "deposit_interest_krw"]
ffill_fields = ["base_amount_krw", "exchange_rate"]
history_columns = ["base_date"] + number_fields + ffill_fields


@app.task(bind=True)
def settle_trade(self):
    """
    Order Trade Exchange
    0     0     0 = pass
    1     0     0 = impossible
    0     1     0 = impossible
    1     1     0 = impossible

    0     0     1 = update_price
    0     1     1 = settle_trade()
    1     0     1 = settle(order()
    1     1     1 = settle_trade() -> settle_order()
    """
    for _filter_kwargs in TradeHistory.objects.values("account_alias").distinct():
        start_date = datetime.datetime.now().date()
        history = TimeSeries(columns=history_columns)
        last_settlement_queryset = Settlement.objects.filter(**_filter_kwargs)

        is_settlement_exists = last_settlement_queryset.exists()
        if is_settlement_exists:

            prev_history = TimeSeries(last_settlement_queryset.values(*history_columns)).sort_values("base_date")
            _filter_kwargs["trade_date__gt"] = prev_history.iloc[-1].base_date
            history = pd.concat([history, prev_history.df])
            start_date = min(prev_history.base_date.max() + datetime.timedelta(days=1), start_date)

        history.set_index("base_date", inplace=True)
        history.index = pd.to_datetime(history.index)

        trade_queryset = TradeHistory.objects.filter(**_filter_kwargs)
        is_trade_exists = trade_queryset.exists()

        if is_trade_exists:
            start_date = min(start_date, trade_queryset.first().trade_date)

        # trade, order, exchange
        exchange_rates_ts = ExchangeHelper.get_exchange_rates(
            currency_code="USD",
            start_date=start_date,
            end_date=datetime.datetime.now(),
        )

        if exchange_rates_ts.empty:
            print("exchange_rate is not ready")
            return -1

        if not is_trade_exists:
            print("No trade for settlement")
            return

        # set history index and exchange_rate
        ts = TradeHistory.objects.pivot_history(queryset=trade_queryset)
        end_date = history.index.append(exchange_rates_ts.index).append(ts.index).max()
        history_index = pd.date_range(start=start_date, end=end_date)
        history = history.reindex(history_index)
        history.loc[exchange_rates_ts.index, "exchange_rate"] = exchange_rates_ts.USD
        history.loc[:, "exchange_rate"] = history.loc[:, "exchange_rate"].ffill().bfill()

        if not is_settlement_exists:
            history.loc[history.index[0], "base_amount_krw"] = 0

        settlement_indexer = history.index[history.index >= ts.index[-1]]
        settlement_indexer = settlement_indexer.append(exchange_rates_ts.index)
        settlement_indexer = pd.date_range(start=settlement_indexer.min(), end=end_date)

        history.loc[settlement_indexer, number_fields] = 0
        history.loc[:, ffill_fields] = history.loc[:, ffill_fields].ffill()
        history.loc[ts.index, "base_io_krw"] = ts.DEPOSIT_KRW + ts.WITHDRAW_KRW
        history.loc[ts.index, "base_io_usd"] = ts.DEPOSIT_USD + ts.WITHDRAW_USD
        history.loc[ts.index, "dividend_usd"] = ts.DIVIDEND_INPUT_USD
        history.loc[ts.index, "deposit_interest_krw"] = ts.DEPOSIT_INTEREST

        history.loc[settlement_indexer, "base_amount_krw"] = \
            history.loc[settlement_indexer, "base_amount_krw"].astype(float) + \
            history.loc[settlement_indexer, "base_io_krw"].fillna(0).cumsum() + \
            (history.loc[settlement_indexer, "base_io_usd"].fillna(0) *
             history.loc[settlement_indexer, "exchange_rate"]).cumsum()

        target_history = history.loc[settlement_indexer, :]
        target_history = target_history.round(3)
        target_history.index.name = "base_date"
        target_history.reset_index(inplace=True)

        settlement_objs = [Settlement(**row) for i, row in
                           target_history.assign(account_alias_id=_filter_kwargs["account_alias"]).iterrows()]
        Settlement.objects.bulk_create(settlement_objs)
        print("Finish Settlement\n", target_history)
