from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api_punts_carrega.models import EstacioCarrega, TipusCarregador, TipusVelocitat

class TestFiltros(TestCase):
    """Tests para todas las funcionalidades relacionadas con filtros"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Crear tipos de velocidad
        self.velocitat_lenta = TipusVelocitat.objects.create(
            id_velocitat="lenta",
            nom_velocitat="Càrrega lenta"
        )
        self.velocitat_rapida = TipusVelocitat.objects.create(
            id_velocitat="rapida",
            nom_velocitat="Càrrega ràpida"
        )
        self.velocitat_ultra = TipusVelocitat.objects.create(
            id_velocitat="ultra",
            nom_velocitat="Càrrega ultra-ràpida"
        )
        
        # Crear tipos de cargador
        self.carregador_tipus1 = TipusCarregador.objects.create(
            id_carregador="tipus1",
            nom_tipus="Tipus 1",
            tipus_connector="Connector Tipus 1",
            tipus_corrent="Corrent alterna"
        )
        self.carregador_tipus2 = TipusCarregador.objects.create(
            id_carregador="tipus2",
            nom_tipus="Tipus 2",
            tipus_connector="Connector Tipus 2",
            tipus_corrent="Corrent alterna"
        )
        self.carregador_ccs = TipusCarregador.objects.create(
            id_carregador="ccs",
            nom_tipus="CCS",
            tipus_connector="Connector CCS",
            tipus_corrent="Corrent continua"
        )
        
        # Crear estaciones con diferentes características
        # Estación 1: Potencia baja, carga lenta, tipo 1
        self.estacio1 = EstacioCarrega.objects.create(
            id_punt="estacio_test_1",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Test, 123",
            ciutat="Barcelona",
            provincia="Barcelona",
            gestio="Pública",
            tipus_acces="Lliure",
            nplaces="2",
            potencia=7
        )
        self.estacio1.tipus_velocitat.add(self.velocitat_lenta)
        self.estacio1.tipus_carregador.add(self.carregador_tipus1)
        
        # Estación 2: Potencia media, carga rápida, tipo 2
        self.estacio2 = EstacioCarrega.objects.create(
            id_punt="estacio_test_2",
            lat=41.4036,
            lng=2.1744,
            direccio="Carrer de Prova, 456",
            ciutat="Barcelona",
            provincia="Barcelona",
            gestio="Privada",
            tipus_acces="Restringit",
            nplaces="4",
            potencia=22
        )
        self.estacio2.tipus_velocitat.add(self.velocitat_rapida)
        self.estacio2.tipus_carregador.add(self.carregador_tipus2)
        
        # Estación 3: Potencia alta, carga ultra-rápida, CCS
        self.estacio3 = EstacioCarrega.objects.create(
            id_punt="estacio_test_3",
            lat=41.4100,
            lng=2.1800,
            direccio="Avinguda Test, 789",
            ciutat="Badalona",
            provincia="Barcelona",
            gestio="Pública",
            tipus_acces="Lliure",
            nplaces="1",
            potencia=150
        )
        self.estacio3.tipus_velocitat.add(self.velocitat_ultra)
        self.estacio3.tipus_carregador.add(self.carregador_ccs)
        
        # Estación 4: Múltiples tipos de cargador y velocidad
        self.estacio4 = EstacioCarrega.objects.create(
            id_punt="estacio_test_4",
            lat=41.3900,
            lng=2.1600,
            direccio="Plaça Test, 10",
            ciutat="L'Hospitalet",
            provincia="Barcelona",
            gestio="Privada",
            tipus_acces="Restringit",
            nplaces="3",
            potencia=50
        )
        self.estacio4.tipus_velocitat.add(self.velocitat_rapida)
        self.estacio4.tipus_velocitat.add(self.velocitat_ultra)
        self.estacio4.tipus_carregador.add(self.carregador_tipus2)
        self.estacio4.tipus_carregador.add(self.carregador_ccs)
    
    # Tests para filtrar_per_potencia
    
    def test_filtrar_per_potencia_min(self):
        """Test para filtrar estaciones por potencia mínima"""
        url = reverse('filtrar_per_potencia') + '?min=20'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Estaciones 2, 3 y 4
        
        # Verificar que solo se incluyen estaciones con potencia >= 20
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_3', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
    
    def test_filtrar_per_potencia_max(self):
        """Test para filtrar estaciones por potencia máxima"""
        url = reverse('filtrar_per_potencia') + '?max=50'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Estaciones 1, 2 y 4
        
        # Verificar que solo se incluyen estaciones con potencia <= 50
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_1', ids_estaciones)
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    def test_filtrar_per_potencia_rango(self):
        """Test para filtrar estaciones por rango de potencia"""
        url = reverse('filtrar_per_potencia') + '?min=20&max=100'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 2 y 4
        
        # Verificar que solo se incluyen estaciones con 20 <= potencia <= 100
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    def test_filtrar_per_potencia_parametro_invalido(self):
        """Test para verificar el manejo de parámetros inválidos"""
        url = reverse('filtrar_per_potencia') + '?min=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        url = reverse('filtrar_per_potencia') + '?max=xyz'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    # Tests para filtrar_per_velocitat
    
    def test_filtrar_per_velocitat_una(self):
        """Test para filtrar estaciones por un tipo de velocidad"""
        url = reverse('filtrar_per_velocitat') + f'?velocitat={self.velocitat_rapida.id_velocitat}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 2 y 4
        
        # Verificar que solo se incluyen estaciones con velocidad rápida
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    def test_filtrar_per_velocitat_multiples(self):
        """Test para filtrar estaciones por múltiples tipos de velocidad"""
        url = reverse('filtrar_per_velocitat') + f'?velocitat={self.velocitat_lenta.id_velocitat},{self.velocitat_ultra.id_velocitat}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Estaciones 1, 3 y 4
        
        # Verificar que se incluyen estaciones con velocidad lenta o ultra-rápida
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_1', ids_estaciones)
        self.assertIn('estacio_test_3', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_2', ids_estaciones)
    
    # Tests para filtrar_per_carregador
    
    def test_filtrar_per_carregador_uno(self):
        """Test para filtrar estaciones por un tipo de cargador"""
        url = reverse('filtrar_per_carregador') + f'?id={self.carregador_ccs.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 3 y 4
        
        # Verificar que solo se incluyen estaciones con cargador CCS
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_3', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_2', ids_estaciones)
    
    def test_filtrar_per_carregador_multiples(self):
        """Test para filtrar estaciones por múltiples tipos de cargador"""
        url = reverse('filtrar_per_carregador') + f'?id={self.carregador_tipus1.id_carregador},{self.carregador_tipus2.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)  # Estaciones 1, 2 y 4
        
        # Verificar que se incluyen estaciones con cargador tipo 1 o tipo 2
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_1', ids_estaciones)
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    # Tests para obtenir_opcions_filtres
    
    def test_obtenir_opcions_filtres(self):
        """Test para obtener las opciones disponibles para los filtros"""
        url = reverse('obtenir_opcions_filtres')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que la respuesta contiene las secciones esperadas
        self.assertIn('potencia', response.data)
        self.assertIn('velocitats', response.data)
        self.assertIn('carregadors', response.data)
        
        # Verificar los valores de potencia
        self.assertIn('min', response.data['potencia'])
        self.assertIn('max', response.data['potencia'])
        self.assertEqual(response.data['potencia']['min'], 7)  # Potencia mínima (estación 1)
        self.assertEqual(response.data['potencia']['max'], 150)  # Potencia máxima (estación 3)
        
        # Verificar las velocidades disponibles
        self.assertEqual(len(response.data['velocitats']), 3)
        velocitats = response.data['velocitats']
        self.assertIn(self.velocitat_lenta.id_velocitat, velocitats)
        self.assertIn(self.velocitat_rapida.id_velocitat, velocitats)
        self.assertIn(self.velocitat_ultra.id_velocitat, velocitats)
        
        # Verificar los cargadores disponibles
        self.assertEqual(len(response.data['carregadors']), 3)
        carregadors_ids = [c['id'] for c in response.data['carregadors']]
        self.assertIn(self.carregador_tipus1.id_carregador, carregadors_ids)
        self.assertIn(self.carregador_tipus2.id_carregador, carregadors_ids)
        self.assertIn(self.carregador_ccs.id_carregador, carregadors_ids)
    
    # Tests para filtrar_estacions (filtro combinado)
    
    def test_filtrar_estacions_potencia(self):
        """Test para filtrar estaciones por potencia usando filtrar_estacions"""
        url = reverse('filtrar_estacions') + '?potencia_min=20&potencia_max=100'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 2 y 4
        
        # Verificar que solo se incluyen estaciones con 20 <= potencia <= 100
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    def test_filtrar_estacions_velocitat(self):
        """Test para filtrar estaciones por velocidad usando filtrar_estacions"""
        url = reverse('filtrar_estacions') + f'?velocitat={self.velocitat_rapida.id_velocitat}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 2 y 4
        
        # Verificar que solo se incluyen estaciones con velocidad rápida
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
    
    def test_filtrar_estacions_tipus_carregador(self):
        """Test para filtrar estaciones por tipo de cargador usando filtrar_estacions"""
        url = reverse('filtrar_estacions') + f'?tipus_carregador={self.carregador_ccs.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 3 y 4
        
        # Verificar que solo se incluyen estaciones con cargador CCS
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_3', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_2', ids_estaciones)
    
    def test_filtrar_estacions_ciutat(self):
        """Test para filtrar estaciones por ciudad usando filtrar_estacions"""
        url = reverse('filtrar_estacions') + '?ciutat=Badalona'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Solo estación 3
        
        # Verificar que solo se incluye la estación de Badalona
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_3')
    
    def test_filtrar_estacions_combinado(self):
        """Test para filtrar estaciones usando múltiples criterios combinados"""
        # Filtrar por potencia mínima, velocidad y tipo de cargador
        url = reverse('filtrar_estacions') + f'?potencia_min=20&velocitat={self.velocitat_rapida.id_velocitat}&tipus_carregador={self.carregador_tipus2.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)  # Estaciones 2 y 4
        
        # Verificar que solo se incluyen las estaciones que cumplen todos los criterios
        ids_estaciones = [estacion['id_punt'] for estacion in response.data]
        self.assertIn('estacio_test_2', ids_estaciones)
        self.assertIn('estacio_test_4', ids_estaciones)
        self.assertNotIn('estacio_test_1', ids_estaciones)
        self.assertNotIn('estacio_test_3', ids_estaciones)
        
        # Añadir criterio de ciudad para filtrar aún más
        url += '&ciutat=Barcelona'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # Solo estación 2
        
        # Verificar que solo se incluye la estación que cumple todos los criterios
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_2')
    
    def test_filtrar_estacions_parametro_potencia_invalido(self):
        """Test para verificar el manejo de parámetros de potencia inválidos"""
        url = reverse('filtrar_estacions') + '?potencia_min=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        
        url = reverse('filtrar_estacions') + '?potencia_max=xyz'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_filtrar_estacions_sin_resultados(self):
        """Test para verificar el comportamiento cuando no hay resultados"""
        # Usar criterios que no coinciden con ninguna estación
        url = reverse('filtrar_estacions') + '?ciutat=Madrid'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No hay resultados
        
        # Combinar criterios que no coinciden con ninguna estación
        url = reverse('filtrar_estacions') + f'?potencia_min=200&velocitat={self.velocitat_lenta.id_velocitat}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)  # No hay resultados