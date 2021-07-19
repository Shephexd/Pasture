from uuid import uuid4
from django.db import models
from pasture.common.behaviors import TimeStampable


class Asset(TimeStampable, models.Model):
    asset_type = models.CharField(max_length=1, choices=[('E', 'ETF'), ('S', 'STOCK')])
    symbol = models.CharField(max_length=20, help_text="symbol(ticker)")
    category = models.CharField(max_length=50, help_text="category")
    sub_category = models.CharField(max_length=100, help_text="sub category")
    description = models.TextField(help_text="description", blank=True, null=True)

    class Meta:
        unique_together = ('asset_type', 'symbol', 'category', 'sub_category')


class AssetUniverse(TimeStampable, models.Model):
    universe_id = models.UUIDField(default=uuid4)
    symbol = models.CharField(max_length=20, help_text="symbol(ticker)")


class DailyPrice(TimeStampable, models.Model):
    symbol = models.CharField(max_length=20, help_text="symbol(ticker)")
    open = models.DecimalField(max_digits=15, decimal_places=5, help_text="open price")
    close = models.DecimalField(max_digits=15, decimal_places=5, help_text="close price")
    adj_close = models.DecimalField(null=True, max_digits=15, decimal_places=5, help_text="Ajd close")
    high = models.DecimalField(max_digits=15, decimal_places=5, help_text="high price")
    low = models.DecimalField(max_digits=15, decimal_places=5, help_text="low price")
    volume = models.DecimalField(max_digits=40, decimal_places=5, help_text="volume")
    base_date = models.DateField(help_text="Base date")

    def __str__(self):
        return f"DailyPrice({self.symbol})"

    class Meta:
        unique_together = ('symbol', 'base_date')
