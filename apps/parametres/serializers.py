from rest_framework import serializers
from django.db.models import Max
from .models import Dossier

class DossierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dossier
        fields = '__all__'

    def create(self, validated_data):
        compte_client = validated_data.get('compteClient', '')
        compte_fournisseur = validated_data.get('compteFournisseur', '')

        if compte_client == '411':
            max_compte = Dossier.objects.filter(compteClient__startswith='4111').aggregate(Max('compteClient'))['compteClient__max']
            if max_compte and len(max_compte) >= 6:
                try:
                    aux = int(max_compte[4:]) + 1
                    validated_data['compteClient'] = f"4111{aux:02d}"
                except ValueError:
                    validated_data['compteClient'] = "411101"
            else:
                validated_data['compteClient'] = "411101"

        if compte_fournisseur == '401':
            max_compte = Dossier.objects.filter(compteFournisseur__startswith='401').aggregate(Max('compteFournisseur'))['compteFournisseur__max']
            if max_compte and len(max_compte) >= 6:
                try:
                    aux = int(max_compte[3:]) + 1
                    validated_data['compteFournisseur'] = f"401{aux:03d}"
                except ValueError:
                    validated_data['compteFournisseur'] = "401001"
            else:
                validated_data['compteFournisseur'] = "401001"

        dossier = super().create(validated_data)
        
        from apps.plan_comptable.models import CompteComptable
        
        if dossier.compteClient:
            parent_client = CompteComptable.objects.filter(numero='411100').first()
            if not CompteComptable.objects.filter(numero=dossier.compteClient).exists():
                CompteComptable.objects.create(
                    numero=dossier.compteClient,
                    libelle=f"Client - {dossier.raisonSociale}",
                    classe='4',
                    type='auxiliaire',
                    parent=parent_client,
                    dossier=dossier
                )
                
        if dossier.compteFournisseur:
            parent_fourn = CompteComptable.objects.filter(numero='401100').first()
            if not CompteComptable.objects.filter(numero=dossier.compteFournisseur).exists():
                CompteComptable.objects.create(
                    numero=dossier.compteFournisseur,
                    libelle=f"Fournisseur - {dossier.raisonSociale}",
                    classe='4',
                    type='auxiliaire',
                    parent=parent_fourn,
                    dossier=dossier
                )

        return dossier
