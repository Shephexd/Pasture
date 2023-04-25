import datetime

import numpy as np
import pytz

from linchfin.models.hrp import (
    HierarchyRiskParityModel,
    AttentionHRPModel,
    SharpAttentionHRPModel,
)
from linchfin.services import PortfolioService
from pasture.assets.models import DailyPrice
from pasture.common.helpers import DailyPriceHelper
from pasture.configs.celery import app
from pasture.portfolio.models import Portfolio

MODEL_CLASS_MAP = {
    "HRP": HierarchyRiskParityModel,
    "AHRP": AttentionHRPModel,
    "SAHRP": SharpAttentionHRPModel,
}

LOOKBACK_DAYS = 180
YEARS = 2
MIN_DAYS = 20


@app.task(bind=True)
def run_portfolio_simulation(
        self, symbols=[], start_date=None, end_date=None, model_name="SAHRP"
):
    today = datetime.datetime.now(pytz.timezone("Asia/Seoul"))
    if start_date is None:
        start_date = today - datetime.timedelta(days=365 * YEARS + LOOKBACK_DAYS)
    if end_date is None:
        end_date = today

    filter_kwargs = {
        "symbol__in": symbols,
        "base_date__gte": start_date,
        "base_date__lte": end_date,
    }
    queryset = DailyPrice.objects.filter(**filter_kwargs)
    port_service = PortfolioService(repo=queryset)
    model = MODEL_CLASS_MAP[model_name](asset_universe=symbols)
    THRESHOLD = 1 / np.log(len(symbols)) / np.sqrt(len(symbols))

    ts = DailyPriceHelper.get_prices(symbols=symbols).dropna(axis=1)
    rebalancing_result = port_service.do_rebalancing(
        model=model,
        prices=ts,
        threshold=THRESHOLD,
        min_days=MIN_DAYS,
        lookback_days=LOOKBACK_DAYS,
    )
    last_portfolio = rebalancing_result.history.iloc[-1].astype(float)
    port_date = last_portfolio.name.date()

    print("port_date:", port_date)

    port_changes = rebalancing_result.get_port_changes(prices=ts)
    port_returns = np.exp(port_changes.sum(axis=1).apply(np.log).sum())
    volatility = port_changes.sum(axis=1).std()

    if not Portfolio.objects.filter(base_date=port_date).exists():
        _weights = []
        for symbol, w in last_portfolio.to_dict().items():
            _weights.append({"symbol": symbol, "weight": w})
        _weights.sort(key=lambda x: -x["weight"])
        port = Portfolio(
            weights=_weights,
            base_date=port_date,
            description=f"Simulation Period:{min(ts.index)}~{max(ts.index)}" + \
                        f"\nSymbols: {symbols}" + \
                        f"\nport simulation acc returns: {round(port_returns, 3)}" + \
                        f"\nport simulation volatility: {round(volatility, 3)}",
        )
        port.save()
