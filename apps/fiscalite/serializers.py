from rest_framework import serializers
from .models import DeclarationFiscale, RetenueSource

class DeclarationFiscaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeclarationFiscale
        fields = '__all__'

class RetenueSourceSerializer(serializers.ModelSerializer):
    tiers_nom = serializers.CharField(source='tiers.nom', read_only=True)

    class Meta:
        model = RetenueSource
        fields = '__all__'
