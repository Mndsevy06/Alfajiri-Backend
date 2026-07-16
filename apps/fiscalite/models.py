from django.db import models
from apps.plan_comptable.models import Tiers

class DeclarationFiscale(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class TypeDeclaration(models.TextChoices):
        TVA = 'TVA', 'TVA'
        IPR = 'IPR', 'IPR (Impôt Professionnel sur les Rémunérations)'
        IS_ACOMPTE = 'Acompte IS', 'Acompte Provisionnel IS'
        IS_SOLDE = 'Solde IS', 'Solde IS (Impôt sur les Sociétés)'
        PATENTE = 'Patente', 'Patente'
        AUTRE = 'Autre', 'Autre'

    class StatutDeclaration(models.TextChoices):
        BROUILLON = 'Brouillon', 'Brouillon'
        EN_ATTENTE = 'En attente', 'En attente'
        DECLARE_PAYE = 'Déclaré et Payé', 'Déclaré et Payé'
        EN_RETARD = 'En retard', 'En retard'

    id = models.CharField(max_length=20, primary_key=True)
    type_declaration = models.CharField(max_length=20, choices=TypeDeclaration.choices, default=TypeDeclaration.TVA)
    periode = models.CharField(max_length=50) # e.g. "Juillet 2026"
    montant = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    echeance = models.DateField()
    statut = models.CharField(max_length=20, choices=StatutDeclaration.choices, default=StatutDeclaration.BROUILLON)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.type_declaration} ({self.periode})"

class RetenueSource(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class TypeRetenue(models.TextChoices):
        IBP = 'IBP 14%', 'IBP 14%'
        LOYER = 'Loyer 22%', 'Loyer 22%'
        AUTRE = 'Autre', 'Autre'

    class StatutRetenue(models.TextChoices):
        BROUILLON = 'Brouillon', 'Brouillon'
        PRELEVE = 'Prélevé', 'Prélevé'
        REVERSE = 'Reversé à l\'État', 'Reversé à l\'État'

    id = models.CharField(max_length=20, primary_key=True)
    tiers = models.ForeignKey(Tiers, on_delete=models.CASCADE, related_name='retenues_fiscales')
    type_retenue = models.CharField(max_length=20, choices=TypeRetenue.choices, default=TypeRetenue.IBP)
    date = models.DateField()
    base_calcul = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    montant = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=StatutRetenue.choices, default=StatutRetenue.PRELEVE)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.tiers.nom} ({self.type_retenue})"
