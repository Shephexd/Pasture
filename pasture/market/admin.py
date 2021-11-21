from django.contrib import admin
from .models import MacroMaster, MacroIndex


@admin.register(MacroMaster)
class MacroMasterAdmin(admin.ModelAdmin):
    list_display = (
        'symbol',
        'name',
        'category',
        'sub_category',
        'description',
    )
    list_filter = ('category', 'sub_category', 'created_at', 'updated_at')
    search_fields = ('symbol', 'name')


@admin.register(MacroIndex)
class MacroIndexAdmin(admin.ModelAdmin):
    list_display = (
        'symbol', 'base_date', 'value'
    )
    list_filter = ('created_at', 'updated_at')
