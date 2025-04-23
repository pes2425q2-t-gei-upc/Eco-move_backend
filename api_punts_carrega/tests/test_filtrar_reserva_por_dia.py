from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva, Usuario, Vehicle, ModelCotxe, TipusCarregador

class ReservaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.test_user = Usuario.objects.create_user(
            username='test_reserva_user', email='test_reserva@example.com',
            password='password123'
        )
        self.test_model_coche = ModelCotxe.objects.create(marca="TMarca", model="TModel", any_model=2024)
        self.test_vehicle = Vehicle.objects.create(
            matricula="TESTVEH", propietari=self.test_user, model_cotxe=self.test_model_coche,
            carrega_actual=50, capacitat_bateria=70
        )
        self.estacio = EstacioCarrega.objects.create(
            id_punt="TESTEST01", lat=41.0, lng=2.0, nplaces="1", gestio="Test", tipus_acces="Test"
        )
        self.reserva_dia_19 = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 19),
            hora=time(10, 0),
            duracion=timedelta(hours=2),
            vehicle=self.test_vehicle
        )
        self.reserva_dia_20 = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 20),
            hora=time(15, 0),
            duracion=timedelta(hours=1),
            vehicle=self.test_vehicle
        )
        self.list_url = reverse('reserva-list')

    def test_filtrar_reservas_por_dia_existente(self):
        self.client.force_login(self.test_user)
        fecha_filtro = "19/03/2025"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro}"
        response = self.client.get(url_con_filtro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.reserva_dia_19.id)
        self.assertEqual(response.data[0]['fecha'], fecha_filtro)

    def test_filtrar_reservas_por_dia_inexistente(self):
        self.client.force_login(self.test_user)
        fecha_filtro = "21/03/2025"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro}"
        response = self.client.get(url_con_filtro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filtrar_reservas_formato_dia_invalido(self):
        self.client.force_login(self.test_user)
        fecha_filtro_invalida = "2025-03-19"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro_invalida}"
        response = self.client.get(url_con_filtro)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
