from django.contrib import admin
from .models import DailyPrice, Asset


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'asset_type',
        'symbol',
        'category',
        'sub_category',
        'description',
        'created_at',
        'updated_at'
    )
    list_filter = ('asset_type', 'category', 'sub_category', 'created_at', 'updated_at')
    search_fields = ('symbol', 'description')


@admin.register(DailyPrice)
class DailyPriceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'symbol',
        'open',
        'close',
        'high',
        'low',
        'adj_close',
        'volume',
        'created_at',
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at')


