import uuid
from django.db import models
from django.core.validators import MinValueValidator

class CircuitLogistique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150, unique=True, help_text="Nom du circuit (ex: Import Zambie -> RDC)")
    description = models.TextField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nom

class EtapeCircuit(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    circuit = models.ForeignKey(CircuitLogistique, on_delete=models.CASCADE, related_name='etapes')
    nom = models.CharField(max_length=100)
    ordre = models.PositiveIntegerField(help_text="Position de l'étape dans le circuit (1, 2, 3...)")
    est_finale = models.BooleanField(default=False, help_text="Cochez si cette étape marque la fin du circuit (ex: Déchargé)")
    couleur_badge = models.CharField(max_length=50, default="bg-muted text-muted-foreground", help_text="Classes CSS Tailwind pour l'UI")
    
    class Meta:
        ordering = ['circuit', 'ordre']
        unique_together = ('circuit', 'ordre')

    def __str__(self):
        return f"{self.ordre}. {self.nom} ({self.circuit.nom})"

class Expedition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    identifiant = models.CharField(max_length=50, help_text="Plaque d'immatriculation, N° de vol, N° conteneur...")
    responsable = models.CharField(max_length=255, help_text="Chauffeur, Capitaine, etc.")
    transporteur = models.CharField(max_length=255)
    chargement = models.DecimalField(max_digits=10, decimal_places=2, help_text="Poids en tonnes ou volume")
    
    circuit = models.ForeignKey(CircuitLogistique, on_delete=models.PROTECT, related_name='expeditions')
    etape_actuelle = models.ForeignKey(EtapeCircuit, on_delete=models.PROTECT, null=True, blank=True, related_name='expeditions_en_cours')
    
    date_depart = models.DateTimeField(blank=True, null=True)
    date_arrivee = models.DateTimeField(blank=True, null=True)
    position = models.CharField(max_length=255, blank=True, null=True)
    progression = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    
    document_reference = models.CharField(max_length=100, blank=True, null=True, help_text="BL, LTA, N° Tracking")
    facture_transport = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    frais_douane = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.identifiant} - {self.transporteur}"
