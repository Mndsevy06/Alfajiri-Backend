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

    def get_amortissement_plan(self):
        from datetime import date
        
        plan = []
        if float(self.valeurAcquisition) <= 0 or self.duree <= 0:
            return plan

        vnc = float(self.valeurAcquisition)
        valeur_origine = float(self.valeurAcquisition)
        
        # Taux linéaire
        taux_lineaire = 1.0 / self.duree
        
        # Coeff dégressif (simplifié, souvent 1.25, 1.75, 2.25 selon la durée)
        coeff = 1.5 if self.duree < 5 else (1.75 if self.duree <= 6 else 2.25)
        taux_degressif = taux_lineaire * coeff
        
        # Prorata temporis première année
        acq_date = self.dateAcquisition
        if not acq_date:
            acq_date = date.today()
            
        annee_base = acq_date.year
        
        if self.methode in [self.Methode.LINEAIRE, self.Methode.UNITES_OEUVRE]:
            jour = min(acq_date.day, 30)
            jours_restants = (30 - jour + 1) + (12 - acq_date.month) * 30
            prorata_premiere_annee = jours_restants / 360.0
        elif self.methode == self.Methode.DEGRESSIVE:
            mois_restants = 13 - acq_date.month
            prorata_premiere_annee = mois_restants / 12.0
        else: # EXCEPTIONNELLE
            prorata_premiere_annee = 1.0

        cumul = 0.0
        
        # Le nombre d'années d'amortissement peut s'étendre sur duree + 1 si prorata < 1
        annee_courante = 1
        annee_fiscale = annee_base
        
        while vnc > 0.01 and annee_courante <= self.duree + 1:
            base = valeur_origine if self.methode == self.Methode.LINEAIRE else vnc
            
            if self.methode == self.Methode.EXCEPTIONNELLE:
                dotation = vnc
            elif self.methode in [self.Methode.LINEAIRE, self.Methode.UNITES_OEUVRE]:
                if annee_courante == 1:
                    dotation = base * taux_lineaire * prorata_premiere_annee
                elif annee_courante == self.duree + 1:
                    # Dernière année (reliquat du prorata)
                    dotation = vnc
                else:
                    dotation = base * taux_lineaire
            elif self.methode == self.Methode.DEGRESSIVE:
                # Dégressif
                duree_restante = self.duree - annee_courante + 1
                if duree_restante > 0:
                    taux_lin_restant = 1.0 / duree_restante
                else:
                    taux_lin_restant = 1.0
                    
                taux_retenu = max(taux_degressif, taux_lin_restant)
                
                if annee_courante == 1:
                    dotation = base * taux_retenu * prorata_premiere_annee
                else:
                    dotation = base * taux_retenu
                    
            if dotation > vnc or annee_courante == self.duree + (1 if prorata_premiere_annee < 1.0 else 0):
                dotation = vnc
                
            vnc -= dotation
            cumul += dotation
            
            plan.append({
                'annee': annee_fiscale,
                'baseAmortissable': round(base, 2),
                'dotation': round(dotation, 2),
                'cumul': round(cumul, 2),
                'vnc': round(max(vnc, 0), 2)
            })
            
            annee_courante += 1
            annee_fiscale += 1
            
            if round(vnc, 2) <= 0:
                break
                
        return plan

    def calculate_current_state(self, current_date=None):
        from datetime import date
        if not current_date:
            current_date = date.today()
            
        plan = self.get_amortissement_plan()
        current_year = current_date.year
        
        cumul = 0.0
        vnc = float(self.valeurAcquisition)
        dotation_annuelle = 0.0
        
        for ligne in plan:
            if ligne['annee'] == current_year:
                dotation_annuelle = ligne['dotation']
                
            if ligne['annee'] <= current_year:
                cumul = ligne['cumul']
                vnc = ligne['vnc']
                
        from decimal import Decimal
        self.cumulAmortissement = Decimal(str(cumul))
        self.vnc = Decimal(str(vnc))
        self.dotationAnnuelle = Decimal(str(dotation_annuelle))
