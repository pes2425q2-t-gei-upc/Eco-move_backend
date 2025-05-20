import json
import requests
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from api_punts_carrega.models import RefugioClimatico, Usuario
from api_punts_carrega.serializers import RefugioClimaticoSerializer

class RefugioClimaticoModelTest(TestCase):
    """Tests para el modelo RefugioClimatico"""
    
    def setUp(self):
        # Crear refugio de prueba
        self.refugio = RefugioClimatico.objects.create(
            id_punt="test_refugio_1",
            nombre="Refugio Test",
            lat=41.3851,
            lng=2.1734,
            direccio="Calle Test, 123",
            numero_calle="123",
            ciutat="Barcelona",
            provincia="Barcelona"
        )
    
    def test_refugio_creation(self):
        """Verifica que el refugio se crea correctamente"""
        self.assertEqual(self.refugio.nombre, "Refugio Test")
        self.assertEqual(self.refugio.lat, 41.3851)
        self.assertEqual(self.refugio.lng, 2.1734)
        self.assertEqual(self.refugio.direccio, "Calle Test, 123")
        self.assertEqual(self.refugio.numero_calle, "123")
        self.assertEqual(self.refugio.ciutat, "Barcelona")
    
    def test_refugio_str(self):
        """Verifica que el método __str__ funciona correctamente"""
        expected_str = f"Refugio {self.refugio.nombre} - {self.refugio.lat}, {self.refugio.lng}"
        self.assertEqual(str(self.refugio), expected_str)


class RefugioClimaticoAPITest(APITestCase):
    """Tests para los endpoints básicos de la API de refugios climáticos"""
    
    def setUp(self):
        # Crear cliente API
        self.client = APIClient()
        
        # Crear usuario administrador
        self.admin_user = Usuario.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpassword",
            is_staff=True,
            is_superuser=True
        )
        
        # Crear usuario normal
        self.normal_user = Usuario.objects.create_user(
            username="user",
            email="user@example.com",
            password="userpassword"
        )
        
        # Crear refugios de prueba
        self.refugio1 = RefugioClimatico.objects.create(
            id_punt="test_refugio_1",
            nombre="Refugio Test 1",
            lat=41.3851,
            lng=2.1734,
            direccio="Calle Test, 123",
            numero_calle="123"
        )
        
        self.refugio2 = RefugioClimatico.objects.create(
            id_punt="test_refugio_2",
            nombre="Refugio Test 2",
            lat=41.4,
            lng=2.2,
            direccio="Calle Test, 456",
            numero_calle="456"
        )
    
    def test_get_refugios(self):
        """Verifica que se pueden obtener todos los refugios"""
        url = '/api_punts_carrega/refugios/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        refugios = RefugioClimatico.objects.all()
        serializer = RefugioClimaticoSerializer(refugios, many=True)
        self.assertEqual(len(response.data), len(serializer.data))
    
    def test_get_refugio_detail(self):
        """Verifica que se puede obtener un refugio específico"""
        url = f'/api_punts_carrega/refugios/{self.refugio1.id_punt}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        serializer = RefugioClimaticoSerializer(self.refugio1)
        self.assertEqual(response.data, serializer.data)
    
        
    def test_create_refugio(self):
        """Verifica que un administrador puede crear refugios"""
        # Autenticar como administrador
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/refugios/'
        data = {
            'id_punt': 'new_refugio',
            'nombre': 'Nuevo Refugio',
            'lat': 41.5,
            'lng': 2.3,
            'direccio': 'Nueva Dirección',
            'numero_calle': '789'
        }
        
        response = self.client.post(url, data, format='json')
        
        # Si el endpoint requiere permisos específicos, este test podría fallar
        # En ese caso, ajusta según los permisos reales de tu aplicación
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que el refugio se creó correctamente
        self.assertTrue(RefugioClimatico.objects.filter(id_punt='new_refugio').exists())


