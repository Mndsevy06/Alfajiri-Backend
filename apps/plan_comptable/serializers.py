from rest_framework import serializers
from .models import Journal, CompteComptable, Tiers

class JournalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Journal
        fields = '__all__'

class CompteComptableSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompteComptable
        fields = '__all__'

class TiersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tiers
        fields = '__all__'
