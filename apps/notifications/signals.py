"""
Signaux Django pour la génération automatique de notifications
sur tous les événements métier importants de l'application Alfajiri.
"""
import logging
from decimal import Decimal

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Notification
from .services import send_notification, notify_roles, notify_all_admins

logger = logging.getLogger(__name__)

MONTANT_ANORMAL_PAIEMENT = Decimal('15000000')   # 15 000 000 CDF
MONTANT_ANORMAL_TERRAIN  = Decimal('500000')      # 500 000 CDF
SEUIL_AMORTISSEMENT      = Decimal('80')          # %


# ============================================================
#  VENTES & FACTURATION
# ============================================================
def _try_import_facture():
    try:
        from apps.ventes.models import Facture
        return Facture
    except Exception:
        return None

# Stocker l'ancien statut avant sauvegarde
@receiver(pre_save, sender='ventes.Facture')
def store_old_facture_statut(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_statut = sender.objects.get(pk=instance.pk).statut
        except sender.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender='ventes.Facture')
def notify_on_facture(sender, instance, created, **kwargs):
    try:
        client_nom = instance.client.nom if instance.client else 'Client inconnu'
        montant = instance.montantTTC or instance.montantHT or 0

        if created:
            notify_roles(
                ['Chef Comptable', 'Super Admin', 'Comptable'],
                titre=f'Nouvelle facture créée — {instance.numero}',
                message=f'Facture {instance.numero} créée pour {client_nom} — Montant TTC : {montant:,.0f} CDF',
                type=Notification.Type.INFO,
                module=Notification.Module.VENTES,
                action_url='/ventes',
                meta={'facture_id': str(instance.id), 'numero': instance.numero},
            )
        else:
            old = getattr(instance, '_old_statut', None)
            if old and old != instance.statut:
                if instance.statut == 'payee':
                    notify_roles(
                        ['Chef Comptable', 'Super Admin', 'Comptable', 'Directeur'],
                        titre=f'Paiement reçu ✓ — {instance.numero}',
                        message=f'La facture {instance.numero} ({client_nom}) a été soldée intégralement — {montant:,.0f} CDF',
                        type=Notification.Type.INFO,
                        module=Notification.Module.VENTES,
                        action_url='/ventes',
                        meta={'facture_id': str(instance.id)},
                    )
                elif instance.statut == 'partielle':
                    notify_roles(
                        ['Chef Comptable', 'Comptable'],
                        titre=f'Paiement partiel reçu — {instance.numero}',
                        message=f'Paiement partiel sur {instance.numero} ({client_nom}). Solde non réglé restant.',
                        type=Notification.Type.WARNING,
                        module=Notification.Module.VENTES,
                        action_url='/ventes',
                        meta={'facture_id': str(instance.id)},
                    )

            # Vérifier les retards d'échéance
            if instance.statut == 'impayee' and instance.echeance:
                from datetime import date
                jours_retard = (date.today() - instance.echeance).days
                if jours_retard >= 30:
                    notify_roles(
                        ['Chef Comptable', 'Directeur', 'Super Admin'],
                        titre=f'Retard critique — {instance.numero} ({jours_retard}j)',
                        message=f'Facture {instance.numero} ({client_nom}) non réglée depuis {jours_retard} jours — {montant:,.0f} CDF — Relance urgente requise',
                        type=Notification.Type.CRITICAL,
                        module=Notification.Module.VENTES,
                        action_url='/ventes',
                        meta={'facture_id': str(instance.id), 'jours_retard': jours_retard},
                    )
                elif jours_retard >= 1:
                    notify_roles(
                        ['Comptable', 'Chef Comptable'],
                        titre=f'Facture impayée à échéance — {instance.numero}',
                        message=f'La facture {instance.numero} ({client_nom}, {montant:,.0f} CDF) est arrivée à échéance il y a {jours_retard} jour(s)',
                        type=Notification.Type.URGENT,
                        module=Notification.Module.VENTES,
                        action_url='/ventes',
                        meta={'facture_id': str(instance.id)},
                    )
    except Exception as e:
        logger.error(f'[notifications] erreur signal facture: {e}')


