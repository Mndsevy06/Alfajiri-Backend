from rest_framework import serializers
from .models import Ecriture, LigneEcriture
from django.contrib.auth import get_user_model

User = get_user_model()

class LigneEcritureSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneEcriture
        fields = ['id', 'date', 'compte', 'libelleCompte', 'libelle', 'debit', 'credit', 'centre_cout', 'tiers_auxiliaire']
        read_only_fields = ['id']

class EcritureSerializer(serializers.ModelSerializer):
    lignes = LigneEcritureSerializer(many=True)
    saisiePar = serializers.SerializerMethodField()
    validePar = serializers.SerializerMethodField()

    class Meta:
        model = Ecriture
        fields = ['id', 'numero', 'journal', 'date', 'libelle', 'statut', 'saisiePar', 'validePar', 'piece', 'lignes']
        read_only_fields = ['id', 'saisiePar', 'validePar']

    def get_saisiePar(self, obj):
        return obj.saisiePar.email if obj.saisiePar else None
        
    def get_validePar(self, obj):
        return obj.validePar.email if obj.validePar else None

    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        validated_data['saisiePar'] = self.context['request'].user
        ecriture = Ecriture.objects.create(**validated_data)
        for ligne_data in lignes_data:
            LigneEcriture.objects.create(ecriture=ecriture, **ligne_data)
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
                LigneEcriture.objects.create(ecriture=instance, **ligne_data)

        return instance
