import json
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer
from django.test import TestCase, Client
from django.urls import reverse, path
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from asgiref.sync import sync_to_async
from unittest.mock import patch, MagicMock

from social_community.models import PuntEmergencia
from social_community.consumers import EmergenciaConsumer

User = get_user_model()

class EmergenciaWebSocketTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        self.sender = User.objects.create_user(
            email='sender@example.com',
            username='senderuser',
            password='senderpassword',
            first_name='Sender',
            last_name='User',
        )
        self.receiver = User.objects.create_user(
            email='receiver@example.com',
            username='receiveruser',
            password='receiverpassword',
            first_name='Receiver',
            last_name='User',
        )
        
        self.sender_password = 'senderpassword'
        self.receiver_password = 'receiverpassword'
        
        self.data_alert = {
            'titol': 'Test Alert',
            'descripcio': 'This is a test alert.',
            'lat': 41.123456,
            'lng': 2.123456,
            'is_active': True,
        }
        
        self.application = AuthMiddlewareStack(
            URLRouter([
                path('ws/emergencias/', EmergenciaConsumer.as_asgi()),
            ])
        )

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'      

    def create_alert(self):
        return self.client.post(
            reverse('alerts-list'),
            self.data_alert,
            content_type='application/json'
        )
    
    async def test_websocket_connection(self):
        communicator = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected, _ = await communicator.connect()
        
        self.assertTrue(connected)
        
        await communicator.disconnect()
    
    async def test_alert_creation_websocket_message(self):
        communicator = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        await sync_to_async(self.authenticate)(self.sender)
        

        alert = await sync_to_async(PuntEmergencia.objects.create)(
            sender=self.sender,
            titol=self.data_alert['titol'],
            descripcio=self.data_alert['descripcio'],
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=self.data_alert['is_active']
        )
        
        channel_layer = get_channel_layer()
        await channel_layer.group_send(
            "emergencias",
            {
                "type": "emergencia_update",
                "emergencia": {
                    "id_emergencia": alert.id_emergencia,
                    "sender": self.sender.id,
                    "titol": alert.titol,
                    "descripcio": alert.descripcio,
                    "lat": alert.lat,
                    "lng": alert.lng,
                    "is_active": alert.is_active,
                    "timestamp": alert.timestamp.isoformat()
                }
            }
        )
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'emergencia.update')
        self.assertEqual(response['emergencia']['titol'], self.data_alert['titol'])
        
        await communicator.disconnect()
    
    async def test_multiple_clients_receive_alert(self):
        communicator1 = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected1, _ = await communicator1.connect()
        self.assertTrue(connected1)
        
        communicator2 = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected2, _ = await communicator2.connect()
        self.assertTrue(connected2)
        
        punt = await sync_to_async(PuntEmergencia.objects.create)(
            sender=self.sender,
            titol=self.data_alert['titol'],
            descripcio=self.data_alert['descripcio'],
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=self.data_alert['is_active']
        )
        
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            "emergencias",
            {
                "type": "emergencia_update",
                "emergencia": {
                    "id_emergencia": punt.id_emergencia,
                    "sender": self.sender.id,
                    "titol": punt.titol,
                    "descripcio": punt.descripcio,
                    "lat": punt.lat,
                    "lng": punt.lng,
                    "is_active": punt.is_active
                }
            }
        )
        
        response1 = await communicator1.receive_json_from()
        self.assertEqual(response1['type'], 'emergencia.update')
        self.assertEqual(response1['emergencia']['titol'], self.data_alert['titol'])
        
        response2 = await communicator2.receive_json_from()
        self.assertEqual(response2['type'], 'emergencia.update')
        self.assertEqual(response2['emergencia']['titol'], self.data_alert['titol'])
        
        await communicator1.disconnect()
        await communicator2.disconnect()
    
    async def test_client_disconnection(self):

        communicator = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        await communicator.disconnect()
        
        try:
            await communicator.send_json_to({"message": "test"})
            self.fail("Should have raised an exception")
        except Exception:
            pass 
    
    async def test_emergency_update_sends_correct_format(self):
        communicator = WebsocketCommunicator(self.application, "ws/emergencias/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)
        
        test_data = {
            "id_emergencia": 1,
            "titol": "Test Emergency",
            "descripcio": "Emergency description",
            "lat": 41.123,
            "lng": 2.123,
            "is_active": True
        }
        
        channel_layer = get_channel_layer()
        
        await channel_layer.group_send(
            "emergencias",
            {
                "type": "emergencia_update",
                "emergencia": test_data
            }
        )
        
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'emergencia.update')
        self.assertEqual(response['emergencia'], test_data)
        
        await communicator.disconnect()
