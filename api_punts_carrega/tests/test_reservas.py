from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from api_punts_carrega.models import EstacioCarrega, Reserva, Ubicacio
import json

class ReservaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.uubicacio = Ubicacio.objects.create(
            id_ubicacio="loc_001",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Barcelona, 123",
            ciutat="Barcelona",
            provincia="Barcelona"
        )
        
        self.estacio = EstacioCarrega.objects.create(
            id_estacio="12345",
            gestio="Public",
            tipus_acces="targeta",
            ubicacio_estacio = self.uubicacio,
            nplaces="2",
        )
        '''
        self.reserva_data = {
            "estacio_id": self.estacio.id_estacio,
            "fecha": "2025-03-19",
            "hora": "10:00",
            "duracion": 2
        }'''
        self.reserva = Reserva.objects.create(
            estacion=self.estacio,
            fecha="2025-03-19",
            hora="10:00",
            duracion=2
        )

    def test_crear_reserva(self):
        response = self.client.post(
            reverse('crear_reserva'),
            data=json.dumps(self.reserva_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 2)

    def test_modificar_reserva(self):
        modificar_data = {
            "fecha": "2025-03-20",
            "hora": "11:00",
            "duracion": 3
        }
        response = self.client.put(
            reverse('modificar_reserva', kwargs={'reserva_id': self.reserva.id}),
            data=json.dumps(modificar_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.fecha, "2025-03-20")
        self.assertEqual(self.reserva.hora, "11:00")
        self.assertEqual(self.reserva.duracion, 3)

    def test_eliminar_reserva(self):
        response = self.client.delete(
            reverse('eliminar_reserva', kwargs={'reserva_id': self.reserva.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reserva.objects.count(), 0)