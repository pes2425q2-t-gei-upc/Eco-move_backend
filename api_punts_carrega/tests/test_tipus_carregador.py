from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from api_punts_carrega.models import TipusCarregador, EstacioCarrega, Vehicle

class TestTipusCarregador(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.tipus_carregador = TipusCarregador.objects.create(
            id_carregador="tipus_test_1",
            nom_tipus="Carregador Test",
            tipus_connector="Connector Test",
            tipus_corrent="Corrent alterna"
        )
        self.tipus_carregador_url = reverse('tipuscarregador-detail', args=[self.tipus_carregador.id_carregador])
        self.tipus_carregadors_url = reverse('tipuscarregador-list')

    def test_obtenir_tipus_carregador(self):
        response = self.client.get(self.tipus_carregador_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id_carregador'], self.tipus_carregador.id_carregador)
        self.assertEqual(response.data['nom_tipus'], self.tipus_carregador.nom_tipus)
        self.assertEqual(response.data['tipus_connector'], self.tipus_carregador.tipus_connector)
        self.assertEqual(response.data['tipus_corrent'], self.tipus_carregador.tipus_corrent)

    def test_llistar_tipus_carregadors(self):
        response = self.client.get(self.tipus_carregadors_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_crear_tipus_carregador(self):
        data = {
            'id_carregador': 'tipus_test_2',
            'nom_tipus': 'Carregador Nou',
            'tipus_connector': 'Connector Nou',
            'tipus_corrent': 'Corrent continua'
        }
        response = self.client.post(self.tipus_carregadors_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(TipusCarregador.objects.count(), 2)
        self.assertEqual(TipusCarregador.objects.get(id_carregador='tipus_test_2').nom_tipus, 'Carregador Nou')

    def test_actualitzar_tipus_carregador(self):
        data = {
            'nom_tipus': 'Carregador Actualitzat',
            'tipus_connector': 'Connector Actualitzat'
        }
        response = self.client.patch(self.tipus_carregador_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.tipus_carregador.refresh_from_db()
        self.assertEqual(self.tipus_carregador.nom_tipus, 'Carregador Actualitzat')
        self.assertEqual(self.tipus_carregador.tipus_connector, 'Connector Actualitzat')

    def test_eliminar_tipus_carregador(self):
        response = self.client.delete(self.tipus_carregador_url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(TipusCarregador.objects.count(), 0)

    def test_filtrar_estacions_per_carregador(self):
        estacio = EstacioCarrega.objects.create(
            id_punt="estacio_test_1",
            lat=41.3851,
            lng=2.1734,
            gestio="Pública",
            tipus_acces="Lliure"
        )
        estacio.tipus_carregador.add(self.tipus_carregador)

        tipus_carregador2 = TipusCarregador.objects.create(
            id_carregador="tipus_test_2",
            nom_tipus="Carregador Test 2",
            tipus_connector="Connector Test 2",
            tipus_corrent="Corrent continua"
        )
        estacio2 = EstacioCarrega.objects.create(
            id_punt="estacio_test_2",
            lat=41.4036,
            lng=2.1744,
            gestio="Privada",
            tipus_acces="Restringit"
        )
        estacio2.tipus_carregador.add(tipus_carregador2)

        url = reverse('filtrar_per_carregador') + f'?id={self.tipus_carregador.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_1')

        url = reverse('filtrar_per_carregador') + f'?id={tipus_carregador2.id_carregador}'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id_punt'], 'estacio_test_2')

def test_compatibilitat_model_cotxe_carregador(self):
        vehicle = Vehicle.objects.create(
            matricula="TEST123",
            marca="Marca Test",
            model="Model Test",
            any_model=2023,
            carrega_actual=50.0,
            capacitat_bateria=70.0
        )
        vehicle.tipus_carregador.add(self.tipus_carregador)

        self.assertEqual(vehicle.tipus_carregador.count(), 1)
        self.assertEqual(vehicle.tipus_carregador.first().id_carregador, self.tipus_carregador.id_carregador)

        self.assertEqual(self.tipus_carregador.tipus_carregador.count(), 1)
        self.assertEqual(self.tipus_carregador.tipus_carregador.first().matricula, "TEST123")