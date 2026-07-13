from rest_framework import serializers
from .models import OperationTerrain

class OperationTerrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = OperationTerrain
        fields = '__all__'
