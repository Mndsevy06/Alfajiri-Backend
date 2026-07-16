import uuid
from django.db import models

class Immobilisation(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    class Methode(models.TextChoices):
        LINEAIRE = 'lineaire', 'Linéaire'
        DEGRESSIVE = 'degressive', 'Dégressive'
        EXCEPTIONNELLE = 'exceptionnelle', 'Exceptionnelle'
        UNITES_OEUVRE = 'unites_oeuvre', 'Unités d\'œuvre'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50)
    libelle = models.CharField(max_length=255)
    categorie = models.CharField(max_length=100)
    dateAcquisition = models.DateField()
    valeurAcquisition = models.DecimalField(max_digits=15, decimal_places=2)
    duree = models.IntegerField(help_text="Durée en années")
    methode = models.CharField(max_length=20, choices=Methode.choices, default=Methode.LINEAIRE)
    cumulAmortissement = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    vnc = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    dotationAnnuelle = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    succursale = models.ForeignKey('parametres.Succursale', on_delete=models.CASCADE, related_name='immobilisations')

    def __str__(self):
        return f"{self.code} - {self.libelle}"
