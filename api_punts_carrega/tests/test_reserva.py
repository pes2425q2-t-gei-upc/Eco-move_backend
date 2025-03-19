# tests/test_reservas.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from api_punts_carrega.models import EstacioCarrega, Reserva, Ubicacio
import json

class CrearReservaTestCase(TestCase):
    def setUp(self):
        self.client = Client()

        # Crear una ubicación de prueba
        self.ubicacio = Ubicacio.objects.create(
            id_ubicacio='222',
            direccio='Plaza Catalunya',
            lat=2.234567,
            lng=1.234567,
            ciutat='Barcelona',
            provincia='Barcelona'
        )

        # Crear una estación de carga asociada a la ubicación
        self.estacio = EstacioCarrega.objects.create(
            id_estacio='1',
            gestio='Gestio Test',
            tipus_acces='Acces Test',
            ubicacio_estacio=self.ubicacio
        )

        # URL del endpoint para crear reservas
        self.url = reverse('crear_reserva')

        # Datos de la primera reserva
        self.data_reserva_1 = {
            'estacio_id': self.estacio.id_estacio,
            'fecha': '2023-12-31',
            'hora': '12:00:00',
            'duracion': '01:00:00',  # 1 hora de duración
        }

        # Datos de la segunda reserva solapada
        self.data_reserva_2 = {
            'estacio_id': self.estacio.id_estacio,
            'fecha': '2023-12-31',
            'hora': '12:30:00',  # Empieza a las 12:30, solapa con la anterior
            'duracion': '01:00:00',
        }

    def test_crear_reserva_exito(self):
        """Prueba la creación exitosa de una reserva"""
        response = self.client.post(
            self.url,
            data=json.dumps(self.data_reserva_1),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reserva.objects.count(), 1)

    def test_crear_reserva_solapada(self):
        """Prueba que no se puedan hacer reservas solapadas"""
        # Crear la primera reserva
        self.client.post(
            self.url,
            data=json.dumps(self.data_reserva_1),
            content_type='application/json'
        )

        # Intentar crear una segunda reserva en el mismo horario
        response = self.client.post(
            self.url,
            data=json.dumps(self.data_reserva_2),
            content_type='application/json'
        )

        # La respuesta debe ser un error 409 (Conflict)
        self.assertEqual(response.status_code, 409)
        self.assertEqual(Reserva.objects.count(), 1)  # Solo debe haber 1 reserva creada