class SincronizarRefugiosTest(APITestCase):
    """Tests para el endpoint sincronizar_refugios"""
    
    def setUp(self):
        # Crear cliente API
        self.client = APIClient()
        
        # Crear usuario administrador
        self.admin_user = Usuario.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="adminpassword",
            is_staff=True,
            is_superuser=True
        )
        
        # Datos de ejemplo para mock de la API externa
        self.mock_api_data = [
            {
                'id': 'refugio_api_1',
                'nombre': 'Refugio API 1',
                'latitud': '41.3851',
                'longitud': '2.1734',
                'direccion': 'Calle API, 123',
                'numero_calle': '123'
            },
            {
                'id': 'refugio_api_2',
                'nombre': 'Refugio API 2',
                'latitud': '41.4',
                'longitud': '2.2',
                'direccion': 'Calle API, 456',
                'numero_calle': '456'
            }
        ]
    
    @patch('requests.get')
    def test_sincronizar_refugios_success(self, mock_get):
        """Verifica que sincronizar_refugios funciona correctamente"""
        # Configurar el mock para simular una respuesta exitosa de la API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_data
        mock_get.return_value = mock_response
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta es correcta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('mensaje', response.data)
        self.assertIn('total_refugios', response.data)
        
        # Verificar que se crearon los refugios
        self.assertTrue(RefugioClimatico.objects.filter(id_punt='refugio_api_1').exists())
        self.assertTrue(RefugioClimatico.objects.filter(id_punt='refugio_api_2').exists())
        
        # Verificar que los datos se guardaron correctamente
        refugio1 = RefugioClimatico.objects.get(id_punt='refugio_api_1')
        self.assertEqual(refugio1.nombre, 'Refugio API 1')
        self.assertEqual(float(refugio1.lat), 41.3851)
        self.assertEqual(float(refugio1.lng), 2.1734)
        self.assertEqual(refugio1.direccio, 'Calle API, 123')
        self.assertEqual(refugio1.numero_calle, '123')
    
    @patch('requests.get')
    def test_sincronizar_refugios_update_existing(self, mock_get):
        """Verifica que sincronizar_refugios actualiza refugios existentes"""
        # Crear un refugio existente que será actualizado
        RefugioClimatico.objects.create(
            id_punt='refugio_api_1',
            nombre='Nombre Antiguo',
            lat=40.0,
            lng=2.0,
            direccio='Dirección Antigua',
            numero_calle='999'
        )
        
        # Configurar el mock para simular una respuesta exitosa de la API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_data
        mock_get.return_value = mock_response
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta es correcta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el mensaje indica que se actualizaron refugios
        self.assertIn('mensaje', response.data)
        self.assertIn('actualizados', response.data['mensaje'])
        
        # Verificar que el refugio se actualizó correctamente
        refugio1 = RefugioClimatico.objects.get(id_punt='refugio_api_1')
        self.assertEqual(refugio1.nombre, 'Refugio API 1')  # Nombre actualizado
        self.assertEqual(float(refugio1.lat), 41.3851)  # Latitud actualizada
        self.assertEqual(float(refugio1.lng), 2.1734)  # Longitud actualizada
        self.assertEqual(refugio1.direccio, 'Calle API, 123')  # Dirección actualizada
        self.assertEqual(refugio1.numero_calle, '123')  # Número de calle actualizado
    
    @patch('requests.get')
    def test_sincronizar_refugios_timeout(self, mock_get):
        """Verifica que sincronizar_refugios maneja correctamente los timeouts"""
        # Configurar el mock para simular un timeout
        mock_get.side_effect = requests.Timeout("Connection timed out")
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta indica un timeout
        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertIn('error', response.data)
        self.assertIn('Tiempo de espera agotado', response.data['error'])
    
    @patch('requests.get')
    def test_sincronizar_refugios_http_error(self, mock_get):
        """Verifica que sincronizar_refugios maneja correctamente los errores HTTP"""
        # Crear una respuesta con error HTTP
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Client Error")
        mock_response.raise_for_status.side_effect.response = mock_response
        mock_get.return_value = mock_response
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta indica un error HTTP
        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        self.assertIn('Error HTTP', response.data['error'])
    
    @patch('requests.get')
    def test_sincronizar_refugios_request_exception(self, mock_get):
        """Verifica que sincronizar_refugios maneja correctamente las excepciones de solicitud"""
        # Configurar el mock para simular una excepción de solicitud
        mock_get.side_effect = requests.RequestException("Connection error")
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta indica un error de conexión
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn('error', response.data)
        self.assertIn('Error de conexión', response.data['error'])
    
    @patch('requests.get')
    def test_sincronizar_refugios_mixed_create_update(self, mock_get):
        """Verifica que sincronizar_refugios puede crear y actualizar refugios en la misma operación"""
        # Crear un refugio existente que será actualizado
        RefugioClimatico.objects.create(
            id_punt='refugio_api_1',
            nombre='Nombre Antiguo',
            lat=40.0,
            lng=2.0,
            direccio='Dirección Antigua',
            numero_calle='999'
        )
        
        # Configurar el mock para simular una respuesta exitosa de la API
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.mock_api_data
        mock_get.return_value = mock_response
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta es correcta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el mensaje indica que se crearon y actualizaron refugios
        self.assertIn('mensaje', response.data)
        self.assertIn('nuevos', response.data['mensaje'])
        self.assertIn('actualizados', response.data['mensaje'])
        
        # Verificar que se actualizó el refugio existente
        refugio1 = RefugioClimatico.objects.get(id_punt='refugio_api_1')
        self.assertEqual(refugio1.nombre, 'Refugio API 1')
        
        # Verificar que se creó el nuevo refugio
        self.assertTrue(RefugioClimatico.objects.filter(id_punt='refugio_api_2').exists())
        refugio2 = RefugioClimatico.objects.get(id_punt='refugio_api_2')
        self.assertEqual(refugio2.nombre, 'Refugio API 2')

    @patch('requests.get')
    def test_sincronizar_refugios_api_error(self, mock_get):
        """Verifica que sincronizar_refugios maneja errores de la API correctamente"""
        # Configurar el mock para simular un error de la API
        mock_get.side_effect = Exception("API Error")
        
        # Autenticar como administrador (si es necesario)
        self.client.force_authenticate(user=self.admin_user)
        
        url = '/api_punts_carrega/sincronizar_refugios/'
        response = self.client.get(url)
        
        # Verificar que la respuesta indica un error
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn('error', response.data)


