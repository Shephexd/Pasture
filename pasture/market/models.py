from django.db import models
import datetime
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


class ExchangeRate(TimeStampable, models.Model):
    currency_code = models.CharField(max_length=10)
    currency_name = models.CharField(max_length=50)

    base_date = models.DateField(default=datetime.datetime.now())
    sending_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, null=True
    )
    receiving_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, null=True
    )
    trading_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="매매기준율"
    )
    book_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="장부가격"
    )
    kor_book_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="서울외국환중개장부가격", null=True
    )
    kor_trading_exchange_rate = models.DecimalField(
        max_digits=15, decimal_places=2, help_text="서울외국환매매기준율", null=True
    )

    class Meta:
        unique_together = ("currency_code", "base_date")


# https://www.koreaexim.go.kr/site/program/financial/exchangeJSON?authkey=mDp4HhNGn6gEq54LiHedwEhnSpMT1rgU&searchdate=20180102&data=AP01
