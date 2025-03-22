'''
/api_punts_carrega/reservas/crear/
/api_punts_carrega/reservas/4/modificar/
/api_punts_carrega/reservas/3/eliminar/

'''





from django.test import TestCase, Client
from django.urls import reverse
from rest_framework import status
import json
from datetime import date, datetime, timedelta, time
from api_punts_carrega.models import EstacioCarrega, Reserva, Punt

class ReservaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        print("\n=== Configurando tests de Reserva ===")
        
        # Ya no necesitamos crear un objeto Ubicacio separado
        # Creamos directamente la EstacioCarrega con los campos de ubicación
        self.estacio = EstacioCarrega.objects.create(
            id_punt="12345",  # Ahora id_punt es la clave primaria
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Barcelona, 123",
            ciutat="Barcelona",
            provincia="Barcelona",
            gestio="Public",
            tipus_acces="targeta",
            nplaces="2",
        )
        print(f"✓ Estación creada: {self.estacio.id_punt} en {self.estacio.direccio}")
        
        self.reserva = Reserva.objects.create(
            estacion=self.estacio,
            fecha=date(2025, 3, 19),
            hora=time(10, 0),
            duracion=timedelta(hours=2)
        )
        print(f"✓ Reserva inicial creada: {self.reserva.pk} - {self.reserva.fecha} {self.reserva.hora}")
        
        # Definir los datos para crear una nueva reserva
        self.reserva_data = {
            "estacion": self.estacio.id_punt,  # Usamos id_punt como identificador
            "fecha": "2025-03-20",
            "hora": "14:00",
            "duracion": "03:00:00"
        }
        print("✓ Datos para nueva reserva preparados")
        
    def test_crear_reserva(self):
        url = reverse('reserva-crear')
        print(f"\n=== TEST: Crear Reserva ===")
        print(f"URL: {url}")
        print(f"Datos: {self.reserva_data}")
        
        response = self.client.post(
            url,
            data=json.dumps(self.reserva_data),
            content_type='application/json'
        )
        
        print(f"Código de estado: {response.status_code}")
        print(f"Respuesta: {response.content.decode()}")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Reserva.objects.count(), 2)
        
        # Verificar que la nueva reserva se creó correctamente
        nueva_reserva = Reserva.objects.exclude(pk=self.reserva.pk).first()
        self.assertEqual(nueva_reserva.fecha, date(2025, 3, 20))
        self.assertEqual(nueva_reserva.hora, time(14, 0))
        self.assertEqual(nueva_reserva.duracion, timedelta(hours=3))
        
        print(f"✓ Nueva reserva creada correctamente: {nueva_reserva.pk} - {nueva_reserva.fecha} {nueva_reserva.hora}")

    def test_modificar_reserva(self):
        modificar_data = {
            "fecha": "2025-03-20",
            "hora": "11:00",
            "duracion": "04:00:00"
        }
        
        url = reverse('reserva-modificar', kwargs={'pk': self.reserva.pk})
        print(f"\n=== TEST: Modificar Reserva ===")
        print(f"URL: {url}")
        print(f"Datos: {modificar_data}")
        
        response = self.client.put(
            url,
            data=json.dumps(modificar_data),
            content_type='application/json'
        )
        
        print(f"Código de estado: {response.status_code}")
        print(f"Respuesta: {response.content.decode()}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Recargar el objeto desde la base de datos
        self.reserva.refresh_from_db()
        
        # Verificar que los campos se actualizaron correctamente
        self.assertEqual(self.reserva.fecha, date(2025, 3, 20))
        self.assertEqual(self.reserva.hora, time(11, 0))
        self.assertEqual(self.reserva.duracion, timedelta(hours=4))
        
        print(f"✓ Reserva modificada correctamente: {self.reserva.pk} - {self.reserva.fecha} {self.reserva.hora}")

    def test_eliminar_reserva(self):
        url = reverse('reserva-eliminar', kwargs={'pk': self.reserva.pk})
        print(f"\n=== TEST: Eliminar Reserva ===")
        print(f"URL: {url}")
        
        response = self.client.delete(url)
        
        print(f"Código de estado: {response.status_code}")
        print(f"Respuesta: {response.content.decode()}")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Reserva.objects.count(), 0)
        
        print(f"✓ Reserva eliminada correctamente")