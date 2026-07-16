from django.db import models
import uuid

class Contrat(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe = models.ForeignKey('plan_comptable.Tiers', on_delete=models.CASCADE, limit_choices_to={'type': 'personnel'}, related_name='contrats')
    type_contrat = models.CharField(max_length=50, choices=[('CDI', 'CDI'), ('CDD', 'CDD'), ('STAGE', 'Stage'), ('CONSULTANT', 'Consultant')])
    salaire_base = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)
    fonction = models.CharField(max_length=255)
    est_actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.employe.nom} - {self.type_contrat}"

class BulletinPaie(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class StatutBulletin(models.TextChoices):
        BROUILLON = 'brouillon', 'Brouillon'
        VALIDE = 'valide', 'Validé'
        PAYE = 'paye', 'Payé'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employe = models.ForeignKey('plan_comptable.Tiers', on_delete=models.CASCADE, limit_choices_to={'type': 'personnel'})
    periode = models.CharField(max_length=7) # Format YYYY-MM
    jours_travailles = models.IntegerField(default=26)
    mode_paiement = models.CharField(max_length=50, default='virement')
    
    # Gains
    salaire_base = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    heures_sup = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    primes = models.JSONField(default=list, blank=True) # Stocke la liste détaillée des primes
    
    # Retenues employe
    cnss_employe = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    ipr = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    avances = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Charges patronales
    cnss_patronal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    inpp_patronal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    onem_patronal = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    
    # Résultat
    net_a_payer = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    statut = models.CharField(max_length=20, choices=StatutBulletin.choices, default=StatutBulletin.BROUILLON)
    
    cree_le = models.DateTimeField(auto_now_add=True)
    mis_a_jour_le = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Bulletin {self.periode} - {self.employe.nom}"
