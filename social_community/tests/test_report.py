from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model

from social_community.models import Chat, Report, PuntEmergencia
from api_punts_carrega.models import Usuario

User = get_user_model()

class ReportTests(APITestCase):
    def setUp(self):
        self.user1 = Usuario.objects.create_user(email="user1@example.com", password="pass1234", username="user1")
        self.user2 = Usuario.objects.create_user(email="user2@example.com", password="pass1234", username="user2")
        self.admin = Usuario.objects.create_user(email="admin@example.com", password="admin1234", username="admin", is_staff=True)

        self.chat = Chat.objects.create(creador=self.user1, receptor=self.user2)

        self.client.login(username="user1", password="pass1234")  # Corregido: usar username, no email

    def test_create_report_from_chat(self):
        url = reverse('reports-report-from-chat')
        data = {
            "chat_id": self.chat.id,
            "descripcio": "Este usuario me ha insultado."
        }
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Report.objects.count(), 1)
        self.assertEqual(Report.objects.first().receptor, self.user2)

    def test_cannot_create_duplicate_active_report(self):
        Report.objects.create(creador=self.user1, receptor=self.user2, descripcio="Spam")

        url = reverse('reports-report-from-chat')
        data = {
            "chat_id": self.chat.id,
            "descripcio": "Otra queja."
        }

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Ya has reportado a este usuario", response.data['error'])

    def test_user_can_see_own_reports(self):
        Report.objects.create(creador=self.user1, receptor=self.user2, descripcio="Algo")
        url = reverse('reports-my-reports')

        self.client.force_authenticate(user=self.user1)

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_blocked_user_cannot_create_chat(self):
        self.user1.bloqueado = True
        self.user1.save()
        self.client.force_authenticate(user=self.user1)

        self.alert = PuntEmergencia.objects.create(
            lat=41.3879,        
            lng=2.16992,      
            is_active=True,
            sender=self.user2,
            titol = 'Alerta test',
            descripcio = 'Descripción de prueba',

        )

        url = reverse('chat-create-alert-chat', kwargs={'pk': self.alert.id_emergencia})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Usuario bloqueado', response.data.get('error', ''))



    def test_blocked_user_cannot_create_alert(self):
        self.user1.bloqueado = True
        self.user1.is_active = True
        self.user1.save()

        self.client.force_authenticate(user=self.user1)

        data = {
            'lat': 41.38,
            'lng': 2.17,
            'titol': 'Alerta test',
            'descripcio': 'Descripción de prueba',
        }
        
        url = reverse('alerts-list')  # cambia por tu nombre real
        response = self.client.post(url, data)
        
        print('Status:', response.status_code)
        print('Response:', response.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Usuario bloqueado', str(response.data))
    
    def test_blocked_user_cannot_poll_alerts(self):
        self.user1.bloqueado = True
        self.user1.save()
        self.client.force_authenticate(user=self.user1)

        url = reverse('alerts-polling-alertes')  # Cambia este nombre por el correcto si es distinto
        params = {'lat': 41.38, 'lng': 2.17}
        
        response = self.client.get(url, params)
        
        print('Status:', response.status_code)
        print('Response:', response.data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Usuario bloqueado', response.data.get('error', ''))

