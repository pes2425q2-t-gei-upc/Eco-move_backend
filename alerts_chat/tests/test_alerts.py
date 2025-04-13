from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
import json
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva
from django.contrib.auth.models import User

class AlertsAPITests(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        # Create a test users
        # Create sender and receiver users
        self.sender = User.objects.create_user(
            username='senderuser',
            password='senderpassword'
        )
        self.receiver = User.objects.create_user(
            username='receiveruser',
            password='receiverpassword'
        )
        
        # Create a test station
        self.estacio = EstacioCarrega.objects.create(
            nom='Test Station',
            adreca='123 Test St',
            latitud=41.123456,
            longitud=2.123456,
            potencia_maxima=50.0,
            tipus_connector='Type 2'
        )
    
    
    # Test creating a new alert
    def test_creating_alert(self):
        url = reverse('alerts-list')
        data = {
            'titol': 'Test Alert',
            'descripcio': 'This is a test alert.',
            'latitud': 41.123456,
            'longitud': 2.123456,
            'is_active': True,
            'sender': self.sender.pk
        }
        
        self.client.login(username='senderuser', password='senderpassword')
        
        response = self.client.post(url, data, format='json')
        
        # Check if the alert was created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if the alert data is correct
        alert_data = response.json()
        self.assertEqual(alert_data['titol'], data['titol'])
        self.assertEqual(alert_data['descripcio'], data['descripcio'])
        self.assertEqual(alert_data['latitud'], data['latitud'])
        self.assertEqual(alert_data['longitud'], data['longitud'])
        self.assertTrue(alert_data['is_active'])
    
    
    # Test creating chat from an alert
    def test_creating_chat(self):
        url = reverse('alerts-create_chat', kwargs={'pk': self.estacio.pk})
        
        # Create a new alert
        self.client.login(username='senderuser', password='senderpassword')
        alert_response = self.client.post(reverse('alerts-list'), {
            'titol': 'Test Alert',
            'descripcio': 'This is a test alert.',
            'latitud': 41.123456,
            'longitud': 2.123456,
            'is_active': True,
            'sender': self.sender.pk
        }, format='json')
        
        alert_data = alert_response.json()
        
        response = self.client.post(url, {'alert_id': alert_data['id']}, format='json')
        
        # Check if the chat was created successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if the chat data is correct
        chat_data = response.json()
        self.assertEqual(chat_data['alerta'], alert_data['id'])
        self.assertEqual(chat_data['creador'], self.sender.pk)
    
    # Test sending messages in a chat
    def test_sending_message_in_chat(self):

        self.client.login(username='senderuser', password='senderpassword')
        alert_response = self.client.post(reverse('alerts-list'), {
            'titol': 'Test Alert',
            'descripcio': 'This is a test alert.',
            'latitud': 41.123456,
            'longitud': 2.123456,
            'is_active': True,
            'sender': self.sender.pk
        }, format='json')
        
        alert_data = alert_response.json()
        
        chat_response = self.client.post(reverse('alerts-create_chat', kwargs={'pk': alert_data['id']}), {
            'alert_id': alert_data['id']
        }, format='json')
        
        chat_data = chat_response.json()
        
        url = reverse('messages-list')
        data = {
            'missatge': 'Hello, this is a test message.',
            'chat': chat_data['id'],
            'sender': self.sender.pk
        }
        
        response = self.client.post(url, data, format='json')
        
        # Check if the message was sent successfully
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check if the message data is correct
        message_data = response.json()
        self.assertEqual(message_data['missatge'], data['missatge'])
        
        data_2 = {
            'missatge': 'Hello, I am responding to you message.',
            'chat': chat_data['id'],
            'receiver': self.receiver.pk
        }
        response_2 = self.client.post(url, data, format='json')
        
        # Check if the message was sent successfully
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        
        # Check if the message data is correct
        message_data_2 = response_2.json()
        self.assertEqual(message_data_2['missatge'], data['missatge'])
    
    # Test getting messages from a chat
    
    # Test getting all chats for a user
    
        
        
        
    def test_modificar_reserva(self):
        print()
        
    def test_eliminar_reserva(self):
        url = self.reserva_url + f"{self.reserva.pk}/eliminar/"
