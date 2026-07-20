from rest_framework import serializers
from .models import Ecriture, LigneEcriture
from django.contrib.auth import get_user_model
import base64
from django.core.files.base import ContentFile

User = get_user_model()

class LigneEcritureSerializer(serializers.ModelSerializer):
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_nom = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_url = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = LigneEcriture
        fields = ['id', 'date', 'compte', 'libelleCompte', 'libelle', 'debit', 'credit', 'centre_cout', 'tiers_auxiliaire', 'fichier', 'fichier_base64', 'fichier_nom', 'fichier_url']
        read_only_fields = ['id', 'fichier']

class EcritureSerializer(serializers.ModelSerializer):
    lignes = LigneEcritureSerializer(many=True)
    saisiePar = serializers.SerializerMethodField()
    validePar = serializers.SerializerMethodField()

    class Meta:
        model = Ecriture
        fields = ['id', 'numero', 'journal', 'date', 'libelle', 'statut', 'saisiePar', 'validePar', 'piece', 'lignes']
        read_only_fields = ['id', 'saisiePar', 'validePar', 'numero', 'piece']

    def get_saisiePar(self, obj):
        if not obj.saisiePar:
            return None
        return obj.saisiePar.nom or f"{obj.saisiePar.first_name} {obj.saisiePar.last_name}".strip() or obj.saisiePar.email
        
    def get_validePar(self, obj):
        if not obj.validePar:
            return None
        return obj.validePar.nom or f"{obj.validePar.first_name} {obj.validePar.last_name}".strip() or obj.validePar.email

    def _process_fichier(self, ligne_data):
        fichier_base64 = ligne_data.pop('fichier_base64', None)
        fichier_nom = ligne_data.pop('fichier_nom', None)
        fichier_url = ligne_data.pop('fichier_url', None)
        if fichier_base64 and fichier_nom:
            try:
                format, imgstr = fichier_base64.split(';base64,')
                ligne_data['fichier'] = ContentFile(base64.b64decode(imgstr), name=fichier_nom)
            except Exception:
                pass
        elif fichier_url:
            from django.conf import settings
            import urllib.parse
            
            parsed_url = urllib.parse.urlparse(fichier_url)
            path = parsed_url.path
            
            if path.startswith(settings.MEDIA_URL):
                relative_path = path[len(settings.MEDIA_URL):]
                ligne_data['fichier'] = relative_path
            else:
                ligne_data['fichier'] = fichier_url
                
        return ligne_data

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        validated_data['saisiePar'] = self.context['request'].user
        
        journal = validated_data['journal']
        date = validated_data.get('date')
        
        # Incrémenter le dernier numéro du journal
        journal.dernierNumero += 1
        journal.save()
        
        # Générer le numéro unique par le backend
        year = date.year
        seq = str(journal.dernierNumero).zfill(5)
        numero_genere = f"{journal.code}-{year}-{seq}"
        
        validated_data['numero'] = numero_genere
        validated_data['piece'] = f"PC-{numero_genere}"

        ecriture = Ecriture.objects.create(**validated_data)
        
        for ligne_data in lignes_data:
            ligne_data = self._process_fichier(ligne_data)
            LigneEcriture.objects.create(ecriture=ecriture, dossier=ecriture.dossier, **ligne_data)
        return ecriture

    def update(self, instance, validated_data):
        lignes_data = validated_data.pop('lignes', None)
        
        # Update Ecriture fields
        instance.numero = validated_data.get('numero', instance.numero)
        instance.journal = validated_data.get('journal', instance.journal)
        instance.date = validated_data.get('date', instance.date)
        instance.libelle = validated_data.get('libelle', instance.libelle)
        
        if validated_data.get('statut') == 'valide' and instance.statut != 'valide':
            instance.validePar = self.context['request'].user
        instance.statut = validated_data.get('statut', instance.statut)
        
        instance.save()

        # Update Lignes: simplest way is to delete old and create new
        if lignes_data is not None:
            instance.lignes.all().delete()
            for ligne_data in lignes_data:
                ligne_data = self._process_fichier(ligne_data)
                LigneEcriture.objects.create(ecriture=instance, dossier=instance.dossier, **ligne_data)

        return instance
