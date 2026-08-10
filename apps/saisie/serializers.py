from rest_framework import serializers
from .models import Ecriture, LigneEcriture
from django.contrib.auth import get_user_model
from django.db import transaction
import logging
import base64
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

User = get_user_model()

class LigneEcritureSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(required=False)
    fichier_base64 = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_nom = serializers.CharField(write_only=True, required=False, allow_null=True)
    fichier_url = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = LigneEcriture
        fields = ['id', 'numero_ligne', 'date', 'compte', 'libelleCompte', 'libelle', 'debit', 'credit', 'centre_cout', 'tiers_auxiliaire', 'fichier', 'fichier_base64', 'fichier_nom', 'fichier_url', 'devise_origine', 'taux_change', 'montant_debit_origine', 'montant_credit_origine']
        read_only_fields = ['fichier', 'numero_ligne']

class EcritureSerializer(serializers.ModelSerializer):
    lignes = LigneEcritureSerializer(many=True)
    saisiePar = serializers.SerializerMethodField()
    validePar = serializers.SerializerMethodField()
    batch_number = serializers.CharField(source='numero', read_only=True)

    class Meta:
        model = Ecriture
        fields = ['id', 'numero', 'batch_number', 'numero_facture', 'journal', 'date', 'created_at', 'libelle', 'statut', 'saisiePar', 'validePar', 'piece', 'lignes']
        read_only_fields = ['id', 'saisiePar', 'validePar', 'numero', 'piece', 'created_at']

    def validate(self, data):
        lignes = data.get('lignes', None)
        if not self.instance or lignes is not None:

            # ── R-MIN : Au moins 2 lignes ────────────────────────────────────────
            if not lignes or len(lignes) < 2:
                raise serializers.ValidationError(
                    "Une opération doit comporter au minimum 2 lignes (au moins une au Débit et une au Crédit)."
                )

            # ── Nouvelles règles métier (OHADA) ──────────────────────────────────
            for idx, l in enumerate(lignes):
                compte = l.get('compte')
                if compte:
                    if len(compte.numero) != 6:
                        raise serializers.ValidationError(f"Le compte {compte.numero} n'est pas saisissable (doit comporter exactement 6 caractères).")
                    
                    if compte.numero.startswith('4') and not l.get('tiers_auxiliaire'):
                        raise serializers.ValidationError(f"Un tiers auxiliaire est obligatoire pour le compte {compte.numero} (Ligne {idx+1}).")
                    
                    if (compte.numero.startswith('6') or compte.numero.startswith('7')) and not l.get('centre_cout'):
                        raise serializers.ValidationError(f"Un centre de coût est obligatoire pour le compte de gestion {compte.numero} (Ligne {idx+1}).")
                
                libelle = l.get('libelle')
                if not libelle or not str(libelle).strip():
                    raise serializers.ValidationError(f"Le libellé de la ligne {idx+1} est obligatoire.")

            lignes_actives = [
                l for l in lignes
                if float(l.get('debit', 0)) > 0 or float(l.get('credit', 0)) > 0
            ]

            # ── R7 : Pas de montant nul ou négatif ───────────────────────────────
            for l in lignes_actives:
                if float(l.get('debit', 0)) < 0 or float(l.get('credit', 0)) < 0:
                    raise serializers.ValidationError(
                        f"Les montants négatifs sont interdits sur la ligne du compte {l.get('compte', '?')} (OHADA)."
                    )

            # ── R1 : Au moins une ligne Débit ET une ligne Crédit ───────────────
            lignes_debit = [l for l in lignes_actives if float(l.get('debit', 0)) > 0]
            lignes_credit = [l for l in lignes_actives if float(l.get('credit', 0)) > 0]

            if not lignes_debit:
                raise serializers.ValidationError(
                    "L'écriture doit comporter au moins une ligne au Débit (principe de la partie double — OHADA)."
                )
            if not lignes_credit:
                raise serializers.ValidationError(
                    "L'écriture doit comporter au moins une ligne au Crédit (principe de la partie double — OHADA)."
                )

            # ── R2 : Pas de compensation — même compte au Débit ET au Crédit ────
            comptes_debit = set(l.get('compte') for l in lignes_debit if l.get('compte'))
            comptes_credit = set(l.get('compte') for l in lignes_credit if l.get('compte'))
            comptes_compenses = comptes_debit & comptes_credit
            if comptes_compenses:
                raise serializers.ValidationError(
                    f"Le compte {list(comptes_compenses)[0]} figure à la fois au Débit et au Crédit. "
                    "La compensation de comptes est interdite (OHADA)."
                )

            # ── R3 : Pas de doublon dans le même sens ────────────────────────────
            comptes_debit_list = [l.get('compte') for l in lignes_debit if l.get('compte')]
            comptes_credit_list = [l.get('compte') for l in lignes_credit if l.get('compte')]
            if len(comptes_debit_list) != len(set(comptes_debit_list)):
                raise serializers.ValidationError(
                    "Un même compte apparaît plusieurs fois au Débit. Regroupez les montants en une seule ligne (OHADA)."
                )
            if len(comptes_credit_list) != len(set(comptes_credit_list)):
                raise serializers.ValidationError(
                    "Un même compte apparaît plusieurs fois au Crédit. Regroupez les montants en une seule ligne (OHADA)."
                )

            # ── R6 : Équilibre Débit = Crédit ────────────────────────────────────
            total_debit = sum(float(l.get('debit', 0)) for l in lignes)
            total_credit = sum(float(l.get('credit', 0)) for l in lignes)
            if round(total_debit, 2) != round(total_credit, 2):
                raise serializers.ValidationError(
                    f"L'écriture n'est pas équilibrée "
                    f"(Total Débit: {total_debit:.2f} ≠ Total Crédit: {total_credit:.2f}) — OHADA."
                )

        return data

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
            except Exception as e:
                # BUG-4 fix: loguer l'erreur au lieu de l'ignorer silencieusement
                logger.warning(f"Fichier base64 invalide ou mal formaté (ignoré) : {e}")
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

    @transaction.atomic
    def create(self, validated_data):
        lignes_data = validated_data.pop('lignes')
        validated_data['saisiePar'] = self.context['request'].user
        
        # BUG-1 fix: select_for_update() verrouille le journal le temps de la transaction
        # pour éviter la race condition sur le numéro de lot (Batch Number)
        from apps.plan_comptable.models import Journal
        journal = Journal.objects.select_for_update().get(pk=validated_data['journal'].pk)
        validated_data['journal'] = journal
        date = validated_data.get('date')
        
        year = date.year
        journal.dernierNumero += 1
        seq = str(journal.dernierNumero).zfill(5)
        numero_genere = f"{journal.code}-{year}-{seq}"
        journal.save()
        
        validated_data['numero'] = numero_genere
        validated_data['piece'] = f"PC-{numero_genere}"

        # BUG-2 fix: grâce à @transaction.atomic, si une LigneEcriture échoue,
        # l'Ecriture header est aussi annulée (rollback complet)
        ecriture = Ecriture.objects.create(**validated_data)
        
        for idx, ligne_data in enumerate(lignes_data, start=1):
            ligne_data = self._process_fichier(ligne_data)
            numero_ligne = f"PC-{numero_genere}/L{str(idx).zfill(2)}"
            LigneEcriture.objects.create(
                ecriture=ecriture,
                dossier=ecriture.dossier,
                numero_ligne=numero_ligne,
                **ligne_data
            )
        return ecriture

    def update(self, instance, validated_data):
        if instance.statut == 'valide':
            raise serializers.ValidationError("Impossible de modifier une écriture déjà validée. Vous devez passer par une écriture d'extourne.")
            
        lignes_data = validated_data.pop('lignes', None)
        
        # Update Ecriture fields
        instance.numero_facture = validated_data.get('numero_facture', instance.numero_facture)
        instance.journal = validated_data.get('journal', instance.journal)
        instance.date = validated_data.get('date', instance.date)
        instance.libelle = validated_data.get('libelle', instance.libelle)
        
        if validated_data.get('statut') == 'valide' and instance.statut != 'valide':
            instance.validePar = self.context['request'].user
        instance.statut = validated_data.get('statut', instance.statut)
        
        instance.save()

        # Update Lignes intelligemment pour préserver la piste d'audit
        if lignes_data is not None:
            lignes_existantes = {ligne.id: ligne for ligne in instance.lignes.all()}
            
            for idx, ligne_data in enumerate(lignes_data, start=1):
                ligne_data = self._process_fichier(ligne_data)
                ligne_id = ligne_data.pop('id', None)
                numero_ligne = f"PC-{instance.numero}/L{str(idx).zfill(2)}"
                
                if ligne_id and ligne_id in lignes_existantes:
                    # Mise à jour ligne existante
                    ligne_obj = lignes_existantes.pop(ligne_id)
                    ligne_obj.numero_ligne = numero_ligne
                    for attr, value in ligne_data.items():
                        setattr(ligne_obj, attr, value)
                    ligne_obj.save()
                else:
                    # Création d'une nouvelle ligne
                    LigneEcriture.objects.create(
                        ecriture=instance,
                        dossier=instance.dossier,
                        numero_ligne=numero_ligne,
                        **ligne_data
                    )
            
            # Supprimer les lignes orphelines
            for ligne_obj in lignes_existantes.values():
                ligne_obj.delete()

        return instance
