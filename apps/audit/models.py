import uuid
from django.db import models
from django.conf import settings

class AuditEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=50, blank=True, null=True)
    ip = models.GenericIPAddressField(blank=True, null=True)
    terminal = models.CharField(max_length=255, blank=True, null=True)
    action = models.CharField(max_length=50) # e.g. CREATION, MODIFICATION, CONNEXION
    module = models.CharField(max_length=100)
    objet = models.CharField(max_length=255)
    avant = models.TextField(blank=True, null=True)
    apres = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.timestamp} - {self.action} - {self.objet}"
