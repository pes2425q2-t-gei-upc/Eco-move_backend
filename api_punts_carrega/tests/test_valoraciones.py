import json
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from api_punts_carrega.models import ValoracionEstacion, EstacioCarrega, Usuario
from api_punts_carrega.serializers import ValoracionEstacionSerializer, EstacioCarregaConValoracionesSerializer

class ValoracionEstacionModelTest(TestCase):
    """Tests para el modelo ValoracionEstacion"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User"
        )
        
        # Crear estación de prueba
        self.estacion = EstacioCarrega.objects.create(
            id_punt=1,
            lat=41.3851,
            lng=2.1734,
            gestio="Test",
            tipus_acces="Público",
            nplaces=2,
            potencia=50
        )
        
        # Crear valoración de prueba
        self.valoracion = ValoracionEstacion.objects.create(
            estacion=self.estacion,
            usuario=self.usuario,
            puntuacion=4,
            comentario="Buena estación, carga rápida"
        )
    
    def test_valoracion_creation(self):
        """Verifica que la valoración se crea correctamente"""
        self.assertEqual(self.valoracion.puntuacion, 4)
        self.assertEqual(self.valoracion.comentario, "Buena estación, carga rápida")
        self.assertEqual(self.valoracion.usuario, self.usuario)
        self.assertEqual(self.valoracion.estacion, self.estacion)
    
    def test_valoracion_str(self):
        """Verifica que el método __str__ funciona correctamente"""
        expected_str = f"Valoración de {self.usuario.username} para {self.estacion.id_punt}: 4/5"
        self.assertEqual(str(self.valoracion), expected_str)
    
    def test_unique_constraint(self):
        """Verifica que un usuario no puede valorar la misma estación dos veces"""
        # Intentar crear una segunda valoración del mismo usuario para la misma estación
        with self.assertRaises(Exception):
            ValoracionEstacion.objects.create(
                estacion=self.estacion,
                usuario=self.usuario,
                puntuacion=5,
                comentario="Otra valoración"
            )
    
    def test_puntuacion_validation(self):
        """Verifica que la puntuación debe estar entre 1 y 5"""
        # Intentar crear una valoración con puntuación fuera de rango
        with self.assertRaises(Exception):
            ValoracionEstacion.objects.create(
                estacion=self.estacion,
                usuario=self.usuario,
                puntuacion=6,
                comentario="Puntuación inválida"
            )


class ValoracionEstacionAPITest(APITestCase):
    """Tests para los endpoints de la API de valoraciones"""
    
    def setUp(self):
        # Crear cliente API
        self.client = APIClient()
        
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User"
        )
        
        # Crear estación de prueba
        self.estacion = EstacioCarrega.objects.create(
            id_punt="test_station_1",
            lat=41.3851,
            lng=2.1734,
            gestio="Test",
            tipus_acces="Público",
            nplaces=2,
            potencia=50
        )
        
        # Crear valoración de prueba
        self.valoracion = ValoracionEstacion.objects.create(
            estacion=self.estacion,
            usuario=self.usuario,
            puntuacion=4,
            comentario="Buena estación, carga rápida"
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.usuario)
    
    def test_get_valoraciones(self):
        """Verifica que se pueden obtener las valoraciones"""
        # Usar la URL directamente en lugar de reverse
        url = '/api_punts_carrega/valoraciones_estaciones/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        valoraciones = ValoracionEstacion.objects.all()
        serializer = ValoracionEstacionSerializer(valoraciones, many=True)
        self.assertEqual(response.data, serializer.data)
    
    def test_get_valoraciones_por_estacion(self):
        """Verifica que se pueden filtrar valoraciones por estación"""
        # Usar la URL directamente con parámetro de consulta
        url = f'/api_punts_carrega/valoraciones_estaciones/?estacion={self.estacion.id_punt}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        valoraciones = ValoracionEstacion.objects.filter(estacion=self.estacion)
        serializer = ValoracionEstacionSerializer(valoraciones, many=True)
        self.assertEqual(response.data, serializer.data)
    
    def test_crear_valoracion(self):
        """Verifica que se puede crear una valoración"""
        # Crear otra estación para valorar
        estacion2 = EstacioCarrega.objects.create(
            id_punt=2,
            lat=41.4,
            lng=2.2,
            gestio="Test2",
            tipus_acces="Público",
            nplaces=1,
            potencia=22
        )
        
        # Usar la URL directamente
        url = '/api_punts_carrega/valoraciones_estaciones/'
        data = {
            'estacion': estacion2.id_punt,
            'puntuacion': 5,
            'comentario': 'Excelente estación',
            'usuario': self.usuario.id
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verificar que la valoración se creó correctamente
        self.assertEqual(ValoracionEstacion.objects.count(), 2)
        nueva_valoracion = ValoracionEstacion.objects.get(estacion=estacion2)
        self.assertEqual(nueva_valoracion.puntuacion, 5)
        self.assertEqual(nueva_valoracion.comentario, 'Excelente estación')
        self.assertEqual(nueva_valoracion.usuario, self.usuario)
    
    def test_actualizar_valoracion(self):
        """Verifica que se puede actualizar una valoración existente"""
        # Usar la URL directamente
        url = f'/api_punts_carrega/valoraciones_estaciones/{self.valoracion.id}/'
        data = {
            'estacion': self.estacion.id_punt,
            'puntuacion': 3,
            'comentario': 'Actualizado: Estación normal',
            'usuario': self.usuario.id
        }
        
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la valoración se actualizó correctamente
        self.valoracion.refresh_from_db()
        self.assertEqual(self.valoracion.puntuacion, 3)
        self.assertEqual(self.valoracion.comentario, 'Actualizado: Estación normal')
    
    def test_eliminar_valoracion(self):
        """Verifica que se puede eliminar una valoración"""
        # Usar la URL directamente
        url = f'/api_punts_carrega/valoraciones_estaciones/{self.valoracion.id}/'
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verificar que la valoración se eliminó
        self.assertEqual(ValoracionEstacion.objects.count(), 0)
    
    def test_validacion_puntuacion(self):
        """Verifica que la API valida el rango de puntuación"""
        # Usar la URL directamente
        url = '/api_punts_carrega/valoraciones_estaciones/'
        data = {
            'estacion': self.estacion.id_punt,
            'puntuacion': 6,  # Fuera de rango
            'comentario': 'Puntuación inválida'
        }
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class EstacionConValoracionesTest(APITestCase):
    """Tests para verificar la funcionalidad de estaciones con valoraciones"""
    
    def setUp(self):
        # Crear cliente API
        self.client = APIClient()
        
        # Crear usuarios de prueba
        self.usuario1 = Usuario.objects.create_user(
            username="user1", email="user1@example.com", password="password1"
        )
        self.usuario2 = Usuario.objects.create_user(
            username="user2", email="user2@example.com", password="password2"
        )
        self.usuario3 = Usuario.objects.create_user(
            username="user3", email="user3@example.com", password="password3"
        )
        
        # Crear estación de prueba
        self.estacion = EstacioCarrega.objects.create(
            id_punt="test_station_ratings",
            lat=41.3851,
            lng=2.1734,
            gestio="Test",
            tipus_acces="Público",
            nplaces=2,
            potencia=50
        )
        
        # Crear varias valoraciones para la estación
        self.valoracion1 = ValoracionEstacion.objects.create(
            estacion=self.estacion, usuario=self.usuario1, puntuacion=5, 
            comentario="Excelente"
        )
        self.valoracion2 = ValoracionEstacion.objects.create(
            estacion=self.estacion, usuario=self.usuario2, puntuacion=3, 
            comentario="Normal"
        )
        self.valoracion3 = ValoracionEstacion.objects.create(
            estacion=self.estacion, usuario=self.usuario3, puntuacion=4, 
            comentario="Buena"
        )
        
        # Autenticar usuario
        self.client.force_authenticate(user=self.usuario1)
    
    def test_get_estacion_con_valoraciones(self):
        """Verifica que se pueden obtener las estaciones con sus valoraciones"""
        # Usar la URL directamente con parámetro de consulta
        url = f'/api_punts_carrega/estacions/{self.estacion.id_punt}/?include_valoraciones=true'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la respuesta incluye las valoraciones
        self.assertIn('valoraciones', response.data)
        self.assertEqual(len(response.data['valoraciones']), 3)
        
        # Verificar que la puntuación media es correcta
        self.assertIn('puntuacion_media', response.data)
        # La media de 5, 3 y 4 es 4
        self.assertEqual(response.data['puntuacion_media'], 4.0)
        
        # Verificar que el número de valoraciones es correcto
        self.assertIn('num_valoraciones', response.data)
        self.assertEqual(response.data['num_valoraciones'], 3)
    
    def test_estadisticas_valoraciones(self):
        """Verifica que las estadísticas de valoraciones son correctas"""
        # Usar la URL directamente para la acción valoraciones
        url = f'/api_punts_carrega/estacions/{self.estacion.id_punt}/estadisticas_valoraciones/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar estadísticas
        self.assertEqual(response.data['media'], 4.0)  # (5+3+4)/3 = 4
        self.assertEqual(response.data['total'], 3)
        self.assertEqual(response.data['puntuacion_1'], 0)
        self.assertEqual(response.data['puntuacion_2'], 0)
        self.assertEqual(response.data['puntuacion_3'], 1)
        self.assertEqual(response.data['puntuacion_4'], 1)
        self.assertEqual(response.data['puntuacion_5'], 1)

    def test_get_valoraciones_action(self):
        """Verifica que la acción 'valoraciones' devuelve todas las valoraciones de una estación"""
        # Usar la URL directamente para la acción valoraciones
        url = f'/api_punts_carrega/estacions/{self.estacion.id_punt}/valoraciones/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la respuesta contiene todas las valoraciones de la estación
        valoraciones = ValoracionEstacion.objects.filter(estacion=self.estacion)
        serializer = ValoracionEstacionSerializer(valoraciones, many=True)
        self.assertEqual(len(response.data), 3)
        
        # Verificar que los datos de las valoraciones son correctos
        valoraciones_ids = [item['id'] for item in response.data]
        self.assertIn(self.valoracion1.id, valoraciones_ids)
        self.assertIn(self.valoracion2.id, valoraciones_ids)
        self.assertIn(self.valoracion3.id, valoraciones_ids)
        
        # Verificar que los comentarios están presentes
        comentarios = [item['comentario'] for item in response.data]
        self.assertIn("Excelente", comentarios)
        self.assertIn("Normal", comentarios)
        self.assertIn("Buena", comentarios)
        
        # Verificar que las puntuaciones están presentes
        puntuaciones = [item['puntuacion'] for item in response.data]
        self.assertIn(5, puntuaciones)
        self.assertIn(3, puntuaciones)
        self.assertIn(4, puntuaciones)
        
        # Verificar que los nombres de usuario están presentes
        usernames = [item['username'] for item in response.data]
        self.assertIn("user1", usernames)
        self.assertIn("user2", usernames)
        self.assertIn("user3", usernames)

