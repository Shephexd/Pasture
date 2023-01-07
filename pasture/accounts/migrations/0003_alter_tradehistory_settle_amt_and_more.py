# Generated by Django 4.0.5 on 2022-10-30 10:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_tradehistory"),
    ]

    operations = [
        migrations.AlterField(
            model_name="tradehistory",
            name="settle_amt",
            field=models.DecimalField(
                decimal_places=3, default=0, help_text="정산금액(세후)", max_digits=20
            ),
        ),
        migrations.AlterField(
            model_name="tradehistory",
            name="trade_amt",
            field=models.DecimalField(
                decimal_places=3, default=0, help_text="거래금액(세전)", max_digits=20
            ),
        ),
    ]
