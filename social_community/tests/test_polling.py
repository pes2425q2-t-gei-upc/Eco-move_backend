import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import time
from datetime import timedelta

from social_community.models import PuntEmergencia

User = get_user_model()

class EmergenciaPollingTests(TestCase):
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
        
        # Coordenadas para probar el ordenamiento por distancia
        self.test_locations = [
            {'lat': 41.123456, 'lng': 2.123456},  # ubicación del alerta
            {'lat': 41.123458, 'lng': 2.123458},  # muy cerca
            {'lat': 41.130000, 'lng': 2.130000},  # más lejos
            {'lat': 42.000000, 'lng': 3.000000},  # muy lejos
        ]

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
    
    def test_poll_requires_coordinates(self):
        """Test que el endpoint de polling requiere coordenadas"""
        self.authenticate(self.receiver)
        
        # Intentar polling sin coordenadas
        response = self.client.get(reverse('alerts-poll'))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Intentar con lat pero sin lng
        response = self.client.get(f"{reverse('alerts-poll')}?lat=41.123456")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Intentar con lng pero sin lat
        response = self.client.get(f"{reverse('alerts-poll')}?lng=2.123456")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_poll_invalid_coordinates(self):
        """Test que el endpoint de polling valida las coordenadas"""
        self.authenticate(self.receiver)
        
        # Intentar polling con coordenadas inválidas
        response = self.client.get(f"{reverse('alerts-poll')}?lat=abc&lng=2.123456")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        response = self.client.get(f"{reverse('alerts-poll')}?lat=41.123456&lng=xyz")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_poll_returns_active_alerts(self):
        """Test que el polling devuelve alertas activas"""
        self.authenticate(self.sender)
        
        # Crear una alerta
        alert = PuntEmergencia.objects.create(
            sender=self.sender,
            titol=self.data_alert['titol'],
            descripcio=self.data_alert['descripcio'],
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=True
        )
        
        # Polling cerca de la ubicación de la alerta
        self.authenticate(self.receiver)
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat={self.test_locations[0]['lat']}&lng={self.test_locations[0]['lng']}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('alerts', response.json())
        self.assertIn('timestamp', response.json())
        self.assertEqual(len(response.json()['alerts']), 1)
        self.assertEqual(response.json()['alerts'][0]['id_emergencia'], alert.id_emergencia)
    
    def test_poll_filters_inactive_alerts(self):
        """Test que el polling filtra alertas inactivas por defecto"""
        self.authenticate(self.sender)
        
        # Crear una alerta activa
        active_alert = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Activa",
            descripcio="Esta alerta está activa",
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=True
        )
        
        # Crear una alerta inactiva
        inactive_alert = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Inactiva",
            descripcio="Esta alerta está inactiva",
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=False
        )
        
        # Hacer polling con active_only=true (por defecto)
        self.authenticate(self.receiver)
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat={self.test_locations[0]['lat']}&lng={self.test_locations[0]['lng']}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.json()['alerts']
        # Debería retornar solo la alerta activa
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['id_emergencia'], active_alert.id_emergencia)
        
        # Hacer polling con active_only=false
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat={self.test_locations[0]['lat']}&lng={self.test_locations[0]['lng']}&active_only=false"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.json()['alerts']
        # Debería retornar ambas alertas
        self.assertEqual(len(alerts), 2)
    
    def test_poll_sorts_by_distance(self):
        """Test que el polling ordena alertas por distancia"""
        self.authenticate(self.sender)
        
        # Crear alertas en distintas ubicaciones
        alert1 = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Cercana",
            descripcio="Esta alerta está cerca",
            lat=41.123458,  # muy cerca del punto de consulta
            lng=2.123458,
            is_active=True
        )
        
        alert2 = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Media",
            descripcio="Esta alerta está a media distancia",
            lat=41.130000,  # más lejos
            lng=2.130000,
            is_active=True
        )
        
        alert3 = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Lejana",
            descripcio="Esta alerta está lejos",
            lat=42.000000,  # muy lejos
            lng=3.000000,
            is_active=True
        )
        
        # Hacer polling desde un punto específico
        self.authenticate(self.receiver)
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat=41.123456&lng=2.123456"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.json()['alerts']
        
        # Las alertas deberían estar ordenadas por cercanía
        self.assertEqual(len(alerts), 3)
        self.assertEqual(alerts[0]['id_emergencia'], alert1.id_emergencia)  # la más cercana
        self.assertEqual(alerts[1]['id_emergencia'], alert2.id_emergencia)  # la de media distancia
        self.assertEqual(alerts[2]['id_emergencia'], alert3.id_emergencia)  # la más lejana
    
    def test_poll_since_timestamp(self):
        """Test que el polling filtra alertas por timestamp"""
        self.authenticate(self.sender)
        
        # Crear una alerta antigua
        old_alert = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Antigua",
            descripcio="Esta es una alerta antigua",
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=True
        )
        
        # Capturar el timestamp actual
        current_time = timezone.now()
        timestamp_str = current_time.timestamp()
        
        # Esperar un momento para asegurar que el timestamp sea diferente
        time.sleep(1)
        
        # Crear una alerta nueva
        new_alert = PuntEmergencia.objects.create(
            sender=self.sender,
            titol="Alerta Nueva",
            descripcio="Esta es una alerta nueva",
            lat=self.data_alert['lat'],
            lng=self.data_alert['lng'],
            is_active=True
        )
        
        # Hacer polling con el parámetro since
        self.authenticate(self.receiver)
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat={self.test_locations[0]['lat']}&lng={self.test_locations[0]['lng']}&since={timestamp_str}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        alerts = response.json()['alerts']
        
        # Debería retornar solo la alerta nueva
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['id_emergencia'], new_alert.id_emergencia)
    
    def test_poll_invalid_timestamp(self):
        """Test que el polling maneja timestamps inválidos"""
        self.authenticate(self.receiver)
        
        # Intentar polling con timestamp inválido
        response = self.client.get(
            f"{reverse('alerts-poll')}?lat={self.test_locations[0]['lat']}&lng={self.test_locations[0]['lng']}&since=invalid_timestamp"
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)