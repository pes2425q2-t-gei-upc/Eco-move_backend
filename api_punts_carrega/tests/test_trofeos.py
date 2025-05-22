from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from api_punts_carrega.models import Usuario, Trofeo, UsuarioTrofeo
from rest_framework.authtoken.models import Token

class TrofeoAPITests(TestCase):
    def setUp(self):
        # Crear usuarios de prueba
        self.client = Client()
        self.test_user = Usuario.objects.create_user(
            username='test_trofeo_user', 
            email='test_trofeo@example.com', 
            password='password123'
        )
        self.admin_user = Usuario.objects.create_user(
            username='admin_trofeo_user', 
            email='admin_trofeo@example.com', 
            password='password456',
            is_admin=True
        )
        
        # Crear tokens para autenticación
        self.token = Token.objects.create(user=self.test_user)
        self.admin_token = Token.objects.create(user=self.admin_user)
        self.auth_header = f'Token {self.token.key}'
        self.admin_auth_header = f'Token {self.admin_token.key}'
        
        # Inicializar trofeos para las pruebas
        self.trofeo_bronce = Trofeo.objects.create(
            id_trofeo=1,
            nombre="Trofeo Bronce",
            descripcion="Has alcanzado 50 puntos. ¡Buen comienzo!",
            puntos_necesarios=50
        )
        
        self.trofeo_plata = Trofeo.objects.create(
            id_trofeo=2,
            nombre="Trofeo Plata",
            descripcion="Has alcanzado 150 puntos. ¡Sigue así!",
            puntos_necesarios=150
        )
        
        self.trofeo_oro = Trofeo.objects.create(
            id_trofeo=3,
            nombre="Trofeo Oro",
            descripcion="Has alcanzado 300 puntos. ¡Impresionante!",
            puntos_necesarios=300
        )
        
        # URLs para las pruebas - Usando URLs directas en lugar de reverse
        self.inicializar_trofeos_url = '/api_punts_carrega/inicializarTrofeos/'
        self.trofeos_user_url = f'/api_punts_carrega/usuari/{self.test_user.pk}/trofeos/'
        self.suma_punts_url = f'/api_punts_carrega/usuari/{self.test_user.pk}/sumaPunts/'
        self.get_punts_url = f'/api_punts_carrega/usuari/{self.test_user.pk}/getPunts/'
        
    def test_inicializar_trofeos(self):
        """Prueba la inicialización de trofeos predeterminados"""
        # Eliminar trofeos existentes para probar la inicialización
        Trofeo.objects.all().delete()
        self.assertEqual(Trofeo.objects.count(), 0)
        
        # Llamar al endpoint de inicialización
        response = self.client.get(self.inicializar_trofeos_url)
        
        # Verificar respuesta y creación de trofeos
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Trofeo.objects.count(), 4)  # Deben crearse 4 trofeos predeterminados
        
        # Verificar que los trofeos tienen los puntos correctos
        puntos_esperados = [50, 150, 300, 500]
        for puntos in puntos_esperados:
            self.assertTrue(Trofeo.objects.filter(puntos_necesarios=puntos).exists())
    
    def test_sumar_puntos_sin_trofeo(self):
        """Prueba sumar puntos insuficientes para obtener un trofeo"""
        # Verificar puntos iniciales
        response = self.client.get(self.get_punts_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos'], 0)
        
        # Sumar puntos insuficientes para un trofeo
        puntos_a_sumar = 30
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': puntos_a_sumar}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar respuesta y puntos actualizados
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], puntos_a_sumar)
        
        # Verificar que no se ha obtenido ningún trofeo
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 0)
        
        # Verificar progreso hacia el siguiente trofeo
        self.assertIsNotNone(response.data['siguiente_trofeo'])
        self.assertEqual(response.data['siguiente_trofeo']['id_trofeo'], self.trofeo_bronce.id_trofeo)
        self.assertAlmostEqual(response.data['progreso_siguiente'], 60.0)  # 30/50 = 60%
    
    def test_obtener_trofeo_bronce(self):
        """Prueba obtener el trofeo de bronce al sumar suficientes puntos"""
        # Sumar puntos suficientes para el trofeo de bronce
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 50}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar respuesta y puntos actualizados
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 50)
        
        # Verificar que se ha obtenido el trofeo de bronce
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 1)
        self.assertEqual(response.data['trofeos_conseguidos'][0]['trofeo']['id_trofeo'], self.trofeo_bronce.id_trofeo)
        
        # Verificar que el siguiente trofeo es el de plata
        self.assertEqual(response.data['siguiente_trofeo']['id_trofeo'], self.trofeo_plata.id_trofeo)
        self.assertEqual(response.data['progreso_siguiente'], 0.0)  # 0/100 puntos adicionales = 0%
    
    def test_obtener_multiples_trofeos(self):
        """Prueba obtener múltiples trofeos al sumar muchos puntos de una vez"""
        # Sumar puntos suficientes para obtener trofeo de bronce y plata de una vez
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 200}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar respuesta y puntos actualizados
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 200)
        
        # Verificar que se han obtenido los trofeos de bronce y plata
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 2)
        
        # Verificar IDs de trofeos obtenidos
        trofeos_ids = [t['trofeo']['id_trofeo'] for t in response.data['trofeos_conseguidos']]
        self.assertIn(self.trofeo_bronce.id_trofeo, trofeos_ids)
        self.assertIn(self.trofeo_plata.id_trofeo, trofeos_ids)
        
        # Verificar que el siguiente trofeo es el de oro
        self.assertEqual(response.data['siguiente_trofeo']['id_trofeo'], self.trofeo_oro.id_trofeo)
        
        # Verificar progreso hacia el trofeo de oro (200-150)/(300-150) = 33.33%
        self.assertAlmostEqual(response.data['progreso_siguiente'], 33.33, delta=0.01)
    
    def test_sumar_puntos_valor_invalido(self):
        """Prueba sumar puntos con un valor inválido"""
        # Intentar sumar puntos negativos
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': -10}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se rechaza la solicitud
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Intentar sumar puntos no numéricos
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': "abc"}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se rechaza la solicitud
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_trofeos_usuario_no_autenticado(self):
        """Prueba acceder a trofeos sin autenticación"""
        response = self.client.get(self.trofeos_user_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_trofeos_otro_usuario(self):
        """Prueba que un usuario puede ver los trofeos de otro usuario"""
        # Primero, dar puntos al usuario de prueba para que tenga trofeos
        self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 150}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Intentar ver los trofeos como administrador
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.admin_auth_header)
        
        # Verificar que se puede acceder a los trofeos
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 2)  # Debe tener 2 trofeos

    def test_progreso_cero_puntos(self):
        """Test para verificar que el progreso es 0 cuando el usuario tiene 0 puntos"""
        # Verificar que el usuario comienza con 0 puntos
        response = self.client.get(self.get_punts_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos'], 0)
        
        # Obtener trofeos y verificar que el progreso es 0
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['progreso_siguiente'], 0)
        
        # Verificar que el siguiente trofeo es el de bronce
        self.assertEqual(response.data['siguiente_trofeo']['id_trofeo'], self.trofeo_bronce.id_trofeo)
    
    def test_progreso_exacto_para_trofeo(self):
        """Test para verificar que el progreso es 100 cuando el usuario tiene exactamente los puntos necesarios para el siguiente trofeo"""
        # Sumar exactamente los puntos necesarios para el trofeo de bronce
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 50}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se han sumado los puntos correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 50)
        
        # Obtener trofeos y verificar que se ha obtenido el trofeo de bronce
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 1)
        
        # Verificar que el progreso hacia el siguiente trofeo es 0
        self.assertEqual(response.data['progreso_siguiente'], 0)
        
        # Ahora sumar exactamente los puntos necesarios para llegar al trofeo de plata
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 100}),  # 50 + 100 = 150 (exactamente los puntos para plata)
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se han sumado los puntos correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 150)
        
        # Obtener trofeos y verificar que se ha obtenido el trofeo de plata
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 2)
        
        # Verificar que el progreso hacia el siguiente trofeo es 0
        self.assertEqual(response.data['progreso_siguiente'], 0)
    
    def test_progreso_entre_trofeos(self):
        """Test para verificar el cálculo correcto del progreso entre trofeos"""
        # Sumar puntos para estar entre el trofeo de bronce y plata
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 100}),  # Más que bronce (50) pero menos que plata (150)
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se han sumado los puntos correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 100)
        
        # Obtener trofeos y verificar el progreso
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # El progreso debería ser (100-50)/(150-50) = 50/100 = 50%
        self.assertEqual(response.data['progreso_siguiente'], 50)
    
    def test_progreso_sin_siguiente_trofeo(self):
        """Test para verificar el comportamiento cuando no hay siguiente trofeo"""
        # Crear un trofeo máximo
        Trofeo.objects.create(
            id_trofeo=99,
            nombre="Trofeo Máximo",
            descripcion="Has alcanzado el máximo nivel",
            puntos_necesarios=1000
        )
        
        # Sumar suficientes puntos para obtener el trofeo máximo
        response = self.client.post(
            self.suma_punts_url,
            data=json.dumps({'punts': 1000}),
            content_type='application/json',
            HTTP_AUTHORIZATION=self.auth_header
        )
        
        # Verificar que se han sumado los puntos correctamente
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['puntos_actuales'], 1000)
        
        # Obtener trofeos y verificar que se han obtenido todos los trofeos
        response = self.client.get(self.trofeos_user_url, HTTP_AUTHORIZATION=self.auth_header)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['trofeos_conseguidos']), 4)  
        
        # Verificar que no hay siguiente trofeo y el progreso es 0
        self.assertIsNone(response.data['siguiente_trofeo'])
        self.assertEqual(response.data['progreso_siguiente'], 0)