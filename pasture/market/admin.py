from django.contrib import admin

from .models import MacroMaster, MacroIndex, ExchangeRate


@admin.register(MacroMaster)
class MacroMasterAdmin(admin.ModelAdmin):
    list_display = (
        "symbol",
        "name",
        "category",
        "sub_category",
        "description",
    )
    list_filter = ("category", "sub_category", "created_at", "updated_at")
    search_fields = ("symbol", "name")


@admin.register(MacroIndex)
class MacroIndexAdmin(admin.ModelAdmin):
    list_display = ("symbol", "base_date", "value")
    list_filter = ("created_at", "updated_at")


@admin.register(ExchangeRate)
class ExchangeRateAdmin(admin.ModelAdmin):
    list_display = (
        "currency_code",
        "base_date",
        "currency_name",
        "kor_book_exchange_rate",
        "kor_trading_exchange_rate",
        "sending_exchange_rate",
        "receiving_exchange_rate",
        "trading_exchange_rate",
        "book_exchange_rate",
    )
    list_filter = ("currency_code", "base_date")
    search_fields = ("currency_code",)
