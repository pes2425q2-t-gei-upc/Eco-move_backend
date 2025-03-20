from django.test import TestCase, Client
from rest_framework.test import APITestCase
from django.urls import reverse
from rest_framework import status
from api_punts_carrega.models import EstacioCarrega, Reserva, Ubicacio
import json
from datetime import date, time, timedelta

class ReservaTests(APITestCase):
    """Test API endpoints for reservations."""
    
    def setUp(self):
        """Set up the reservations"""
        self.client = Client()
        
        # Create location
        self.ubicacio = Ubicacio.objects.create(
            id_ubicacio="loc_001",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Barcelona, 123",
            ciutat="Barcelona",
            provincia="Barcelona"
        )
        
        # Create charging station
        self.estacio = EstacioCarrega.objects.create(
            id_estacio="12345",
            gestio="Public",
            tipus_acces="targeta",
            ubicacio_estacio=self.ubicacio,
            nplaces="2",
        )
        
        # Create reservation
        self.reserva = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 19),
            hora=time(10, 0),
            duracion=timedelta(hours=2)
        )
        
        self.reserva2 = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 20),
            hora=time(14, 0),
            duracion=timedelta(hours=3)
        )
        
        self.reserva_url = "/api_punts_carrega/reservas/"
        
        # Definir los datos para crear una nueva reserva
        self.reserva_data = {
            "estacion": self.estacio.id_punt,  # Usa el ID correcto según tu modelo
            "fecha": "2025-03-20",
            "hora": "14:00",
            "duracion": "01:30:00"  # Formato para DurationField: "HH:MM:SS"
        }
        
    def test_get_all_reservations(self):
        response = self.client.get(self.reserva_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        
    def test_get_reservation_by_id(self):
        response = self.client.get(reverse('reserva-detail', kwargs={'pk': self.reserva.id}))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estacion"], self.estacio.id_estacio)

    def test_crear_reserva(self):
        # Asegúrate de que la URL coincida con la definida en urls.py
        response = self.client.post(
            reverse('reserva-list'),  # Ajusta según tu urls.py
            data=json.dumps(self.reserva_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 3)

    def test_modificar_reserva(self):  
        modificar_data = {
            "estacion": self.estacio.id_punt,  # Incluye todos los campos requeridos
            "fecha": "2025-03-20",
            "hora": "11:00",
            "duracion": "03:00:00"  # Formato para DurationField: "HH:MM:SS"
        }
        response = self.client.put(
            reverse('reserva-detail', kwargs={'pk': self.reserva.id}),  # Ajusta según tu urls.py
            data=json.dumps(modificar_data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Recargar el objeto desde la base de datos
        self.reserva.refresh_from_db()
        
        # Comparar con los valores correctos
        self.assertEqual(self.reserva.fecha, date(2025, 3, 20))
        self.assertEqual(self.reserva.hora, time(11, 0))
        self.assertEqual(self.reserva.duracion, timedelta(hours=3))

    def test_eliminar_reserva(self):
        response = self.client.delete(reverse('reserva-detail', kwargs={'pk': self.reserva.id}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)  # Normalmente es 204, no 200
        self.assertEqual(Reserva.objects.count(), 1)