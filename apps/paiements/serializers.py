from rest_framework import serializers
from .models import Paiement

class PaiementSerializer(serializers.ModelSerializer):
    tiers_nom = serializers.CharField(source='tiers.nom', read_only=True)
    tiers_type = serializers.CharField(source='tiers.type', read_only=True)
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'type', 'date', 'tiers', 'tiers_nom', 'tiers_type',
            'montant', 'mode', 'reference', 'justificatif', 'memo',
            'statut', 'date_creation'
        ]
        read_only_fields = ['id', 'date_creation']
