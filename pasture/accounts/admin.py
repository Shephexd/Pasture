from django.contrib import admin

from pasture.accounts.models import OrderHistory, TradeHistory


# Register your models here.
@admin.register(OrderHistory)
class OrderHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account_alias",
        "order_date",
        "trade_type_name",
        "order_no",
        "symbol",
        "ord_qty",
        "ord_price",
        "exec_qty",
        "exec_price",
        "status_name",
        "currency_code",
        "market_code",
        "channel",
        "cancel_code_name",
        "reject_reason",
    )
    list_filter = (
        "trade_type_name",
        "order_date",
        "market_code",
        "channel",
        "status_name",
        "created_at",
        "updated_at",
    )
    search_fields = ("symbol", "description")


# Register your models here.
@admin.register(TradeHistory)
class TradeHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "account_alias",
        "trade_date",
        "trade_amt",
        "settle_amt",
        "trade_qty",
        "trade_price",
        "trade_type",
        "trade_name",
        "currency_code",
        "exchange_rate",
        "symbol",
    )
    list_filter = ("trade_type", "currency_code", "created_at", "updated_at")
    search_fields = ("symbol", "description")
