from django_filters import FilterSet, filters
from pasture.assets.models import AssetUniverse


class DailyPriceFilterSet(FilterSet):
    symbol = filters.CharFilter(label='ticker')
    from_date = filters.DateFilter(field_name='base_date', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='base_date', lookup_expr='lte')


class DailyPriceChangesFilterSet(FilterSet):
    symbol = filters.CharFilter(label='ticker')
    from_date = filters.DateFilter(field_name='base_date', lookup_expr='gte')
    to_date = filters.DateFilter(field_name='base_date', lookup_expr='lte')


class AssetFilterSet(FilterSet):
    universe_id = filters.UUIDFilter(label='universe_id', method='filter_universe_matched')

    def filter_universe_matched(self, queryset, key, value):
        try:
            target_universe = AssetUniverse.objects.get(**{key: value})
            symbols = target_universe.symbols
        except AssetUniverse.DoesNotExist:
            symbols = []

        return queryset.filter(symbol__in=symbols)
