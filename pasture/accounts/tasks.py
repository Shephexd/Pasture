import datetime

import pandas as pd

from linchfin.value.objects import TimeSeries
from pasture.accounts.models import Settlement, TradeHistory
from pasture.common.helpers import ExchangeHelper
from pasture.configs.celery import app

number_fields = ["base_io_krw", "base_io_usd", "dividend_usd", "deposit_interest_krw"]
ffill_fields = ["base_amount_krw", "exchange_rate"]
history_columns = ["base_date"] + number_fields + ffill_fields


def clean_untracked_settlement(account_alias):
    last_corrected_settlement_obj = None
    for _settlement_obj in Settlement.objects.filter(account_alias=account_alias).order_by("-base_date"):
        if not TradeHistory.objects.filter(trade_date__lte=_settlement_obj.base_date,
                                           created_at__gte=_settlement_obj.created_at,
                                           account_alias=account_alias).exists():
            break

        last_corrected_settlement_obj = _settlement_obj

    if last_corrected_settlement_obj:
        deleted, _ = Settlement.objects.filter(base_date__gte=last_corrected_settlement_obj.base_date).delete()
        print("deleted Settlement: ", deleted)


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
        clean_untracked_settlement(**_filter_kwargs)

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
            start_date=start_date - datetime.timedelta(days=5),
            end_date=datetime.datetime.now(),
        )

        if exchange_rates_ts.empty:
            print("exchange_rate is not ready")
            return -1

        if not is_trade_exists:
            print("No trade for settlement")
            return

        exchange_rates_ts = exchange_rates_ts.resample('D').ffill()

        # set history index and exchange_rate
        ts = TradeHistory.objects.pivot_history(queryset=trade_queryset)
        end_date = history.index.append(exchange_rates_ts.index).append(ts.index).max()
        history_index = pd.date_range(start=start_date - datetime.timedelta(days=1), end=end_date)
        history = history.reindex(history_index)

        history.loc[:, ffill_fields] = history.loc[:, ffill_fields].ffill()

        exchange_history_index = history_index.intersection(exchange_rates_ts.index)
        history.loc[exchange_history_index, "exchange_rate"] = exchange_rates_ts.loc[exchange_history_index, "USD"]
        history.loc[:, "exchange_rate"] = history.loc[:, "exchange_rate"].ffill()

        history = history.iloc[1:]
        if not is_settlement_exists:
            history.loc[history.index[0], "base_amount_krw"] = 0

        history.loc[:, number_fields] = 0
        history.loc[ts.index, "base_io_krw"] = ts.DEPOSIT_KRW + ts.WITHDRAW_KRW
        history.loc[ts.index, "base_io_usd"] = ts.DEPOSIT_USD + ts.WITHDRAW_USD
        history.loc[ts.index, "dividend_usd"] = ts.DIVIDEND_INPUT_USD
        history.loc[ts.index, "deposit_interest_krw"] = ts.DEPOSIT_INTEREST

        history.loc[:, "base_amount_krw"] = \
            history.loc[:, "base_amount_krw"].astype(float) + \
            history.loc[:, "base_io_krw"].astype(float).fillna(0).cumsum() + \
            (history.loc[:, "base_io_usd"].astype(float).fillna(0) *
             history.loc[:, "exchange_rate"].astype(float)).cumsum()

        history = history.round(3)
        history.index.name = "base_date"
        history.reset_index(inplace=True)

        settlement_objs = [Settlement(**row) for i, row in
                           history.assign(account_alias_id=_filter_kwargs["account_alias"]).iterrows()]
        Settlement.objects.bulk_create(settlement_objs)
        print("Finish Settlement\n", history)
