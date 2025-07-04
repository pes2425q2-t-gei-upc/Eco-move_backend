from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from api_punts_carrega.models import EstacioCarrega
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class AlertsAPITests(TestCase):
    def setUp(self):
        # Create a test client
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
        self.helper = User.objects.create_user(
            email='helper@example.com',
            username='helperuser',
            password='helperpassword',
            first_name='Helper',
            last_name='User',
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

    def authenticate(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {access_token}'      

    def create_alert(self, user=None):
        return self.client.post(
            reverse('alerts-list'),
            self.data_alert,
            content_type='application/json'
        )
    
    def create_chat_w_alert(self, alert_id):
        return self.client.post(
            reverse('chat-create-alert-chat', kwargs={'pk': alert_id}),
            content_type='application/json'
        )
    
    def create_chat(self, receptor_email):
        return self.client.post(reverse('chat-create-chat'), {
            'receptor_email': receptor_email
        }, content_type='application/json')
        
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
        self.authenticate(self.sender)
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
    
    
    def test_create_direct_chat_between_users(self):
        self.authenticate(self.sender)
        response = self.create_chat(self.receiver.email)
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(response.json().get('alerta'))
    
    
    # Test creating chat from an alert
    def test_creating_chat_from_alert(self):
        # Create a new alert
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        
        chat = self.create_chat_w_alert(alert['id_emergencia'])
        
        # Check if the chat was created successfully
        self.assertEqual(chat.status_code, status.HTTP_201_CREATED)
        
        # Check if the chat data is correct
        chat_data = chat.json()
        self.assertEqual(chat_data['alerta'], alert['id_emergencia'])
        self.assertEqual(chat_data['creador'], self.sender.pk)
    
    
    # Test sending messages in a chat
    def test_sending_message_in_chat(self):
        # The sender logs in, creates an alert, and logs out
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        self.client.logout()
        
        # The receiver logs in and creates a chat (is the helper for the sender)
        self.authenticate(self.receiver)
        chat = self.create_chat_w_alert(alert['id_emergencia']).json()
        
        # The receiver sends the first message
        response_1 = self.send_message(chat['id'], "Hello, I see your alert.")
        self.assertEqual(response_1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_1.json()['content'], "Hello, I see your alert.")
        self.client.logout()
        
        # The sender replies
        self.authenticate(self.sender)
        response_2 = self.send_message(chat['id'], "Thank you for your response.")
        self.assertEqual(response_2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_2.json()['content'], "Thank you for your response.")
        
        # Now retrieve messages
        response_3 = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}))
        self.assertEqual(response_3.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_3.json()['results']), 2)
        
        messages = response_3.json()['results']
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[1]['content'], "Hello, I see your alert.")
        self.assertEqual(messages[0]['content'], "Thank you for your response.")
        
        # Sending direct messages in chat
        chat_2 = self.create_chat(self.receiver.email).json()
        response_4 = self.send_message(chat_2['id'], "Hey! This is a direct message from the sender.")
        self.assertEqual(response_4.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_4.json()['content'], "Hey! This is a direct message from the sender.")
        
        self.client.logout()
        self.authenticate(self.receiver)
        response_5 = self.send_message(chat_2['id'], "Hey! This is direct message from the receiver.")
        self.assertEqual(response_5.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_5.json()['content'], "Hey! This is direct message from the receiver.")        

    
    # Test getting all chats for a user
    def test_getting_multiple_chats(self):
        # Sender 1 logs in and creates an alert
        self.authenticate(self.sender)
        alert1 = self.create_alert().json()
        self.client.logout()

        # Sender 2 logs in and creates another alert
        self.authenticate(self.receiver)
        alert2 = self.create_alert().json()
        self.client.logout()

        # Helper logs in and creates a chat for both alerts
        self.authenticate(self.helper)
        chat1 = self.create_chat_w_alert(alert1['id_emergencia'])
        self.assertEqual(chat1.status_code, status.HTTP_201_CREATED)
        
        chat2 = self.create_chat_w_alert(alert2['id_emergencia'])
        self.assertEqual(chat2.status_code, status.HTTP_201_CREATED)
        
        # Add a direct chat between helper and sender
        direct_chat = self.create_chat(self.sender.email)
        self.assertEqual(direct_chat.status_code, status.HTTP_201_CREATED)

        # Now check that the user has 3 chats (2 from alerts, 1 direct)
        response = self.client.get(reverse('chat-my-chats'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 3)
        
        # Ensure both alerts are in the chats returned
        alert_ids = {chat['alerta'] for chat in response.json()}
        self.assertIn(alert1['id_emergencia'], alert_ids)
        self.assertIn(alert2['id_emergencia'], alert_ids)


    # Test unauthorized access to chat messages
    def test_unauthorized_alert_and_chat_creation(self):
       response = self.create_alert()
       self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    
    # Test get empty chat messages
    def test_get_empty_chat_messages(self):
        self.authenticate(self.sender)
        
        alert = self.create_alert().json()
        
        chat = self.create_chat_w_alert(alert['id_emergencia'])
        self.assertEqual(chat.status_code, status.HTTP_201_CREATED)

        response = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat.json()['id']}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['count'], 0)
        self.assertEqual(response.json()['results'], [])


    # Test sending empty message
    def test_sending_empty_message(self):
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        chat = self.create_chat_w_alert(alert['id_emergencia']).json()

        response = self.send_message(chat['id'], '')
        
        # Check if the message was not sent
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    
    def test_chat_deactivation(self):
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        chat = self.create_chat_w_alert(alert['id_emergencia']).json()
        
        response = self.client.patch(reverse('chat-detail', kwargs={'pk': chat['id']}), {
            'activa': False
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['activa'])

    
    # Test marking messages as read
    def test_marking_messages_as_read(self):
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        chat = self.create_chat_w_alert(alert['id_emergencia']).json()

        message = self.send_message(chat['id'], "Test message.").json()

        # Mark the message as read
        response = self.client.patch(reverse('messages-detail', kwargs={'pk': message['id_missatge']}), {
            'is_read': True
        }, content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['is_read'])
        
        
    def test_prevent_duplicate_direct_chats(self):
        self.authenticate(self.sender)
        data = {'receptor_email': self.receiver.email}
        self.create_chat(data['receptor_email'])
        duplicate = self.create_chat(data['receptor_email'])
        self.assertEqual(duplicate.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_pagination_returns_10_messages(self):
        self.authenticate(self.sender)
        chat = self.create_chat(self.receiver.email).json()

        for i in range(15):
            self.send_message(chat['id'], f"Test message {i}.")

        response = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}), {'page': 1, 'size': 10})
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 10)

    def test_pagination_second_page(self):
        self.authenticate(self.sender)
        alert = self.create_alert().json()
        chat = self.create_chat_w_alert(alert['id_emergencia']).json()

        for i in range(15):
            self.send_message(chat['id'], f"Msg {i}")

        response = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}), {'page': 2})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['results']), 5)
        self.assertEqual(response.json()['results'][0]['content'], "Msg 4")
    
    def test_only_visible_messages_marked_as_read(self):
        self.authenticate(self.sender)
        chat = self.create_chat(self.receiver.email).json()
        for i in range(12):
            self.send_message(chat['id'], f"Unread {i}")
            
        response = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}), {'page': 1})
        self.assertEqual(response.status_code, 200)
        read_status = [msg['is_read'] for msg in response.json()['results']]
        self.assertFalse(all(read_status))
        
        response_2 = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}), {'page': 2})
        self.assertEqual(response_2.status_code, 200)
        read_status_2 = [msg['is_read'] for msg in response_2.json()['results']]
        self.assertFalse(all(read_status_2))
        
        self.client.logout()

        self.authenticate(self.receiver)
        
        response_3 = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}))
        self.assertEqual(response_3.status_code, 200)
        results = response_3.json()['results']
        self.assertEqual(len(results), 10)

        # Check these messages are now marked as read
        read_status_3 = [msg['is_read'] for msg in results]
        self.assertTrue(all(read_status_3))
        
        self.client.logout()
        self.authenticate(self.sender)

        # The next 2 messages should still be unread
        next_page = self.client.get(reverse('chat-get-messages', kwargs={'pk': chat['id']}), {'page': 2})
        self.assertEqual(len(next_page.json()['results']), 2)
        self.assertFalse(any([msg['is_read'] for msg in next_page.json()['results']]))

