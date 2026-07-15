from rest_framework import serializers
from .models import Facture
from apps.plan_comptable.serializers import TiersSerializer

class FactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facture
        fields = '__all__'
        read_only_fields = ('numero',)

class FactureReadSerializer(serializers.ModelSerializer):
    client = TiersSerializer(read_only=True)
    
    class Meta:
        model = Facture
        fields = '__all__'
