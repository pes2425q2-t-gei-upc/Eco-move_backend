from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class UsuarioCRUDTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            idioma='Català',
            telefon='123456789',
            descripcio='Test user description'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.auth_header = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}
        self.base_url = '/api_punts_carrega/usuari/'

    def test_get_user_list_authenticated(self):
        response = self.client.get(self.base_url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.json()), 1)

    def test_get_user_detail(self):
        url = f"{self.base_url}{self.user.id}/"
        response = self.client.get(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.user.email)

    def test_update_user_partial(self):
        url = f"{self.base_url}{self.user.id}/"
        new_data = {"idioma": "Castellano"}
        response = self.client.patch(url, new_data, format='json', **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['idioma'], "Castellano")

    def test_delete_user(self):
        url = f"{self.base_url}{self.user.id}/"
        response = self.client.delete(url, **self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(User.objects.filter(pk=self.user.id).exists())

    def test_unauthorized_access(self):
        response = self.client.get(self.base_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
    def test_update_language(self):
        url = f"{self.base_url}{self.user.id}/update-language/"
        new_data = {"idioma": "English"}
        response = self.client.put(url, new_data, format='json', **self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('Language'), "English")
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.idioma, "English")
    
    def test_update_language_unauthenticated(self):
        url = f"{self.base_url}{self.user.id}/update-language/"
        new_data = {"idioma": "English"}
        response = self.client.put(url, new_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_language_invalid_value(self):
        url = f"{self.base_url}{self.user.id}/update-language/"
        new_data = {"idioma": "InvalidLanguage"}
        response = self.client.put(url, new_data, format='json', **self.auth_header)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    