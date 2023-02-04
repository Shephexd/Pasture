from linchfin.core.analysis.profiler import AssetProfiler
from linchfin.value.objects import Table
from pasture.common.viewset import DailyPriceMixin
from pasture.configs.celery import app
from pasture.assets.models import DailyPrice, Asset, AssetProfile
import datetime
import logging


@app.task(bind=True)
def run_asset_profile(self, period="1Y"):
    symbols = list(Asset.objects.filter(asset_type="E").values_list("symbol", flat=True))
    to_date = datetime.datetime.now()
    from_date = AssetProfiler.calc_relative_date(period=period, to_date=to_date)

    filter_kwargs = {
        "symbol__in": symbols,
        "base_date__gte": from_date,
        "base_date__lte": to_date
    }

    queryset = DailyPrice.objects.filter(**filter_kwargs)
    ts = DailyPriceMixin().get_prices(queryset=queryset, symbols=symbols).dropna(axis=1)
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
