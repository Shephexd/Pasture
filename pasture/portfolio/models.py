from uuid import uuid4
from django.db import models
from pasture.common.behaviors import TimeStampable


class Portfolio(TimeStampable, models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4)
    weights = models.JSONField(help_text="weights")
    base_date = models.DateField(help_text="base_date")
    description = models.TextField(default="", help_text="portfolio description")
