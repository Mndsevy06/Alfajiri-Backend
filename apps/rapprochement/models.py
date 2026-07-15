import uuid
from django.db import models
from django.conf import settings

class Rapprochement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date_rapprochement = models.DateTimeField(auto_now_add=True)
    valide_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"Rapprochement {self.id} du {self.date_rapprochement.strftime('%Y-%m-%d')}"

class LigneReleve(models.Model):
    class Sens(models.TextChoices):
        DEBIT = 'debit', 'Débit'
        CREDIT = 'credit', 'Crédit'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    libelle = models.CharField(max_length=255)
    reference = models.CharField(max_length=100, blank=True, null=True)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    sens = models.CharField(max_length=10, choices=Sens.choices)
    pointe = models.BooleanField(default=False)
    rapprochement = models.ForeignKey(Rapprochement, on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_releve')

    def __str__(self):
        return f"{self.date} - {self.libelle} ({self.montant})"
