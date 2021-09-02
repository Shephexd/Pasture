from uuid import uuid4
from django.db import models
from django.contrib.postgres.fields import JSONField
from pasture.common.behaviors import TimeStampable


class Portfolio(TimeStampable, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    weights = JSONField(help_text="weights")
