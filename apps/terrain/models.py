from django.db import models
from django.utils import timezone

class OperationTerrain(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    TYPE_OP_CHOICES = [
        ('depense', 'Dépense'),
        ('recette', 'Recette'),
    ]
    
    STATUT_CHOICES = [
        ('en_attente', 'En attente'),
        ('integre', 'Intégré'),
    ]

    type_op = models.CharField(max_length=20, choices=TYPE_OP_CHOICES)
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    nature = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    has_photo = models.BooleanField(default=False)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente')
    date_creation = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.type_op} - {self.nature} - {self.montant}"
    
    class Meta:
        ordering = ['-date_creation']
