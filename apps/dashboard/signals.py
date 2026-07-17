from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from apps.ventes.models import Facture
from apps.saisie.models import LigneEcriture, Ecriture
from apps.logistique.models import Expedition

def broadcast_dashboard_update(dossier_id=None):
    """ Envoie un signal au channel layer pour rafraîchir le dashboard """
    channel_layer = get_channel_layer()
    groups = ['dashboard_updates_all']
    if dossier_id:
        groups.append(f'dashboard_updates_{dossier_id}')

    for group in groups:
        async_to_sync(channel_layer.group_send)(
            group,
            {
                'type': 'dashboard_message',
                'message': 'update'
            }
        )

@receiver([post_save, post_delete], sender=Facture)
def update_on_facture(sender, instance, **kwargs):
    broadcast_dashboard_update(getattr(instance, 'dossier_id', None))

@receiver([post_save, post_delete], sender=Ecriture)
def update_on_ecriture(sender, instance, **kwargs):
    broadcast_dashboard_update(getattr(instance, 'dossier_id', None))

@receiver([post_save, post_delete], sender=LigneEcriture)
def update_on_ligne_ecriture(sender, instance, **kwargs):
    broadcast_dashboard_update(getattr(instance, 'dossier_id', None))

@receiver([post_save, post_delete], sender=Expedition)
def update_on_expedition(sender, instance, **kwargs):
    broadcast_dashboard_update(getattr(instance, 'dossier_id', None))
