from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class BicingForceEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="12345678")
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_forzar_importar(self):
        response = self.client.post("/api/bicing/estaciones/forzar-importar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

    def test_forzar_actualizar(self):
        response = self.client.post("/api/bicing/estaciones/forzar-actualizar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("message", response.data)

