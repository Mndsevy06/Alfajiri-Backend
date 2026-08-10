import uuid
from django.db import models
from django.conf import settings

class Succursale(models.Model):
    id = models.CharField(max_length=50, primary_key=True) # ex: zambie, lubumbashi
    label = models.CharField(max_length=255)
    short = models.CharField(max_length=10)
    color = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.label

class Dossier(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    raisonSociale = models.CharField(max_length=255)
    sigle = models.CharField(max_length=50, blank=True, null=True)
    statutJuridique = models.CharField(max_length=50, blank=True, null=True)
    rccm = models.CharField(max_length=100, blank=True, null=True)
    idNat = models.CharField(max_length=100, blank=True, null=True)
    nImpot = models.CharField(max_length=100, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    ville = models.CharField(max_length=100, blank=True, null=True)
    pays = models.CharField(max_length=100, blank=True, null=True)
    telephone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    logo = models.CharField(max_length=255, blank=True, null=True)
    devise = models.CharField(max_length=10, default='USD')
    exerciceEnCours = models.CharField(max_length=4)
    dateDebut = models.DateField()
    dateFin = models.DateField()
    compteClient = models.CharField(max_length=50, blank=True, null=True)
    compteFournisseur = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.raisonSociale

class Parametre(models.Model):
    class TypeValeur(models.TextChoices):
        STRING = 'string', 'String'
        BOOLEAN = 'boolean', 'Boolean'
        NUMBER = 'number', 'Number'
        JSON = 'json', 'JSON'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cle = models.CharField(max_length=100, unique=True)
    valeur = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100)
    typeValeur = models.CharField(max_length=20, choices=TypeValeur.choices, default=TypeValeur.STRING)
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.cle} : {self.valeur}"

class ExerciceComptable(models.Model):
    class Statut(models.TextChoices):
        OUVERT = 'ouvert', 'Ouvert'
        CLOTURE = 'cloture', 'Clôturé'

    dossier = models.ForeignKey(Dossier, on_delete=models.CASCADE, related_name='exercices')
    annee = models.IntegerField()
    date_debut = models.DateField()
    date_fin = models.DateField()
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT)

    class Meta:
        unique_together = ('dossier', 'annee')
        ordering = ['-annee']

    def __str__(self):
        return f"{self.dossier.raisonSociale} - {self.annee}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Synchronisation automatique du champ raccourci dans Dossier
        if self.statut == self.Statut.OUVERT:
            Dossier.objects.filter(id=self.dossier_id).update(
                exerciceEnCours=str(self.annee),
                dateDebut=self.date_debut,
                dateFin=self.date_fin
            )
            
            # (Optionnel) Clôturer les autres exercices du même dossier
            ExerciceComptable.objects.filter(
                dossier=self.dossier
            ).exclude(id=self.id).update(statut=self.Statut.CLOTURE)

class TauxChange(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    devise = models.CharField(max_length=10) # e.g. 'CDF'
    date = models.DateField()
    taux = models.DecimalField(max_digits=15, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('devise', 'date')

    def __str__(self):
        return f"{self.devise} - {self.date} - {self.taux}"
