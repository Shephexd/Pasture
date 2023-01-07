from django_filters import FilterSet, filters


class DailyPriceFilterSet(FilterSet):
    symbol = filters.CharFilter(label="ticker")
    from_date = filters.DateFilter(field_name="base_date", lookup_expr="gte")
    to_date = filters.DateFilter(field_name="base_date", lookup_expr="lte")


class PortfolioAssetFilterSet(FilterSet):
    symbol = filters.MultipleChoiceFilter(field_name="symbol", lookup_expr="in")
    from_date = filters.DateFilter(field_name="base_date", lookup_expr="gte")
    to_date = filters.DateFilter(field_name="base_date", lookup_expr="lte")
