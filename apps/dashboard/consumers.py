import json
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .services import DashboardService

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        query_string = self.scope['query_string'].decode()
        params = parse_qs(query_string)
        self.dossier_id = params.get('dossier_id', [None])[0]

        if self.dossier_id:
            self.group_name = f'dashboard_updates_{self.dossier_id}'
        else:
            self.group_name = 'dashboard_updates_all'

        # Rejoindre le groupe de diffusion
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

        # Envoyer les données initiales lors de la connexion
        await self.send_dashboard_data()

    async def disconnect(self, close_code):
        # Quitter le groupe
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Réception d'un message du channel layer
    async def dashboard_message(self, event):
        # Quand un signal est déclenché, on renvoie toutes les données rafraîchies
        await self.send_dashboard_data()

    @database_sync_to_async
    def get_data(self):
        return DashboardService.get_dashboard_data(self.dossier_id)

    async def send_dashboard_data(self):
        data = await self.get_data()
        await self.send(text_data=json.dumps({
            'type': 'DASHBOARD_UPDATE',
            'data': data
        }))
