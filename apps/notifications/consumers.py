import json
from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser

from .models import Notification

User = get_user_model()


@database_sync_to_async
def get_user_from_token(token_key: str):
    try:
        UntypedToken(token_key)
        from rest_framework_simplejwt.backends import TokenBackend
        from django.conf import settings
        data = TokenBackend(
            algorithm=settings.SIMPLE_JWT.get('ALGORITHM', 'HS256'),
            signing_key=settings.SECRET_KEY,
        ).decode(token_key, verify=True)
        user = User.objects.get(id=data['user_id'])
        return user
    except (InvalidToken, TokenError, User.DoesNotExist, Exception):
        return AnonymousUser()


@database_sync_to_async
def get_recent_notifications(user):
    qs = Notification.objects.filter(
        user=user, lu=False
    ).order_by('-cree_le')[:30]
    return [
        {
            'id': str(n.id),
            'titre': n.titre,
            'message': n.message,
            'type': n.type,
            'module': n.module,
            'action_url': n.action_url,
            'lu': n.lu,
            'cree_le': n.cree_le.isoformat(),
            'meta': n.meta,
        }
        for n in qs
    ]


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Authentification JWT via query string
        qs = parse_qs(self.scope['query_string'].decode())
        token = qs.get('token', [None])[0]

        if not token:
            await self.close(code=4001)
            return

        self.user = await get_user_from_token(token)

        if not self.user or not self.user.is_authenticated:
            await self.close(code=4001)
            return

        # Canal personnel
        self.user_group = f'notifications_user_{self.user.id}'
        # Canal broadcast (tous les users connectés)
        self.broadcast_group = 'notifications_broadcast'

        await self.channel_layer.group_add(self.user_group, self.channel_name)
        await self.channel_layer.group_add(self.broadcast_group, self.channel_name)

        await self.accept()

        # Envoyer l'historique des notifications non lues à la connexion
        history = await get_recent_notifications(self.user)
        await self.send(text_data=json.dumps({
            'type': 'NOTIFICATION_HISTORY',
            'notifications': history,
        }))

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(self.user_group, self.channel_name)
        if hasattr(self, 'broadcast_group'):
            await self.channel_layer.group_discard(self.broadcast_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Traiter les messages entrants du client (mark as read, etc.)"""
        try:
            data = json.loads(text_data or '{}')
            action = data.get('action')

            if action == 'mark_read':
                notif_id = data.get('id')
                if notif_id:
                    await self._mark_read(notif_id)
                    await self.send(text_data=json.dumps({
                        'type': 'NOTIFICATION_READ',
                        'id': notif_id,
                    }))
            elif action == 'mark_all_read':
                count = await self._mark_all_read()
                await self.send(text_data=json.dumps({
                    'type': 'NOTIFICATIONS_ALL_READ',
                    'count': count,
                }))
        except Exception:
            pass

    @database_sync_to_async
    def _mark_read(self, notif_id: str):
        Notification.objects.filter(id=notif_id, user=self.user).update(lu=True)

    @database_sync_to_async
    def _mark_all_read(self) -> int:
        return Notification.objects.filter(user=self.user, lu=False).update(lu=True)

    # Handler appelé par channel_layer.group_send
    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'NEW_NOTIFICATION',
            'notification': event['notification'],
        }))
