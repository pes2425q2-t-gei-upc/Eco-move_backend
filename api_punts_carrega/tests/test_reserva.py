from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva, Usuario, Vehicle, ModelCotxe, TipusCarregador
from rest_framework.authtoken.models import Token

class ReservaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = Usuario.objects.create_user(username='test_reserva_user', email='test_reserva@example.com', password='password123')
        self.other_user = Usuario.objects.create_user(username='other_reserva_user', email='other_reserva@example.com', password='password456')

        self.token = Token.objects.create(user=self.test_user)
        self.auth_header = f'Token {self.token.key}'

        self.common_charger_type = TipusCarregador.objects.create(id_carregador="TEST-CCS-S", nom_tipus="CCS Setup", tipus_connector="CCS2", tipus_corrent="DC")
        self.test_model_coche = ModelCotxe.objects.create(marca="TestMarcaS", model="TestModelS", any_model=2024)
        self.test_model_coche.tipus_carregador.add(self.common_charger_type)

        self.test_vehicle = Vehicle.objects.create(
            matricula="TESTVEH", propietari=self.test_user, model_cotxe=self.test_model_coche,
            carrega_actual=50.0, capacitat_bateria=70.0
        )

        self.estacio = EstacioCarrega.objects.create(
            id_punt="TEST-EST-SETUP", lat=41.3, lng=2.1, nplaces="1", gestio="TestG", tipus_acces="TestA"
        )
        self.estacio.tipus_carregador.add(self.common_charger_type)

        self.reserva = Reserva.objects.create(
            usuario=self.test_user, estacion=self.estacio, fecha=date(2025, 3, 19),
            hora=time(10, 0), duracion=timedelta(hours=2), vehicle=self.test_vehicle
        )

        self.reserva_data_crear = {
            "estacion": self.estacio.id_punt,
            "fecha": "20/03/2025",
            "hora": "14:00",
            "duracion": "03:00:00",
            "vehicle": self.test_vehicle.matricula
        }

        self.list_url = reverse('reserva-list')
        self.detail_url = reverse('reserva-detail', kwargs={'pk': self.reserva.pk})
        self.crear_url = reverse('reserva-crear')
        self.modificar_url = reverse('reserva-modificar', kwargs={'pk': self.reserva.pk})
        self.eliminar_url = reverse('reserva-eliminar', kwargs={'pk': self.reserva.pk})

    def test_get_all_reservations_authenticated(self):
        response = self.client.get(self.list_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.reserva.id)

    def test_get_all_reservations_unauthenticated(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_get_reservation_by_id_owner(self):
        response = self.client.get(self.detail_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estacion"], self.estacio.id_punt)

    def test_get_reservation_by_id_other_user(self):
        other_token = Token.objects.create(user=self.other_user)
        other_auth_header = f'Token {other_token.key}'
        response = self.client.get(self.detail_url, HTTP_AUTHORIZATION=other_auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_crear_reserva(self):
        response = self.client.post(
            self.crear_url,
            data=json.dumps(self.reserva_data_crear),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        nueva_reserva = Reserva.objects.exclude(pk=self.reserva.pk).first()
        self.assertEqual(nueva_reserva.usuario, self.test_user)

    def test_crear_reserva_unauthenticated(self):
        response = self.client.post(
            self.crear_url,
            data=json.dumps(self.reserva_data_crear),
            content_type='application/json'
        )
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_modificar_reserva(self):
        modificar_data = {
            "fecha": "20/03/2025",
            "hora": "11:00",
            "duracion": "04:00:00"
        }
        response = self.client.put(
            self.modificar_url,
            data=json.dumps(modificar_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.content)

    def test_modificar_reserva_otro_usuario_falla(self):
        modificar_data = {"hora": "12:00"}
        other_token = Token.objects.create(user=self.other_user)
        other_auth_header = f'Token {other_token.key}'
        response = self.client.put(
            self.modificar_url,
            data=json.dumps(modificar_data),
            content_type='application/json',
            HTTP_AUTHORIZATION=other_auth_header
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.hora, time(10, 0))

    def test_eliminar_reserva(self):
        response = self.client.delete(self.eliminar_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reserva.objects.count(), 0)

    def test_eliminar_reserva_otro_usuario_falla(self):
        other_token = Token.objects.create(user=self.other_user)
        other_auth_header = f'Token {other_token.key}'
        response = self.client.delete(self.eliminar_url, HTTP_AUTHORIZATION=other_auth_header)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(Reserva.objects.count(), 1)
