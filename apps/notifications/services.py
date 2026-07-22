from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model

from .models import Notification

User = get_user_model()


def send_notification(
    *,
    user=None,          # User instance or None for broadcast
    dossier=None,       # Dossier instance or None
    titre: str,
    message: str,
    type: str = Notification.Type.INFO,
    module: str = Notification.Module.SECURITE,
    action_url: str | None = None,
    meta: dict | None = None,
    broadcast: bool = False,   # True → envoyer à tous les users connectés
) -> Notification:
    """
    Crée une Notification en DB et la pousse via WebSocket en temps réel.
    """
    notif = Notification.objects.create(
        user=user,
        dossier=dossier,
        titre=titre,
        message=message,
        type=type,
        module=module,
        action_url=action_url,
        meta=meta or {},
    )

    payload = {
        'type': 'notification_message',
        'notification': {
            'id': str(notif.id),
            'dossier_id': str(notif.dossier_id) if notif.dossier_id else None,
            'titre': notif.titre,
            'message': notif.message,
            'type': notif.type,
            'module': notif.module,
            'action_url': notif.action_url,
            'lu': notif.lu,
            'cree_le': notif.cree_le.isoformat(),
            'meta': notif.meta,
        },
    }

    channel_layer = get_channel_layer()

    if broadcast or user is None:
        # Envoyer au groupe broadcast (tous les utilisateurs connectés)
        async_to_sync(channel_layer.group_send)('notifications_broadcast', payload)
    else:
        # Envoyer uniquement au canal personnel de l'utilisateur
        group = f'notifications_user_{user.id}'
        async_to_sync(channel_layer.group_send)(group, payload)

    return notif


def notify_all_admins(titre: str, message: str, type: str, module: str, action_url: str | None = None, meta: dict | None = None, dossier=None):
    """Envoie une notification à tous les Super Admin connectés."""
    admins = User.objects.filter(role='Super Admin', is_active=True)
    for admin in admins:
        send_notification(
            user=admin,
            dossier=dossier,
            titre=titre,
            message=message,
            type=type,
            module=module,
            action_url=action_url,
            meta=meta,
        )


def notify_roles(roles: list, titre: str, message: str, type: str, module: str, action_url: str | None = None, meta: dict | None = None, dossier=None):
    """Envoie une notification à tous les utilisateurs ayant un rôle donné."""
    users = User.objects.filter(role__in=roles, is_active=True)
    for user in users:
        send_notification(
            user=user,
            dossier=dossier,
            titre=titre,
            message=message,
            type=type,
            module=module,
            action_url=action_url,
            meta=meta,
        )
