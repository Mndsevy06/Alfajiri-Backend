import uuid
from django.db import models

class Facture(models.Model):
    class Statut(models.TextChoices):
        IMPAYEE = 'impayee', 'Impayée'
        PAYEE = 'payee', 'Payée'
        PARTIELLE = 'partielle', 'Partielle'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=100)
    date = models.DateField()
    client = models.ForeignKey('plan_comptable.Tiers', on_delete=models.CASCADE, related_name='factures')
    montantHT = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    tva = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montantTTC = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.IMPAYEE)
    echeance = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.numero} - {self.client.nom}"