class RefugiosMasCercanosTest(APITestCase):
    """Tests para el endpoint refugios_mas_cercanos"""
    
    def setUp(self):
        # Crear cliente API
        self.client = APIClient()
        
        # Crear refugios de prueba en diferentes ubicaciones
        self.refugio1 = RefugioClimatico.objects.create(
            id_punt="refugio_cercano_1",
            nombre="Refugio Cercano 1",
            lat=41.3851,  # Barcelona
            lng=2.1734,
            direccio="Calle Cercana, 123",
            numero_calle="123"
        )
        
        self.refugio2 = RefugioClimatico.objects.create(
            id_punt="refugio_cercano_2",
            nombre="Refugio Cercano 2",
            lat=41.3861,  # Muy cerca del primero
            lng=2.1744,
            direccio="Calle Cercana, 456",
            numero_calle="456"
        )
        
        self.refugio3 = RefugioClimatico.objects.create(
            id_punt="refugio_lejano",
            nombre="Refugio Lejano",
            lat=40.4168,  # Madrid (lejos de Barcelona)
            lng=-3.7038,
            direccio="Calle Lejana, 789",
            numero_calle="789"
        )
    
    def test_refugios_mas_cercanos_success(self):
        """Verifica que refugios_mas_cercanos devuelve los refugios más cercanos"""
        # Ubicación en Barcelona
        url = '/api_punts_carrega/refugios_mas_cercanos/?lat=41.3851&lng=2.1734'
        response = self.client.get(url)
        
        # Verificar que la respuesta es correcta
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que devuelve los refugios ordenados por distancia
        self.assertEqual(len(response.data), 3)  
        
        # El primer refugio debería ser el más cercano (refugio1 o refugio2)
        # y el último debería ser el más lejano (refugio3)
        primer_refugio_id = response.data[0]['refugio']['id_punt']
        ultimo_refugio_id = response.data[-1]['refugio']['id_punt']
        
        self.assertIn(primer_refugio_id, ['refugio_cercano_1', 'refugio_cercano_2'])
        self.assertEqual(ultimo_refugio_id, 'refugio_lejano')
        
        # Verificar que las distancias están incluidas y son números
        self.assertIn('distancia_km', response.data[0])
        self.assertIsInstance(response.data[0]['distancia_km'], float)
    
    def test_refugios_mas_cercanos_missing_params(self):
        """Verifica que refugios_mas_cercanos requiere parámetros lat y lng"""
        # Sin parámetros
        url = '/api_punts_carrega/refugios_mas_cercanos/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Solo lat
        url = '/api_punts_carrega/refugios_mas_cercanos/?lat=41.3851'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Solo lng
        url = '/api_punts_carrega/refugios_mas_cercanos/?lng=2.1734'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_refugios_mas_cercanos_invalid_params(self):
        """Verifica que refugios_mas_cercanos valida los parámetros lat y lng"""
        # Parámetros no numéricos
        url = '/api_punts_carrega/refugios_mas_cercanos/?lat=abc&lng=def'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

