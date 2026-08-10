from django.db import models
from django.utils import timezone

class OperationTerrain(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    TYPE_OP_CHOICES = [
        ('depense', 'Dépense'),
        ('entree', 'Entrée'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('integre', 'Intégré'),
    ]

    type_op = models.CharField(max_length=20, choices=TYPE_OP_CHOICES)
    numero_facture = models.CharField(max_length=100)  # Obligatoire - pas de default pour forcer la cohérence API/modèle
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    nature = models.CharField(max_length=50)
    notes = models.CharField(max_length=50, blank=True, null=True)
    has_photo = models.BooleanField(default=False)
    fichier = models.FileField(upload_to='justificatifs_terrain/%Y/%m/', blank=True, null=True)
    saisie_par = models.ForeignKey('authentification.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='operations_terrain')
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type_op} - {self.nature} - {self.montant}"
    
    class Meta:
        ordering = ['-date_creation']
