from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from api_punts_carrega.models import Usuario, EstacioCarrega, ReporteEstacion, TipoErrorEstacion

class ReporteEstacionAPITests(APITestCase):
    def setUp(self):
        self.user1 = Usuario.objects.create_user(
            username='reporter_user1',
            email='reporter1@example.com',
            password='password123'
        )
        self.user1.dni = 'TESTDNI001R'
        self.user1.save()

        self.token1 = Token.objects.create(user=self.user1)
        self.auth_header1 = f'Token {self.token1.key}'

        self.other_user = Usuario.objects.create_user(
            username='other_user_report',
            email='other_report@example.com',
            password='password123'
        )
        self.other_user.dni = 'TESTDNI002S'
        self.other_user.save()

        self.estacion1 = EstacioCarrega.objects.create(
            id_punt="REP-EST-001",
            lat=41.123, lng=2.123,
            nplaces="2",
            gestio="TestGestReport", tipus_acces="TestAccReport"
        )
        from django.urls.exceptions import NoReverseMatch
        try:
            self.report_url_estacion1 = reverse('estacion-reportar-error', kwargs={'pk': self.estacion1.pk})
        except NoReverseMatch:
            self.report_url_estacion1 = reverse('estaciocarrega-reportar-error', kwargs={'pk': self.estacion1.pk})
    def test_crear_reporte_exitoso(self):
        data = {
            "tipo_error": TipoErrorEstacion.NO_FUNCIONA,
            "comentario_usuario": "La estación no suministra energía al conectar el vehículo."
        }
        response = self.client.post(self.report_url_estacion1, data, format='json', HTTP_AUTHORIZATION=self.auth_header1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(ReporteEstacion.objects.count(), 1)
        reporte = ReporteEstacion.objects.first()
        self.assertEqual(reporte.usuario_reporta, self.user1)
        self.assertEqual(reporte.estacion, self.estacion1)
        self.assertEqual(reporte.tipo_error, TipoErrorEstacion.NO_FUNCIONA)
        self.assertEqual(reporte.comentario_usuario, data['comentario_usuario'])
        self.assertEqual(reporte.estado, 'ABIERTO')
        self.assertIn('id', response.data)

    def test_crear_reporte_sin_comentario_opcional(self):
        data = {
            "tipo_error": TipoErrorEstacion.PANTALLA_APAGADA
        }
        response = self.client.post(self.report_url_estacion1, data, format='json', HTTP_AUTHORIZATION=self.auth_header1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.content)
        self.assertEqual(ReporteEstacion.objects.count(), 1)
        reporte = ReporteEstacion.objects.first()
        self.assertEqual(reporte.tipo_error, TipoErrorEstacion.PANTALLA_APAGADA)
        self.assertTrue(reporte.comentario_usuario is None or reporte.comentario_usuario == "")

    def test_crear_reporte_no_autenticado_falla(self):
        data = {
            "tipo_error": TipoErrorEstacion.NO_FUNCIONA,
            "comentario_usuario": "Intento anónimo."
        }
        response = self.client.post(self.report_url_estacion1, data, format='json')
        self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
        self.assertEqual(ReporteEstacion.objects.count(), 0)

    def test_crear_reporte_sin_tipo_error_falla(self):
        data = {
            "comentario_usuario": "Olvidé el tipo de error."
        }
        response = self.client.post(self.report_url_estacion1, data, format='json', HTTP_AUTHORIZATION=self.auth_header1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertIn('tipo_error', response.data)
        self.assertEqual(ReporteEstacion.objects.count(), 0)

    def test_crear_reporte_tipo_error_invalido_falla(self):
        data = {
            "tipo_error": "ESTO_NO_ES_UN_TIPO_VALIDO",
            "comentario_usuario": "Error inventado."
        }
        response = self.client.post(self.report_url_estacion1, data, format='json', HTTP_AUTHORIZATION=self.auth_header1)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST, response.content)
        self.assertIn('tipo_error', response.data)
        self.assertEqual(ReporteEstacion.objects.count(), 0)

        url_estacion_inexistente = ""
        from django.urls.exceptions import NoReverseMatch
        try:
            url_estacion_inexistente = reverse('estacion-reportar-error', kwargs={'pk': "ID_FANTASMA"})
        except NoReverseMatch:
            url_estacion_inexistente = reverse('estaciocarrega-reportar-error', kwargs={'pk': "ID_FANTASMA"})
            url_estacion_inexistente = reverse('estaciocarrega-reportar-error', kwargs={'pk': "ID_FANTASMA"})

        data = {
            "tipo_error": TipoErrorEstacion.NO_FUNCIONA,
            "comentario_usuario": "Reportando estación fantasma."
        }
        response = self.client.post(url_estacion_inexistente, data, format='json', HTTP_AUTHORIZATION=self.auth_header1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, response.content)
        self.assertEqual(ReporteEstacion.objects.count(), 0)
