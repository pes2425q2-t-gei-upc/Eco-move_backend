from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthUsuarioTests(APITestCase):
    def setUp(self):
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.refresh_url = reverse('token_refresh')
        self.me_url = reverse('me')

        self.user_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "testpass123",
            "password2": "testpass123"
        }

    def test_user_registration(self):
        response = self.client.post(self.register_url, self.user_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email="testuser@example.com").exists())

    def test_login_with_valid_credentials(self):
        User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"]
        )
        response = self.client.post(self.login_url, {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_access_me_with_token(self):
        User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"]
        )
        login = self.client.post(self.login_url, {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        })
        token = login.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user_data['email'])

    def test_token_refresh(self):
        User.objects.create_user(
            username=self.user_data["username"],
            email=self.user_data["email"],
            password=self.user_data["password"]
        )
        login = self.client.post(self.login_url, {
            "email": self.user_data['email'],
            "password": self.user_data['password']
        })
        refresh_token = login.data['refresh']
        response = self.client.post(self.refresh_url, {
            "refresh": refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
