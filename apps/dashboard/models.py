import uuid
from django.db import models

class KPI(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    label = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    format = models.CharField(max_length=50, blank=True, null=True)
    evolution = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    icon = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.label
