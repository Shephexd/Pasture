from django.db import models

from pasture.common.behaviors import TimeStampable


class MacroMaster(TimeStampable, models.Model):
    symbol = models.CharField(max_length=20, help_text="symbol")
    name = models.CharField(max_length=200, help_text="name")
    period = models.CharField(help_text="period", max_length=2, null=True)
    category = models.CharField(
        max_length=50, help_text="category", null=True, blank=True
    )
    sub_category = models.CharField(
        max_length=100, help_text="sub category", null=True, blank=True
    )
    description = models.TextField(help_text="description", blank=True, null=True)

    class Meta:
        unique_together = ("symbol", "period", "category", "sub_category")


class MacroIndex(TimeStampable, models.Model):
    symbol = models.CharField(max_length=20, help_text="symbol")
    period = models.CharField(help_text="period", max_length=2, null=True)
    base_date = models.DateField(help_text="base date")
    value = models.DecimalField(max_digits=20, decimal_places=4)

    class Meta:
        unique_together = ("symbol", "period", "base_date")
