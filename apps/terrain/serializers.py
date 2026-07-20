from rest_framework import serializers
from .models import OperationTerrain
import base64
from django.core.files.base import ContentFile

class OperationTerrainSerializer(serializers.ModelSerializer):
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_nom = serializers.CharField(write_only=True, required=False, allow_null=True)
    saisie_par_nom = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = OperationTerrain
        fields = '__all__'
        read_only_fields = ['id', 'saisie_par', 'fichier']

    def get_saisie_par_nom(self, obj):
        if obj.saisie_par:
            nom = getattr(obj.saisie_par, 'nom', '')
            if nom:
                return str(nom)
            first_last = f"{obj.saisie_par.first_name} {obj.saisie_par.last_name}".strip()
            return first_last or obj.saisie_par.email
        return "Inconnu"

    def create(self, validated_data):
        fichier_base64 = validated_data.pop('fichier_base64', None)
        fichier_nom = validated_data.pop('fichier_nom', None)
        
        validated_data['saisie_par'] = self.context['request'].user
        
        if fichier_base64 and fichier_nom:
            try:
                format, imgstr = fichier_base64.split(';base64,')
                validated_data['fichier'] = ContentFile(base64.b64decode(imgstr), name=fichier_nom)
            except Exception:
                pass
                
        return super().create(validated_data)
