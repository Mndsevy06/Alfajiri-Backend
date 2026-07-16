from django.db import models

class CloturePeriode(models.Model):
    dossier = models.ForeignKey('parametres.Dossier', on_delete=models.CASCADE, null=True, blank=True, related_name='%(class)s_dossier')
    periode = models.CharField(max_length=7, unique=True, help_text="Format YYYY-MM ou YYYY")
    # Checklist de clôture
    centralisation_journaux = models.BooleanField(default=False)
    rapprochement_bancaire = models.BooleanField(default=False)
    inventaire_stocks = models.BooleanField(default=False)
    amortissements_provisions = models.BooleanField(default=False)
    regularisation_charges_produits = models.BooleanField(default=False)
    arrete_comptes_tiers = models.BooleanField(default=False)
    validation_commissaire = models.BooleanField(default=False)

    date_mise_a_jour = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Clôture {self.periode}"
