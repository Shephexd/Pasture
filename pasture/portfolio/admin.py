from django.contrib import admin
from .models import Portfolio


@admin.register(Portfolio)
class AssetAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'weights',
    )
    list_filter = ('created_at', 'updated_at')
