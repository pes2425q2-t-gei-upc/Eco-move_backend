import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import PuntEmergencia
from .serializers import AlertSerializer

class EmergenciaConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Unirse al grupo de emergencias
        await self.channel_layer.group_add(
            "emergencias",
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Abandonar el grupo de emergencias
        await self.channel_layer.group_discard(
            "emergencias",
            self.channel_name
        )

    # Recibir mensaje del WebSocket
    async def receive(self, text_data):
        # Esta función no hace nada en este caso porque no esperamos
        # mensajes del cliente, pero podría implementarse para casos 
        # como confirmación de recepción
        pass

    # Método para enviar actualizaciones de emergencias al cliente
    async def emergencia_update(self, event):
        await self.send(text_data=json.dumps({
            'type': 'emergencia.update',
            'emergencia': event['emergencia']
        }))