# ============================================================
#  SAISIE COMPTABLE
# ============================================================
@receiver(pre_save, sender='saisie.Ecriture')
def store_old_ecriture_statut(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_statut = sender.objects.get(pk=instance.pk).statut
        except sender.DoesNotExist:
            instance._old_statut = None
    else:
        instance._old_statut = None


@receiver(post_save, sender='saisie.Ecriture')
def notify_on_ecriture(sender, instance, created, **kwargs):
    try:
        if created:
            notify_roles(
                ['Chef Comptable', 'Super Admin'],
                titre=f'Nouvelle écriture créée — {instance.numero}',
                message=f'Écriture {instance.numero} ({instance.libelle}) créée en brouillard',
                type=Notification.Type.INFO,
                module=Notification.Module.COMPTABILITE,
                action_url='/saisie',
                meta={'ecriture_id': str(instance.id)},
            )
        else:
            old = getattr(instance, '_old_statut', None)
            if old == 'brouillard' and instance.statut == 'valide':
                valideur = instance.validePar.nom if instance.validePar else 'Système'
                notify_roles(
                    ['Chef Comptable', 'Directeur', 'Super Admin'],
                    titre=f'Écriture validée ✓ — {instance.numero}',
                    message=f'L\'écriture {instance.numero} ({instance.libelle}) a été validée et verrouillée par {valideur}',
                    type=Notification.Type.INFO,
                    module=Notification.Module.COMPTABILITE,
                    action_url='/saisie',
                    meta={'ecriture_id': str(instance.id)},
                )
    except Exception as e:
        logger.error(f'[notifications] erreur signal ecriture: {e}')


# ============================================================
#  PAIEMENTS & TRÉSORERIE
# ============================================================
@receiver(post_save, sender='paiements.Paiement')
def notify_on_paiement(sender, instance, created, **kwargs):
    try:
        if created:
            montant = Decimal(str(instance.montant))
            type_label = 'Encaissement' if instance.type == 'encaissement' else 'Décaissement'
            tiers_nom = instance.tiers.nom if instance.tiers else 'Tiers inconnu'

            if montant >= MONTANT_ANORMAL_PAIEMENT:
                notify_all_admins(
                    titre=f'⚠️ Montant inhabituel — {type_label}',
                    message=f'Un {type_label.lower()} de {montant:,.0f} CDF ({tiers_nom}) dépasse le seuil habituel de {MONTANT_ANORMAL_PAIEMENT:,.0f} CDF — Vérification recommandée',
                    type=Notification.Type.URGENT,
                    module=Notification.Module.PAIEMENTS,
                    action_url='/paiements',
                    meta={'paiement_id': str(instance.id), 'montant': float(montant)},
                )
            else:
                notify_roles(
                    ['Comptable', 'Chef Comptable'],
                    titre=f'{type_label} enregistré — {instance.reference}',
                    message=f'{type_label} de {montant:,.0f} CDF ({instance.get_mode_display()}) — {tiers_nom} — Réf. {instance.reference}',
                    type=Notification.Type.INFO,
                    module=Notification.Module.PAIEMENTS,
                    action_url='/paiements',
                    meta={'paiement_id': str(instance.id)},
                )
    except Exception as e:
        logger.error(f'[notifications] erreur signal paiement: {e}')


# ============================================================
#  LOGISTIQUE — EXPÉDITIONS
# ============================================================
@receiver(pre_save, sender='logistique.Expedition')
def store_old_expedition_etape(sender, instance, **kwargs):
    if instance.pk:
        try:
            instance._old_etape = sender.objects.get(pk=instance.pk).etape_courante
        except sender.DoesNotExist:
            instance._old_etape = None
    else:
        instance._old_etape = None


@receiver(post_save, sender='logistique.Expedition')
def notify_on_expedition(sender, instance, created, **kwargs):
    try:
        if created:
            notify_roles(
                ['Agent', 'Chef Comptable', 'Directeur'],
                titre=f'Nouvelle expédition — {instance.reference}',
                message=f'Expédition {instance.reference} créée ({instance.origine} → {instance.destination})',
                type=Notification.Type.INFO,
                module=Notification.Module.LOGISTIQUE,
                action_url='/logistique',
                meta={'expedition_id': str(instance.id)},
            )
        else:
            old_etape = getattr(instance, '_old_etape', None)
            if old_etape and old_etape != instance.etape_courante:
                notify_roles(
                    ['Chef Comptable', 'Directeur', 'Agent'],
                    titre=f'Étape mise à jour — {instance.reference}',
                    message=f'Expédition {instance.reference} : étape "{instance.etape_courante}" validée',
                    type=Notification.Type.INFO,
                    module=Notification.Module.LOGISTIQUE,
                    action_url='/logistique',
                    meta={'expedition_id': str(instance.id), 'etape': instance.etape_courante},
                )
    except Exception as e:
        logger.error(f'[notifications] erreur signal expedition: {e}')


# ============================================================
#  TERRAIN
# ============================================================
@receiver(post_save, sender='terrain.OperationTerrain')
def notify_on_operation_terrain(sender, instance, created, **kwargs):
    try:
        if not created:
            return
        montant = Decimal(str(instance.montant))
        type_label = 'Dépense' if instance.type_op == 'depense' else 'Recette'

        if montant >= MONTANT_ANORMAL_TERRAIN:
            notify_roles(
                ['Chef Comptable', 'Super Admin'],
                titre=f'⚠️ {type_label} terrain inhabituelle',
                message=f'{type_label} de {montant:,.0f} CDF ({instance.nature}) dépasse le seuil habituel — Vérification requise',
                type=Notification.Type.URGENT,
                module=Notification.Module.TERRAIN,
                action_url='/terrain',
                meta={'operation_id': str(instance.id), 'montant': float(montant)},
            )
        elif not instance.has_photo:
            notify_roles(
                ['Comptable', 'Chef Comptable'],
                titre=f'{type_label} terrain sans justificatif',
                message=f'{type_label} de {montant:,.0f} CDF ({instance.nature}) soumise sans photo justificative — Validation manuelle requise',
                type=Notification.Type.WARNING,
                module=Notification.Module.TERRAIN,
                action_url='/terrain',
                meta={'operation_id': str(instance.id)},
            )
        else:
            notify_roles(
                ['Comptable'],
                titre=f'{type_label} terrain reçue',
                message=f'{type_label} de {montant:,.0f} CDF ({instance.nature}) — Photo jointe ✓',
                type=Notification.Type.INFO,
                module=Notification.Module.TERRAIN,
                action_url='/terrain',
                meta={'operation_id': str(instance.id)},
            )
    except Exception as e:
        logger.error(f'[notifications] erreur signal terrain: {e}')


# ============================================================
#  RH & PAIE
# ============================================================
@receiver(post_save, sender='rh.BulletinPaie')
def notify_on_bulletin(sender, instance, created, **kwargs):
    try:
        employe_nom = instance.employe.nom if instance.employe else 'Employé'
        if created:
            notify_roles(
                ['Chef Comptable', 'Super Admin'],
                titre=f'Bulletin de paie généré — {employe_nom}',
                message=f'Bulletin {instance.periode} généré pour {employe_nom} — Net à payer : {instance.net_a_payer:,.0f} CDF',
                type=Notification.Type.INFO,
                module=Notification.Module.RH,
                action_url='/rh',
                meta={'bulletin_id': str(instance.id), 'periode': instance.periode},
            )
        elif instance.statut == 'valide':
            notify_roles(
                ['Chef Comptable', 'Directeur', 'Super Admin'],
                titre=f'Paie validée ✓ — {instance.periode}',
                message=f'Le bulletin de {employe_nom} ({instance.periode}) a été validé — Net : {instance.net_a_payer:,.0f} CDF',
                type=Notification.Type.INFO,
                module=Notification.Module.RH,
                action_url='/rh',
                meta={'bulletin_id': str(instance.id)},
            )
    except Exception as e:
        logger.error(f'[notifications] erreur signal bulletin: {e}')


# ============================================================
#  IMMOBILISATIONS
# ============================================================
@receiver(post_save, sender='immobilisations.Immobilisation')
def notify_on_immobilisation(sender, instance, created, **kwargs):
    try:
        if created:
            notify_roles(
                ['Chef Comptable', 'Super Admin'],
                titre=f'Nouvelle immobilisation — {instance.code}',
                message=f'{instance.libelle} ({instance.categorie}) enregistrée — Valeur : {instance.valeurAcquisition:,.0f} CDF | Durée : {instance.duree} ans',
                type=Notification.Type.INFO,
                module=Notification.Module.IMMOBILISATIONS,
                action_url='/immobilisations',
                meta={'immo_id': str(instance.id)},
            )
        else:
            # Vérifier le taux d'amortissement
            if instance.valeurAcquisition and instance.valeurAcquisition > 0:
                taux = (instance.cumulAmortissement / instance.valeurAcquisition) * 100
                if taux >= 100:
                    notify_roles(
                        ['Chef Comptable', 'Directeur'],
                        titre=f'Immobilisation totalement amortie — {instance.code}',
                        message=f'{instance.libelle} est entièrement amortie (VNC = 0). Prévoir le remplacement.',
                        type=Notification.Type.URGENT,
                        module=Notification.Module.IMMOBILISATIONS,
                        action_url='/immobilisations',
                        meta={'immo_id': str(instance.id), 'taux': float(taux)},
                    )
                elif taux >= 80:
                    notify_roles(
                        ['Chef Comptable'],
                        titre=f'Alerte usure — {instance.code} ({taux:.0f}%)',
                        message=f'{instance.libelle} est amorti à {taux:.0f}% — VNC actuelle : {instance.vnc:,.0f} CDF — Prévoir le remplacement',
                        type=Notification.Type.WARNING,
                        module=Notification.Module.IMMOBILISATIONS,
                        action_url='/immobilisations',
                        meta={'immo_id': str(instance.id), 'taux': float(taux)},
                    )
    except Exception as e:
        logger.error(f'[notifications] erreur signal immobilisation: {e}')


# ============================================================
#  FISCALITÉ
# ============================================================
@receiver(post_save, sender='fiscalite.DeclarationFiscale')
def notify_on_declaration(sender, instance, created, **kwargs):
    try:
        from datetime import date
        if created:
            notify_roles(
                ['Chef Comptable', 'Comptable'],
                titre=f'Déclaration {instance.type_declaration} créée — {instance.periode}',
                message=f'Déclaration {instance.type_declaration} ({instance.periode}) créée — Montant : {instance.montant:,.0f} CDF — Échéance : {instance.echeance}',
                type=Notification.Type.INFO,
                module=Notification.Module.FISCALITE,
                action_url='/fiscalite',
                meta={'declaration_id': str(instance.id)},
            )
        elif instance.statut == 'Déclaré et Payé':
            notify_roles(
                ['Chef Comptable', 'Directeur', 'Super Admin'],
                titre=f'Déclaration {instance.type_declaration} soumise ✓',
                message=f'Déclaration {instance.type_declaration} ({instance.periode}) soumise et archivée — {instance.montant:,.0f} CDF',
                type=Notification.Type.INFO,
                module=Notification.Module.FISCALITE,
                action_url='/fiscalite',
                meta={'declaration_id': str(instance.id)},
            )
        elif instance.statut == 'En retard':
            notify_all_admins(
                titre=f'🚨 Retard fiscal — {instance.type_declaration} {instance.periode}',
                message=f'La déclaration {instance.type_declaration} ({instance.periode}) n\'a pas été déposée à temps — Pénalités en cours',
                type=Notification.Type.CRITICAL,
                module=Notification.Module.FISCALITE,
                action_url='/fiscalite',
                meta={'declaration_id': str(instance.id)},
            )

        # Rappels d'échéance automatiques
        if instance.statut not in ('Déclaré et Payé',) and instance.echeance:
            jours = (instance.echeance - date.today()).days
            if jours == 3:
                notify_roles(
                    ['Chef Comptable', 'Comptable'],
                    titre=f'URGENT : Déclaration {instance.type_declaration} dans 3 jours',
                    message=f'La déclaration {instance.type_declaration} ({instance.periode}) est due dans 3 jours — Préparer le paiement',
                    type=Notification.Type.URGENT,
                    module=Notification.Module.FISCALITE,
                    action_url='/fiscalite',
                    meta={'declaration_id': str(instance.id), 'jours': jours},
                )
            elif jours == 7:
                notify_roles(
                    ['Chef Comptable'],
                    titre=f'Rappel : Déclaration {instance.type_declaration} dans 7 jours',
                    message=f'La déclaration {instance.type_declaration} ({instance.periode}) doit être déposée avant le {instance.echeance}',
                    type=Notification.Type.WARNING,
                    module=Notification.Module.FISCALITE,
                    action_url='/fiscalite',
                    meta={'declaration_id': str(instance.id), 'jours': jours},
                )
    except Exception as e:
        logger.error(f'[notifications] erreur signal declaration: {e}')


# ============================================================
#  UTILISATEURS & SÉCURITÉ
# ============================================================
@receiver(post_save, sender='authentification.User')
def notify_on_user_change(sender, instance, created, **kwargs):
    try:
        if created:
            notify_all_admins(
                titre=f'Nouvel utilisateur créé — {instance.email}',
                message=f'Compte créé pour {instance.nom or instance.email} — Rôle : {instance.role} — Site : {instance.site or "Non défini"}',
                type=Notification.Type.WARNING,
                module=Notification.Module.SECURITE,
                action_url='/utilisateurs',
                meta={'user_id': str(instance.id), 'email': instance.email},
            )
    except Exception as e:
        logger.error(f'[notifications] erreur signal user: {e}')
