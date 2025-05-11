from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api_punts_carrega.models import Vehicle, Usuario, TipusCarregador
from rest_framework.authtoken.models import Token

class TestVehicle(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = Usuario.objects.create_user(username='test_vehicle_user', email='test_vehicle@example.com', password='password123')
        self.token = Token.objects.create(user=self.user)
        self.auth_header = f'Token {self.token.key}'

        self.tipus_carregador = TipusCarregador.objects.create(
            id_carregador="tipus_test_vehicle",
            nom_tipus="Carregador Test Vehicle",
            tipus_connector="Connector Test",
            tipus_corrent="Corrent alterna"
        )

        self.vehicle = Vehicle.objects.create(
            matricula="TEST001",
            carrega_actual=60.0,
            capacitat_bateria=80.0,
            propietari=self.user,
            model="Model Test",
            marca="Marca Test",
            any_model=2023
        )
        self.vehicle.tipus_carregador.add(self.tipus_carregador)

        self.vehicle_url = reverse('vehicle-detail', args=[self.vehicle.matricula])
        self.vehicles_url = reverse('vehicle-list')

    def test_obtenir_vehicle(self):
        response = self.client.get(self.vehicle_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['matricula'], self.vehicle.matricula)
        self.assertEqual(response.data['model'], self.vehicle.model)
        self.assertEqual(response.data['marca'], self.vehicle.marca)
        self.assertEqual(response.data['any_model'], self.vehicle.any_model)
        self.assertEqual(float(response.data['carrega_actual']), self.vehicle.carrega_actual)
        self.assertEqual(float(response.data['capacitat_bateria']), self.vehicle.capacitat_bateria)

    def test_llistar_vehicles(self):
        response = self.client.get(self.vehicles_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_crear_vehicle(self):
        data = {
            'matricula': 'TEST002',
            'carrega_actual': 70.0,
            'capacitat_bateria': 90.0,
            'model': 'Model Nou',
            'marca': 'Marca Nova',
            'any_model': 2024,
            'tipus_carregador': [self.tipus_carregador.id_carregador]
        }
        response = self.client.post(self.vehicles_url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 2)
        self.assertEqual(Vehicle.objects.get(matricula='TEST002').model, 'Model Nou')

    def test_actualitzar_vehicle(self):
        data = {
            'carrega_actual': 75.0,
            'model': 'Model Actualitzat'
        }
        response = self.client.patch(self.vehicle_url, data, format='json', HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.carrega_actual, 75.0)
        self.assertEqual(self.vehicle.model, 'Model Actualitzat')

    def test_eliminar_vehicle(self):
        response = self.client.delete(self.vehicle_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Vehicle.objects.count(), 0)

    def test_vehicle_propietari(self):
        self.assertEqual(self.vehicle.propietari, self.user)
        self.assertEqual(self.user.vehicles.count(), 1)
        self.assertEqual(self.user.vehicles.first(), self.vehicle)

    def test_vehicle_tipus_carregador(self):
        self.assertEqual(self.vehicle.tipus_carregador.count(), 1)
        self.assertEqual(self.vehicle.tipus_carregador.first(), self.tipus_carregador)
        self.assertEqual(self.tipus_carregador.tipus_carregador.count(), 1)
        self.assertEqual(self.tipus_carregador.tipus_carregador.first(), self.vehicle)

    def test_vehicle_sense_autenticar(self):
        response = self.client.get(self.vehicles_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_vehicle_altre_usuari(self):
        other_user = Usuario.objects.create_user(username='other_vehicle_user', email='other_vehicle@example.com', password='password456')
        other_token = Token.objects.create(user=other_user)
        other_auth_header = f'Token {other_token.key}'
        response = self.client.get(self.vehicle_url, HTTP_AUTHORIZATION=other_auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
