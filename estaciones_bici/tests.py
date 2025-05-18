from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch, Mock
from django.utils.timezone import now, timedelta
from estaciones_bici.models import EstacionBici, DisponibilidadEstacionBici, ReservaBici

User = get_user_model()

class BicingForceEndpointsTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="12345678")
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    @patch("estaciones_bici.utils.get_bicing_headers")
    @patch("estaciones_bici.utils.requests.get")
    def test_forzar_importar(self, mock_get, mock_headers):
        mock_headers.return_value = {}  # Simula los headers para evitar error por variable de entorno
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {
                "stations": []
            }
        }
        mock_get.return_value = mock_response

        response = self.client.post("/api/bicing/estaciones/forzar-importar/")
        self.assertEqual(response.status_code, 200)

    @patch("estaciones_bici.utils.get_bicing_headers")
    @patch("estaciones_bici.utils.requests.get")
    def test_forzar_actualizar(self, mock_get, mock_headers):
        mock_headers.return_value = {}  # Simula los headers para evitar error por variable de entorno
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "last_updated": 1234567890,
            "data": {
                "stations": []
            }
        }
        mock_get.return_value = mock_response

        response = self.client.post("/api/bicing/estaciones/forzar-actualizar/")
        self.assertEqual(response.status_code, 200)


class ReservaBiciTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='12345678')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Crear estación con disponibilidad
        self.estacion = EstacionBici.objects.create(
            station_id=101,
            name="Estació Test",
            address="Carrer Test",
            lat=41.38,
            lon=2.17,
            capacity=20,
            is_charging_station=True
        )
        self.dispo = DisponibilidadEstacionBici.objects.create(
            estacion=self.estacion,
            num_bicis_disponibles=5,
            num_bicis_mecanicas=3,
            num_bicis_electricas=2,
            num_docks_disponibles=15,
            estado="IN_SERVICE"            
        )

    def test_crear_reserva_exitosa(self):
        response = self.client.post('/api/bicing/reservas/', {
            "estacion": self.estacion.id,
            "tipo_bicicleta": "mecanica"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tipo_bicicleta"], "mecanica")
        self.assertEqual(response.data["activa"], True)

    def test_crear_reserva_fallida_sin_disponibilidad(self):
        # Simula que todas las mecánicas están ya reservadas
        for _ in range(3):
            ReservaBici.objects.create(
                usuario=self.user,
                estacion=self.estacion,
                tipo_bicicleta='mecanica',
                activa=True,
                expiracion=now() + timedelta(minutes=15)
            )

        response = self.client.post('/api/bicing/reservas/', {
            "estacion": self.estacion.id,
            "tipo_bicicleta": "mecanica"
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No hay bicicletas disponibles", str(response.data))

    def test_listar_mis_reservas(self):
        ReservaBici.objects.create(
            usuario=self.user,
            estacion=self.estacion,
            tipo_bicicleta='mecanica',
            activa=True,
            expiracion=now() + timedelta(minutes=15)
        )

        response = self.client.get('/api/bicing/reservas/mis_reservas/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["usuario"], self.user.id)

    def test_cancelar_reserva_activa(self):
        reserva = ReservaBici.objects.create(
            usuario=self.user,
            estacion=self.estacion,
            tipo_bicicleta='mecanica',
            activa=True,
            expiracion=now() + timedelta(minutes=15)
        )

        response = self.client.delete(f'/api/bicing/reservas/{reserva.id}/')
        self.assertEqual(response.status_code, 200)

        reserva.refresh_from_db()
        self.assertFalse(reserva.activa)

    def test_ver_historial_de_reservas(self):
        # Reserva activa (no debe aparecer)
        ReservaBici.objects.create(
            usuario=self.user,
            estacion=self.estacion,
            tipo_bicicleta='mecanica',
            activa=True,
            expiracion=now() + timedelta(minutes=15)
        )

        # Reserva inactiva (cancelada o expirada)
        ReservaBici.objects.create(
            usuario=self.user,
            estacion=self.estacion,
            tipo_bicicleta='electrica',
            activa=False,
            expiracion=now() - timedelta(minutes=5)
        )

        response = self.client.get('/api/bicing/reservas/historial/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["activa"], False)
        self.assertEqual(response.data[0]["tipo_bicicleta"], "electrica")
