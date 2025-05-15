from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva, Usuario, Vehicle, TipusCarregador
from rest_framework.authtoken.models import Token

class ReservaFiltradoAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = Usuario.objects.create_user(username='user1_filter', email='user1@filter.com', password='pw1')
        self.user2 = Usuario.objects.create_user(username='user2_filter', email='user2@filter.com', password='pw2')

        self.token_user1 = Token.objects.create(user=self.user1)
        self.auth_header_user1 = f'Token {self.token_user1.key}'

        # Crear tipo de cargador para los vehículos
        self.tipus_carregador = TipusCarregador.objects.create(id_carregador="TEST-CCS", nom_tipus="CCS", tipus_connector="CCS2", tipus_corrent="DC")
        
        # Crear vehículos con el nuevo modelo unificado
        vehiculo1 = Vehicle.objects.create(
            matricula="FIL1", 
            propietari=self.user1, 
            marca="FMarca", 
            model="FModel", 
            any_model=2024,
            carrega_actual=50, 
            capacitat_bateria=70
        )
        vehiculo1.tipus_carregador.add(self.tipus_carregador)
        
        vehiculo2 = Vehicle.objects.create(
            matricula="FIL2", 
            propietari=self.user2, 
            marca="FMarca", 
            model="FModel", 
            any_model=2024,
            carrega_actual=50, 
            capacitat_bateria=70
        )
        vehiculo2.tipus_carregador.add(self.tipus_carregador)
        
        estacio = EstacioCarrega.objects.create(id_punt="TESTFIL", lat=41.1, lng=2.2, nplaces="2", gestio="Test", tipus_acces="Test")
        estacio.tipus_carregador.add(self.tipus_carregador)

        self.reserva_u1_d19 = Reserva.objects.create(usuario=self.user1, estacion=estacio, fecha=date(2025, 3, 19), hora=time(10, 0), duracion=timedelta(hours=1), vehicle=vehiculo1)
        self.reserva_u1_d20 = Reserva.objects.create(usuario=self.user1, estacion=estacio, fecha=date(2025, 3, 20), hora=time(11, 0), duracion=timedelta(hours=1), vehicle=vehiculo1)
        self.reserva_u2_d19 = Reserva.objects.create(usuario=self.user2, estacion=estacio, fecha=date(2025, 3, 19), hora=time(14, 0), duracion=timedelta(hours=1), vehicle=vehiculo2)

        self.list_url = reverse('reserva-list')

    def test_filtrar_reservas_por_dia_existente_usuario_correcto(self):
        fecha_filtro = "19/03/2025"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro}"
        response = self.client.get(url_con_filtro, HTTP_AUTHORIZATION=self.auth_header_user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.reserva_u1_d19.id)

    def test_filtrar_reservas_por_dia_existente_usuario_incorrecto(self):
        token_user2 = Token.objects.create(user=self.user2)
        auth_header_user2 = f'Token {token_user2.key}'
        fecha_filtro = "20/03/2025"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro}"
        response = self.client.get(url_con_filtro, HTTP_AUTHORIZATION=auth_header_user2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filtrar_reservas_por_dia_inexistente(self):
        fecha_filtro = "21/03/2025"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro}"
        response = self.client.get(url_con_filtro, HTTP_AUTHORIZATION=self.auth_header_user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_filtrar_reservas_formato_dia_invalido(self):
        fecha_filtro_invalida = "2025-03-19"
        url_con_filtro = f"{self.list_url}?dia={fecha_filtro_invalida}"
        response = self.client.get(url_con_filtro, HTTP_AUTHORIZATION=self.auth_header_user1)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        ids_devueltos = {r['id'] for r in response.data}
        self.assertEqual(ids_devueltos, {self.reserva_u1_d19.id, self.reserva_u1_d20.id})

    def test_listar_reservas_sin_autenticar_falla(self):
        response = self.client.get(self.list_url)
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
