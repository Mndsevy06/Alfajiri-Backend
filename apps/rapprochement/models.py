import uuid
from django.db import models

class LigneReleve(models.Model):
    class Sens(models.TextChoices):
        DEBIT = 'debit', 'Débit'
        CREDIT = 'credit', 'Crédit'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    libelle = models.CharField(max_length=255)
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    sens = models.CharField(max_length=10, choices=Sens.choices)
    pointe = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - {self.libelle} ({self.montant})"

class LigneCompta(models.Model):
    class Sens(models.TextChoices):
        DEBIT = 'debit', 'Débit'
        CREDIT = 'credit', 'Crédit'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    libelle = models.CharField(max_length=255)
    compte = models.CharField(max_length=50) # To avoid circular dependency with plan_comptable
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    sens = models.CharField(max_length=10, choices=Sens.choices)
    pointe = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.date} - {self.libelle} ({self.montant})"
