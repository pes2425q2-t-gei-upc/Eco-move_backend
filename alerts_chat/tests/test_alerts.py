from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from datetime import datetime
from api_punts_carrega.models import EstacioCarrega
from alerts_chat.models import Missatge, PuntEmergencia, Chat

User = get_user_model()

class AlertsAPITests(TestCase):
    def setUp(self):
        # Create a test client
        self.client = Client()
        
        self.sender = User.objects.create_user(
            email='sender@example.com',
            username='senderuser',
            password='senderpassword',
            dni='12345678A',
        )
        self.receiver = User.objects.create_user(
            email='receiver@example.com',
            username='receiveruser',
            password='receiverpassword',
            dni='87654321B',
        )
        self.helper = User.objects.create_user(
            email='helper@example.com',
            username='helperuser',
            password='helperpassword',
            dni='11223344C',
        )
        self.sender_password = 'senderpassword'
        self.receiver_password = 'receiverpassword'
        self.helper_password = 'helperpassword'
        
        # Create a test station
        self.estacio = EstacioCarrega.objects.create(
            id_punt="12345",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Barcelona, 123",
            ciutat="Barcelona",
            provincia="Barcelona",
            gestio="Public",
            tipus_acces="targeta",
            nplaces="2",
        )
        
        self.data_alert = {
            'titol': 'Test Alert',
            'descripcio': 'This is a test alert.',
            'lat': 41.123456,
            'lng': 2.123456,
            'is_active': True,
        }
        
    def create_alert(self, user=None):
        return self.client.post(
            reverse('alerts-list'),
            self.data_alert,
            content_type='application/json'
        )
    
    def create_chat(self, alert_id):
        return self.client.post(
            reverse('chat-create-chat', kwargs={'pk': alert_id}),
            content_type='application/json'
        )
        
    def send_message(self, chat_id, content):
        return self.client.post(
            reverse('messages-list'),
            {
                'chat': chat_id,
                'content': content,
            },
            content_type='application/json'
        )
    
    
    # Test creating a new alert
    def test_creating_alert(self):
        response = self.client.login(email=self.sender.email, password=self.sender_password)
        self.assertTrue(response, "Login failed")
        alert = self.create_alert()
        
        # Check if the alert was created successfully
        self.assertEqual(alert.status_code, status.HTTP_201_CREATED)
        
        # Check if the alert data is correct
        alert_data = alert.json()
        self.assertEqual(alert_data['titol'], self.data_alert['titol'])
        self.assertEqual(alert_data['descripcio'], self.data_alert['descripcio'])
        self.assertEqual(alert_data['lat'], self.data_alert['lat'])
        self.assertEqual(alert_data['lng'], self.data_alert['lng'])
        self.assertTrue(alert_data['is_active'])
    
    
    # Test creating chat from an alert
    def test_creating_chat(self):
        # Create a new alert
        self.client.login(email=self.sender.email, password=self.sender_password)
        alert = self.create_alert().json()
        
        chat = self.create_chat(alert['id_emergencia'])
        
        # Check if the chat was created successfully
        self.assertEqual(chat.status_code, status.HTTP_201_CREATED)
        
        # Check if the chat data is correct
        chat_data = chat.json()
        self.assertEqual(chat_data['alerta'], alert['id_emergencia'])
        self.assertEqual(chat_data['creador'], self.sender.pk)
    
    
    # Test sending messages in a chat
    def test_sending_message_in_chat(self):
        # The sender logs in, creates an alert, and logs out
        self.client.login(email=self.sender.email, password=self.sender_password)
        alert = self.create_alert().json()
        self.client.logout()
        
        # The receiver logs in and creates a chat (is the helper for the sender)
        self.client.login(email=self.receiver.email, password=self.receiver_password)
        chat = self.create_chat(alert['id_emergencia']).json()
        
        # The receiver sends the first message
        response = self.send_message(chat['id'], "Hello, I see your alert.")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.json()['content'], "Hello, I see your alert.")
        self.client.logout()
        
        # The sender replies
        self.client.login(email=self.sender.email, password=self.sender_password)
        response_2 = self.send_message(chat['id'], "Thank you for your response.")
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_2.json()['content'], "Thank you for your response.")
        
        # Now retrieve messages
        response_3 = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}))
        self.assertEqual(response_3.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_3.json()), 2)
        
        self.assertEqual(response_3.json()[0]['content'], "Hello, I see your alert.")
        self.assertEqual(response_3.json()[1]['content'], "Thank you for your response.")

    
    # Test getting all chats for a user
    def test_getting_multiple_chats_for_user(self):
        # Sender 1 logs in and creates an alert
        self.client.login(email=self.sender.email, password=self.sender_password)
        alert1 = self.create_alert().json()
        self.client.logout()

        # Sender 2 logs in and creates another alert
        self.client.login(email=self.receiver.email, password=self.receiver_password)
        alert2 = self.create_alert().json()
        self.client.logout()

        # Helper logs in and creates a chat for both alerts
        self.client.login(email=self.helper.email, password=self.helper_password)
        chat1 = self.create_chat(alert1['id_emergencia'])
        self.assertEqual(chat1.status_code, status.HTTP_201_CREATED)
        
        chat2 = self.create_chat(alert2['id_emergencia'])
        self.assertEqual(chat2.status_code, status.HTTP_201_CREATED)

        # Get all chats for the helper
        response = self.client.get(reverse('chat-my-chats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        chats = response.json()
        self.assertEqual(len(chats), 2)

        # Ensure both alerts are in the chats returned
        alert_ids = {chat['alerta'] for chat in chats}
        self.assertIn(alert1['id_emergencia'], alert_ids)
        self.assertIn(alert2['id_emergencia'], alert_ids)


    # Test unauthorized access to chat messages
    def test_unauthorized_alert_creation(self):
        response = self.create_alert()
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    
    # Test get empty chat messages
    def test_get_empty_chat_messages(self):
        self.client.login(username=self.sender.email, password=self.sender_password)
        
        alert = self.create_alert().json()
        
        chat = self.create_chat(alert['id_emergencia'])
        self.assertEqual(chat.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat.json()['id']}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])


    # Test sending empty message
    def test_sending_empty_message(self):
        self.client.login(username=self.sender.email, password=self.sender_password)
        alert = self.create_alert().json()
        chat = self.create_chat(alert['id_emergencia']).json()

        response = self.send_message(chat['id'], '')
        
        # Check if the message was not sent
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    
    # Test chat is deactivated
    def test_chat_deactivation(self):
        self.client.login(email=self.sender.email, password=self.sender_password)
        alert = self.create_alert().json()
        chat = self.create_chat(alert['id_emergencia']).json()
        
        response = self.client.patch(reverse('chat-detail', kwargs={'pk': chat['id']}), {
            'activa': False
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['activa'])

    
    # Test marking messages as read
    def test_marking_messages_as_read(self):
        self.client.login(email=self.sender.email, password=self.sender_password)
        alert = self.create_alert().json()
        chat = self.create_chat(alert['id_emergencia']).json()

        message = self.send_message(chat['id'], "Test message.").json()

        # Mark the message as read
        response = self.client.patch(reverse('messages-detail', kwargs={'pk': message['id_missatge']}), {
            'is_read': True
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_read'])
    