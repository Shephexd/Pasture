from django.db import models


class TimeStampable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, help_text="created date")
    updated_at = models.DateTimeField(auto_now=True, help_text="updated date")

    class Meta:
        abstract = True
