from rest_framework import serializers
from .models import Contrat, BulletinPaie
from apps.plan_comptable.serializers import TiersSerializer

class ContratSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contrat
        fields = '__all__'

class BulletinPaieSerializer(serializers.ModelSerializer):
    employe_nom = serializers.CharField(source='employe.nom', read_only=True)
    employe_photo_profil = serializers.ImageField(source='employe.photo_profil', read_only=True)
    
    class Meta:
        model = BulletinPaie
        fields = '__all__'
