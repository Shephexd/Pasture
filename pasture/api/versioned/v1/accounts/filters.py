from django_filters import FilterSet, filters


class TradeFilterSet(FilterSet):
    trade_type = filters.ChoiceFilter(
        label="ticker",
        choices=(
            ["DEPOSIT_INTEREST", "예탹금 이용료"],
            ["DEPOSIT_KRW", "원화 입금"],
            ["DEPOSIT_USD", "달러 입금"],
            ["WITHDRAW_KRW", "원화 인출"],
            ["WITHDRAW_USD", "외화 인출"],
            ["DIVIDEND_INPUT_USD", "외화 배당금 입금"],
        ),
    )
    account_alias = filters.CharFilter()


class OrderFilterSet(FilterSet):
    symbol = filters.CharFilter(label="ticker")
    order_type = filters.ChoiceFilter(
        field_name="trade_type_name",
        label="주문구분",
        method="filter_order_type",
        choices=(
            ["BID", "매수"],
            ["ASK", "매도"],
        ),
    )

    ORDER_TYPES = {"BID": ["매수", "자동매수"], "ASK": ["매도", "자동매도"]}

    def filter_order_type(self, queryset, name, value):
        if value and value in self.ORDER_TYPES.keys():
            return queryset.filter(**{f"{name}__in": self.ORDER_TYPES[value]})
        return queryset
