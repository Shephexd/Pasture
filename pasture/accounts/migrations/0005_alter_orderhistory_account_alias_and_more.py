# Generated by Django 4.0.5 on 2023-04-18 03:29

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('accounts', '0004_alter_orderhistory_unique_together'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orderhistory',
            name='account_alias',
            field=models.ForeignKey(db_column='account_alias', max_length=100,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='orders',
                                    to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
        migrations.AlterField(
            model_name='tradehistory',
            name='account_alias',
            field=models.ForeignKey(db_column='account_alias', max_length=100,
                                    on_delete=django.db.models.deletion.DO_NOTHING, related_name='trades',
                                    to=settings.AUTH_USER_MODEL, to_field='username'),
        ),
    ]
