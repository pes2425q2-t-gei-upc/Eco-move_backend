from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api_punts_carrega.models import Punt, EstacioCarrega, TipusCarregador, TipusVelocitat

class TestPunt(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.punt = Punt.objects.create(
            id_punt="test_punt_1",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Test, 123",
            ciutat="Barcelona",
            provincia="Barcelona"
        )
        self.punt_url = reverse('punt-detail', args=[self.punt.id_punt])
        self.punts_url = reverse('punt-list')

    def test_obtenir_punt(self):
        response = self.client.get(self.punt_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_punt'], self.punt.id_punt)
        self.assertEqual(response.data['lat'], self.punt.lat)
        self.assertEqual(response.data['lng'], self.punt.lng)

    def test_llistar_punts(self):
        response = self.client.get(self.punts_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_crear_punt(self):
        data = {
            'id_punt': 'test_punt_2',
            'lat': 41.4036,
            'lng': 2.1744,
            'direccio': 'Carrer de Prova, 456',
            'ciutat': 'Barcelona',
            'provincia': 'Barcelona'
        }
        response = self.client.post(self.punts_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Punt.objects.count(), 2)
        self.assertEqual(Punt.objects.get(id_punt='test_punt_2').ciutat, 'Barcelona')

    def test_actualitzar_punt(self):
        data = {
            'direccio': 'Nova Direcció, 789',
            'ciutat': 'Girona'
        }
        response = self.client.patch(self.punt_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.punt.refresh_from_db()
        self.assertEqual(self.punt.direccio, 'Nova Direcció, 789')
        self.assertEqual(self.punt.ciutat, 'Girona')

    def test_eliminar_punt(self):
        response = self.client.delete(self.punt_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Punt.objects.count(), 0)


class TestEstacioCarrega(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tipus_velocitat = TipusVelocitat.objects.create(
            id_velocitat="rapida",
            nom_velocitat="Càrrega ràpida"
        )
        self.tipus_carregador = TipusCarregador.objects.create(
            id_carregador="tipus_test",
            nom_tipus="Carregador Test",
            tipus_connector="Connector Test",
            tipus_corrent="Corrent alterna"
        )
        self.estacio = EstacioCarrega.objects.create(
            id_punt="estacio_test_1",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Test, 123",
            ciutat="Barcelona",
            provincia="Barcelona",
            gestio="Pública",
            tipus_acces="Lliure",
            nplaces="2",
            potencia=50
        )
        self.estacio.tipus_velocitat.add(self.tipus_velocitat)
        self.estacio.tipus_carregador.add(self.tipus_carregador)
        self.estacio_url = reverse('estaciocarrega-detail', args=[self.estacio.id_punt])
        self.estacions_url = reverse('estaciocarrega-list')

    def test_obtenir_estacio(self):
        response = self.client.get(self.estacio_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_punt'], self.estacio.id_punt)
        self.assertEqual(response.data['potencia'], self.estacio.potencia)
        self.assertEqual(response.data['nplaces'], self.estacio.nplaces)

    def test_llistar_estacions(self):
        response = self.client.get(self.estacions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_crear_estacio(self):
        data = {
            'id_punt': 'estacio_test_2',
            'lat': 41.4036,
            'lng': 2.1744,
            'direccio': 'Carrer de Prova, 456',
            'ciutat': 'Barcelona',
            'provincia': 'Barcelona',
            'gestio': 'Privada',
            'tipus_acces': 'Restringit',
            'nplaces': '4',
            'potencia': 150,
            'tipus_velocitat': [self.tipus_velocitat.id_velocitat],
            'tipus_carregador': [self.tipus_carregador.id_carregador]
        }
        response = self.client.post(self.estacions_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(EstacioCarrega.objects.count(), 2)
        self.assertEqual(EstacioCarrega.objects.get(id_punt='estacio_test_2').potencia, 150)

    def test_actualitzar_estacio(self):
        data = {
            'potencia': 75,
            'nplaces': '3'
        }
        response = self.client.patch(self.estacio_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.estacio.refresh_from_db()
        self.assertEqual(self.estacio.potencia, 75)
        self.assertEqual(self.estacio.nplaces, '3')

    def test_eliminar_estacio(self):
        response = self.client.delete(self.estacio_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(EstacioCarrega.objects.count(), 0)

    def test_filtrar_per_potencia(self):
        EstacioCarrega.objects.create(
            id_punt="estacio_test_3",
            lat=41.4036,
            lng=2.1744,
            gestio="Pública",
            tipus_acces="Lliure",
            potencia=25
        )
        url = reverse('filtrar_per_potencia') + '?min=30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_1')

        url = reverse('filtrar_per_potencia') + '?max=30'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_3')

    def test_punt_mes_proper(self):
        EstacioCarrega.objects.create(
            id_punt="estacio_test_propera_1",
            lat=41.3855,
            lng=2.1736,
            gestio="Pública",
            tipus_acces="Lliure",
            potencia=25
        )
        EstacioCarrega.objects.create(
            id_punt="estacio_test_propera_2",
            lat=1.3855,
            lng=2.1736,
            gestio="Pública",
            tipus_acces="Lliure",
            potencia=50
        )

        url = reverse('punt_mes_proper') + '?lat=41.3856&lng=2.1737'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['estacio_carrega']['id_punt'], 'estacio_test_propera_1')
    
    
    def test_punt_mes_proper_sin_parametros(self):
        """Test para verificar que se requieren los parámetros lat y lng"""
        # Sin parámetros
        url = reverse('punt_mes_proper')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Se requieren los parámetros', response.data['error'])
        
        # Solo con lat
        url = reverse('punt_mes_proper') + '?lat=41.3856'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Se requieren los parámetros', response.data['error'])
        
        # Solo con lng
        url = reverse('punt_mes_proper') + '?lng=2.1737'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('Se requieren los parámetros', response.data['error'])
    
    def test_punt_mes_proper_parametros_no_numericos(self):
        """Test para verificar que los parámetros lat y lng deben ser numéricos"""
        # lat no numérico
        url = reverse('punt_mes_proper') + '?lat=abc&lng=2.1737'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('no son numeros', response.data['error'])
        
        # lng no numérico
        url = reverse('punt_mes_proper') + '?lat=41.3856&lng=abc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('no son numeros', response.data['error'])
        
        # ambos no numéricos
        url = reverse('punt_mes_proper') + '?lat=abc&lng=def'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertIn('no son numeros', response.data['error'])
