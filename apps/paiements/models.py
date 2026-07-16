import uuid
from django.db import models
from apps.plan_comptable.models import Tiers

class Paiement(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class TypeOperation(models.TextChoices):
        ENCAISSEMENT = 'encaissement', 'Encaissement'
        DECAISSEMENT = 'decaissement', 'Décaissement'

    class ModePaiement(models.TextChoices):
        VIREMENT = 'virement', 'Virement Bancaire'
        ESPECES = 'especes', 'Espèces (Caisse)'
        MOBILE = 'mobile', 'Mobile Money'
        CHEQUE = 'cheque', 'Chèque'

    class Statut(models.TextChoices):
        EN_ATTENTE = 'en_attente', 'En attente'
        RAPPROCHE = 'rapproche', 'Rapproché'
        LETTRE = 'lettre', 'Lettré'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(max_length=20, choices=TypeOperation.choices)
    date = models.DateField()
    tiers = models.ForeignKey(Tiers, on_delete=models.PROTECT, related_name='paiements')
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    mode = models.CharField(max_length=20, choices=ModePaiement.choices)
    reference = models.CharField(max_length=100, help_text="N° Facture, BL, ou Référence de transaction")
    justificatif = models.FileField(upload_to='paiements/justificatifs/', blank=True, null=True)
    memo = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_ATTENTE)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date', '-date_creation']

    def __str__(self):
        return f"{self.get_type_display()} - {self.reference} ({self.montant})"
