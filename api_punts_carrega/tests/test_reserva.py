from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva

class ReservaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        
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
        
        self.reserva = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 19),
            hora=time(10, 0),
            duracion=timedelta(hours=2)
        )
        
        self.reserva_data = {
            "estacion": self.estacio.id_punt,
            "fecha": "20/03/2025",
            "hora": "14:00",
            "duracion": "03:00:00"
        }
        
    def test_crear_reserva(self):
        url = reverse('reserva-crear')
        response = self.client.post(
            url,
            data=json.dumps(self.reserva_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 2)
        
        nueva_reserva = Reserva.objects.exclude(pk=self.reserva.pk).first()
        self.assertEqual(nueva_reserva.fecha, date(2025, 3, 20))
        self.assertEqual(nueva_reserva.hora, time(14, 0))
        self.assertEqual(nueva_reserva.duracion, timedelta(hours=3))
        
    def test_modificar_reserva(self):
        modificar_data = {
            "fecha": "20/03/2025",
            "hora": "11:00",
            "duracion": "04:00:00"
        }
        
        url = reverse('reserva-modificar', kwargs={'pk': self.reserva.pk})
        response = self.client.put(
            url,
            data=json.dumps(modificar_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.fecha, date(2025, 3, 20))
        self.assertEqual(self.reserva.hora, time(11, 0))
        self.assertEqual(self.reserva.duracion, timedelta(hours=4))
        
    def test_eliminar_reserva(self):
        url = reverse('reserva-eliminar', kwargs={'pk': self.reserva.pk})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reserva.objects.count(), 0)
