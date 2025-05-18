import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date
import json

# --- Simulación / Importación de dependencias ---
try:
    from rest_framework.response import Response
    from rest_framework import status
    # Importa APIRequestFactory
    from rest_framework.test import APIRequestFactory
except ImportError:
    # Simulación básica si DRF no está instalado (solo para referencia)
    class Response:
        def __init__(self, data, status):
            self.data = data
            self.status_code = status
            self.status = status
    class StatusMock:
        HTTP_200_OK = 200
        HTTP_404_NOT_FOUND = 404
        HTTP_500_INTERNAL_SERVER_ERROR = 500
        HTTP_503_SERVICE_UNAVAILABLE = 503
        HTTP_504_GATEWAY_TIMEOUT = 504
    status = StatusMock()
    class APIRequestFactory: # Simulación muy básica
        def get(self, path):
            # En un entorno real, esto devolvería un HttpRequest
            # Para la simulación, un mock puede bastar si no se usa DRF completo
            print("ADVERTENCIA: Usando APIRequestFactory simulada.")
            return MagicMock() # O una clase HttpRequest simulada si es necesario


try:
    import requests
except ImportError:
    class RequestsMock:
        class RequestException(Exception): pass
        class Timeout(RequestException): pass
        class HTTPError(RequestException):
            def __init__(self, *args, response=None, **kwargs):
                super().__init__(*args, **kwargs)
                self.response = response
    requests = RequestsMock()

# --- Importa tu función desde la ubicación correcta ---
try:
    from api_punts_carrega.views import obtenir_preu_actual_kwh
except ImportError:
    print("ADVERTENCIA: No se pudo importar 'obtenir_preu_actual_kwh' desde 'api_punts_carrega.views'.")
    def obtenir_preu_actual_kwh(request):
        return Response({"error": "Función no implementada localmente"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# --- Clase de Tests ---
class ObtenirPreuActualKwhTests(unittest.TestCase):

    # --- Método _get_mock_request CORREGIDO ---
    def _get_mock_request(self):
        factory = APIRequestFactory()
        # Puedes ajustar la URL si tu vista depende de ella
        request = factory.get('/api/preu-kwh/')
        return request

    @patch('api_punts_carrega.views.requests.get')
    def test_obtenir_preu_success(self, mock_requests_get):
        # ... (resto del código del test sin cambios) ...
        mock_api_response_data = { "data": { "type": "Precio mercado spot diario", "id": "datos-mercados-precios-mercados-tiempo-real", "attributes": {"title": "Precio mercado spot diario", "last-update": "2023-10-27T15:20:00+02:00", "description": None}, "meta": {"cache-expire-date": "2023-10-27T15:25:00+02:00"} }, "included": [ { "type": "Precios mercado spot (€/MWh)", "id": "10210", "groupId": None, "attributes": { "title": "PVPC (€/MWh)", "description": None, "color": "#00447e", "type": None, "magnitude": None, "composite": False, "step": False, "values": [ {"value": 100.50, "percentage": 0.345, "datetime": "2023-10-27T00:00:00+02:00"}, {"value": 95.20, "percentage": 0.335, "datetime": "2023-10-27T01:00:00+02:00"}, {"value": None, "percentage": 0.335, "datetime": "2023-10-27T02:00:00+02:00"}, {"value": 98.0, "percentage": 0.335, "datetime": None}, ] } } ] }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_data
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        # --- Se usa el request creado por la factory ---
        request_obj = self._get_mock_request()
        response = obtenir_preu_actual_kwh(request_obj)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['unidad'], '€/kWh')
        self.assertEqual(response.data['fuente'], 'Red Eléctrica de España (REE)')
        self.assertIn('fecha', response.data)
        self.assertIsInstance(response.data['precios_hoy'], list)
        self.assertEqual(len(response.data['precios_hoy']), 2)
        precio_hora_1 = response.data['precios_hoy'][0]
        self.assertEqual(precio_hora_1['hora'], '00:00')
        self.assertAlmostEqual(precio_hora_1['precio_kwh'], 100.50 / 1000, places=5)
        precio_hora_2 = response.data['precios_hoy'][1]
        self.assertEqual(precio_hora_2['hora'], '01:00')
        self.assertAlmostEqual(precio_hora_2['precio_kwh'], 95.20 / 1000, places=5)
        mock_requests_get.assert_called_once()


    @patch('api_punts_carrega.views.requests.get')
    def test_obtenir_preu_api_http_error(self, mock_requests_get):
        # ... (resto del código del test sin cambios) ...
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.json.return_value = {"errors": [{"status": "404", "code": "REE-123", "detail": "Recurso no encontrado"}]}
        http_error = requests.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_requests_get.return_value = mock_response

        # --- Se usa el request creado por la factory ---
        request_obj = self._get_mock_request()
        response = obtenir_preu_actual_kwh(request_obj)

        self.assertEqual(response.status_code, 404)
        self.assertIn('error', response.data)
        self.assertIn("Error al obtener datos de REE: Recurso no encontrado", response.data['error'])


    @patch('api_punts_carrega.views.requests.get')
    def test_obtenir_preu_api_timeout(self, mock_requests_get):
        # ... (resto del código del test sin cambios) ...
        mock_requests_get.side_effect = requests.Timeout("Tiempo de espera agotado")

        # --- Se usa el request creado por la factory ---
        request_obj = self._get_mock_request()
        response = obtenir_preu_actual_kwh(request_obj)

        self.assertEqual(response.status_code, status.HTTP_504_GATEWAY_TIMEOUT)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Timeout conectando con API REE") # <-- Cambiado


    @patch('api_punts_carrega.views.requests.get')
    def test_obtenir_preu_api_no_relevant_data(self, mock_requests_get):
        # ... (resto del código del test sin cambios) ...
        mock_api_response_data = { "data": {}, "included": [] }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_api_response_data
        mock_response.raise_for_status.return_value = None
        mock_requests_get.return_value = mock_response

        # --- Se usa el request creado por la factory ---
        request_obj = self._get_mock_request()
        response = obtenir_preu_actual_kwh(request_obj)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "No se encontraron datos horarios en la respuesta de la API REE")
# --- Ejecutar los tests ---
if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)