# tests/test_reservas.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from api_punts_carrega.models import EstacioCarrega, Reserva, Ubicacio
import json

class CrearReservaTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.ubicacio = Ubicacio.objects.create(
            direccio='Plaza Catalunya',
        id_ubicacio = '222',
        lat = '2.234567',
        lng = '1.234567',
        ciutat = 'bcn',
        provincia = 'bcnprovincia'
        )
        self.estacio = EstacioCarrega.objects.create(
            id_estacio='1',
            gestio='Gestio Test',
            tipus_acces='Acces Test',
            ubicacio_estacio=self.ubicacio
        )
        self.url = reverse('crear_reserva')
        self.data = {
            'estacio_id': self.estacio.id_estacio,
            'fecha': '2023-12-31',
            'hora': '12:00:00',
            'duracion': '01:00:00',
        }

    def test_crear_reserva_exito(self):

        response = self.client.post(
            self.url,
            data=json.dumps(self.data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reserva.objects.count(), 1)
        self.assertEqual(Reserva.objects.first().estacio, self.estacio)
