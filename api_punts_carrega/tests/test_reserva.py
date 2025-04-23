# api_punts_carrega/tests/test_reserva.py

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
            password='password123' # Asegurar unicidad
        )

        self.common_charger_type = TipusCarregador.objects.create(
            id_carregador="TEST-CCS-S", nom_tipus="CCS Setup",
            tipus_connector="CCS2", tipus_corrent="DC" # Ejemplo
        )

        self.test_model_coche = ModelCotxe.objects.create(
            marca="TestMarcaS", model="TestModelS", any_model=2024
        )
        self.test_model_coche.tipus_carregador.add(self.common_charger_type)

        self.test_vehicle = Vehicle.objects.create(
            matricula="TEST5678", propietari=self.test_user,
            model_cotxe=self.test_model_coche,
            carrega_actual=50.0, capacitat_bateria=70.0
        )
        # Crear estación y asignar cargador
        self.estacio = EstacioCarrega.objects.create(
            id_punt="TEST-EST-SETUP", lat=41.3, lng=2.1, nplaces="1",
            gestio="TestG", tipus_acces="TestA"
        )
        self.estacio.tipus_carregador.add(self.common_charger_type)

        self.reserva = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 19),
            hora=time(10, 0),
            duracion=timedelta(hours=2),
            vehicle=self.test_vehicle
        )

        self.reserva_data_crear = {
            "estacion": self.estacio.id_punt,
            "fecha": "20/03/2025",
            "hora": "14:00",
            "duracion": "03:00:00",
            "vehicle": self.test_vehicle.matricula
        }

    def test_get_all_reservations(self):
        self.client.force_login(self.test_user)
        url = reverse('reserva-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.reserva.id)

    def test_get_reservation_by_id(self):
        self.client.force_login(self.test_user)
        url = reverse('reserva-detail', kwargs={'pk': self.reserva.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estacion"], self.estacio.id_punt)

    def test_crear_reserva(self):
        url = reverse('reserva-crear')
        self.client.force_login(self.test_user)
        response = self.client.post(
            url,
            data=json.dumps(self.reserva_data_crear),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 2) # La inicial + la nueva
        nueva_reserva = Reserva.objects.exclude(pk=self.reserva.pk).first()
        self.assertEqual(nueva_reserva.fecha, date(2025, 3, 20))
        self.assertEqual(nueva_reserva.hora, time(14, 0))
        self.assertEqual(nueva_reserva.duracion, timedelta(hours=3))
        self.assertEqual(nueva_reserva.vehicle, self.test_vehicle) # Verificar vehículo

    def test_modificar_reserva(self):
        modificar_data = {
            "fecha": "20/03/2025",
            "hora": "11:00",
            "duracion": "04:00:00"
        }
        url = reverse('reserva-modificar', kwargs={'pk': self.reserva.pk})

        self.client.force_login(self.test_user)

        response = self.client.put(
            url,
            data=json.dumps(modificar_data),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, f"Expected 200 OK, got {response.status_code}. Response: {response.content}")

        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.fecha, date(2025, 3, 20))
        self.assertEqual(self.reserva.hora, time(11, 0))
        self.assertEqual(self.reserva.duracion, timedelta(hours=4))

    def test_eliminar_reserva(self):
        url = reverse('reserva-eliminar', kwargs={'pk': self.reserva.pk})
        self.client.force_login(self.test_user)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reserva.objects.count(), 0)