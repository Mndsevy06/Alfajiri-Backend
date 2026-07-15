from rest_framework import serializers
from .models import CircuitLogistique, EtapeCircuit, Expedition

class EtapeCircuitSerializer(serializers.ModelSerializer):
    class Meta:
        model = EtapeCircuit
        fields = '__all__'

class CircuitLogistiqueSerializer(serializers.ModelSerializer):
    etapes = EtapeCircuitSerializer(many=True, read_only=True)
    
    class Meta:
        model = CircuitLogistique
        fields = '__all__'

class ExpeditionSerializer(serializers.ModelSerializer):
    # Include read-only nested representation of the circuit and current step for the frontend
    etape_actuelle_detail = EtapeCircuitSerializer(source='etape_actuelle', read_only=True)
    circuit_detail = CircuitLogistiqueSerializer(source='circuit', read_only=True)

    class Meta:
        model = Expedition
        fields = '__all__'
        read_only_fields = ['id', 'progression', 'date_arrivee']
