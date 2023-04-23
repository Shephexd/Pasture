import datetime
import logging

from linchfin.common.calc import get_sorted_corr
from linchfin.core.analysis.profiler import AssetProfiler
from linchfin.value.encoders import CorrelationEncoder
from linchfin.value.objects import Table
from pasture.assets.models import Asset, AssetProfile, AssetCorrelation
from pasture.common.helpers import DailyPriceHelper
from pasture.configs.celery import app

CORR_PERIODS = 5


@app.task(bind=True)
def run_asset_profile(self, period="1Y"):
    symbols = list(Asset.objects.filter(asset_type="E").values_list("symbol", flat=True))
    to_date = datetime.datetime.now()
    from_date = AssetProfiler.calc_relative_date(period=period, to_date=to_date)

    filter_kwargs = {
        "base_date__gte": from_date,
        "base_date__lte": to_date
    }

    ts = DailyPriceHelper.get_prices(symbols=symbols, filter_kwargs=filter_kwargs).dropna(axis=1)
    base_date = ts.iloc[-1].name.date()
    if AssetProfile.objects.filter(base_date=base_date, period=period).exists():
        logging.warning(f"Already Exist, period: {period} base_date: {base_date}")
        return

    asset_profiler = AssetProfiler()
    profiled: Table = asset_profiler.run(prices=ts)
    profiled['base_date'] = base_date
    profiled['period'] = period

    profiled_objects = []
    for symbol, row in profiled.iterrows():
        profiled_objects.append(
            AssetProfile(symbol=symbol, **row)
        )

    created_objects = AssetProfile.objects.bulk_create(objs=profiled_objects)
    logging.info(f"Created Asset Profile: {created_objects}")
    deleted_objects = AssetProfile.objects.exclude(base_date=base_date).filter(period=period).delete()
    logging.info(f"Clean Asset Profile: {deleted_objects}")


@app.task(bind=True)
def run_correlation(self, period="1Y"):
    symbols = list(Asset.objects.filter(asset_type="E").values_list("symbol", flat=True))
    to_date = datetime.datetime.now()
    from_date = AssetProfiler.calc_relative_date(period=period, to_date=to_date)

    ts = DailyPriceHelper.get_prices(symbols=symbols, start=from_date, end=to_date).dropna(axis=1)
    base_date = ts.iloc[-1].name.date()

    if AssetCorrelation.objects.filter(base_date=base_date, period=period).exists():
        logging.warning(f"Already Exist, period: {period} base_date: {base_date}")
        return

    correlation_objects = []

    corr = ts.calc_corr(periods=CORR_PERIODS)
    corr.value = corr.value.round(4)
    sorted_corr = get_sorted_corr(corr=corr)

    distances = CorrelationEncoder.encode(corr)
    distances.value = distances.value.round(4)
    sorted_distances = get_sorted_corr(corr=distances)

    for (symbol, corr_row), (_, dist_row) in zip(sorted_corr.iterrows(), sorted_distances.iterrows()):
        correlation_objects.append(
            AssetCorrelation(symbol=symbol, base_date=base_date, period=period,
                             correlation=[{"source": symbol, "target": k, "value": v} for k, v in
                                          zip(corr_row.index, corr_row.to_list())],
                             distance=[{"source": symbol, "target": k, "value": v} for k, v in
                                       zip(dist_row.index, dist_row.to_list())]
                             )
        )

    created_objects = AssetCorrelation.objects.bulk_create(objs=correlation_objects)
    logging.info(f"Created AssetCorrelation: {created_objects}")
    deleted_objects = AssetCorrelation.objects.exclude(base_date=base_date).filter(period=period).delete()
    logging.info(f"Clean AssetCorrelation: {deleted_objects}")
