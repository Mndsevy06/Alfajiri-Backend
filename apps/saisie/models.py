import uuid
from django.db import models
from django.conf import settings

class Ecriture(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class Statut(models.TextChoices):
        BROUILLARD = 'brouillard', 'Brouillard'
        VALIDE = 'valide', 'Validé'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero = models.CharField(max_length=50, unique=True) # e.g. ACH-2025-00001
    journal = models.ForeignKey('plan_comptable.Journal', on_delete=models.CASCADE, related_name='ecritures')
    date = models.DateField()
    libelle = models.CharField(max_length=255)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.BROUILLARD)
    saisiePar = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='ecritures_saisies')
    validePar = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='ecritures_validees')
    piece = models.CharField(max_length=255, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    validated_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.numero} - {self.libelle}"

class LigneEcriture(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ecriture = models.ForeignKey(Ecriture, on_delete=models.CASCADE, related_name='lignes')
    # Numéro unique de ligne : ex. PC-ACH-2026-00001/L01
    numero_ligne = models.CharField(max_length=100, unique=True, blank=True, null=True)
    date = models.DateField()
    compte = models.ForeignKey('plan_comptable.CompteComptable', on_delete=models.CASCADE, related_name='lignes')
    libelleCompte = models.CharField(max_length=255, blank=True, null=True)
    libelle = models.CharField(max_length=255)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    centre_cout = models.CharField(max_length=255, blank=True, null=True)
    tiers_auxiliaire = models.ForeignKey('plan_comptable.Tiers', on_delete=models.SET_NULL, blank=True, null=True, related_name='lignes_ecritures')
    fichier = models.FileField(upload_to='justificatifs_comptables/%Y/%m/', blank=True, null=True)
    rapprochement = models.ForeignKey('rapprochement.Rapprochement', on_delete=models.SET_NULL, null=True, blank=True, related_name='lignes_ecriture')

    def __str__(self):
        return f"{self.numero_ligne or self.ecriture.numero} - {self.compte.numero} - {self.libelle}"
