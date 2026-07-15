from rest_framework import serializers
from .models import LigneReleve, Rapprochement
from apps.saisie.models import LigneEcriture

class RapprochementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rapprochement
        fields = '__all__'

class LigneReleveSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneReleve
        fields = '__all__'

class LigneEcritureRapprochementSerializer(serializers.ModelSerializer):
    compte_numero = serializers.CharField(source='compte.numero', read_only=True)
    ecriture_numero = serializers.CharField(source='ecriture.numero', read_only=True)

    class Meta:
        model = LigneEcriture
        fields = ['id', 'date', 'libelle', 'compte_numero', 'ecriture_numero', 'debit', 'credit', 'rapprochement']
