import pandas as pd
from rest_framework import viewsets
from linchfin.value.objects import TimeSeries, TimeSeriesRow


class SerializerMapMixin(viewsets.GenericViewSet):
    serializer_class_map = {}

    def get_serializer_class(self):
        return self.serializer_class_map.get(self.action, self.serializer_class)


class QuerysetMapMixin(viewsets.GenericViewSet):
    queryset_map = {}

    def get_queryset(self):
        return self.queryset_map.get(self.action, self.queryset)


class DailyPriceMixin(viewsets.GenericViewSet):
    def get_prices(self, queryset, symbols) -> TimeSeries:
        queryset = queryset.filter(symbol__in=symbols)
        return self.get_pivot(queryset=queryset)

    def get_last_prices(self, queryset, symbols) -> TimeSeriesRow:
        return self.get_prices(queryset=queryset, symbols=symbols).iloc[-1]

    def set_timeseries_index(self, ts: TimeSeries):
        ts.index = pd.to_datetime(ts.index)
        return ts

    def get_pivot(
        self, queryset, value_keys="close", index_key="base_date", column_keys="symbol"
    ):
        ts = TimeSeries(pd.DataFrame(queryset.values()))
        if not ts.empty:
            ts = ts.pivot(
                index=index_key, values=value_keys, columns=column_keys
            ).astype(float)
            self.set_timeseries_index(ts=ts)
        return ts
