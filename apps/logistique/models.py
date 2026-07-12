import uuid
from django.db import models

class Camion(models.Model):
    class Statut(models.TextChoices):
        CHARGEMENT = 'chargement', 'En Chargement'
        TRANSIT_ZAMBIE = 'transit_zambie', 'En Transit (Zambie)'
        DOUANE = 'douane', 'Bloqué en Douane'
        TRANSIT_RDC = 'transit_rdc', 'En Transit (RDC)'
        ARRIVE_SABRI = 'arrive_sabri', 'Arrivé à Sabri'
        LIVRE = 'livre', 'Livré'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    immat = models.CharField(max_length=50)
    chauffeur = models.CharField(max_length=255)
    transporteur = models.CharField(max_length=255)
    chargement = models.DecimalField(max_digits=10, decimal_places=2, help_text="Poids en tonnes")
    statut = models.CharField(max_length=30, choices=Statut.choices, default=Statut.CHARGEMENT)
    dateDepart = models.DateTimeField(blank=True, null=True)
    dateArrivee = models.DateTimeField(blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    progression = models.IntegerField(default=0)
    bl = models.CharField(max_length=100, blank=True, null=True)
    factureTransport = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    douaneMontant = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.immat} - {self.transporteur}"
