from rest_framework import serializers
from .models import OperationTerrain
import base64
import logging
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

class OperationTerrainSerializer(serializers.ModelSerializer):
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_nom = serializers.CharField(write_only=True, required=False, allow_null=True)
    saisie_par_nom = serializers.SerializerMethodField(read_only=True)
    
    nature = serializers.CharField(max_length=50, required=True, error_messages={'max_length': 'La nature ne peut pas dépasser 50 caractères.'})
    notes = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True, error_messages={'max_length': 'Les notes ne peuvent pas dépasser 50 caractères.'})
    numero_facture = serializers.CharField(max_length=100, required=True, error_messages={'required': 'Le numéro de facture est obligatoire.', 'blank': 'Le numéro de facture ne peut pas être vide.'})

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
            except Exception as e:
                logger.warning(f"Fichier base64 invalide (terrain, ignoré) : {e}")
                
        return super().create(validated_data)
