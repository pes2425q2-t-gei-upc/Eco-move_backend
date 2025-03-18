from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from api_punts_carrega.models import EstacioCarrega, Reserva, Ubicacio
from django.utils.timezone import now, timedelta

class ReservationAPITestCase(APITestCase):
    def setUp(self):
        """Set up test users and reservation"""
        #TODO: change this test when we have made users users
        # Regular user
        self.user = User.objects.create_user(username="testuser", password="testpass")
        
        # User with admin access - superuser
        self.admin_user = User.objects.create_superuser(username="superuser", password="testpass2")
        
        self.uubicacio = Ubicacio.objects.create(
            id_ubicacio="loc_001",
            lat=41.3851,
            lng=2.1734,
            direccio="Carrer de Barcelona, 123",
            ciutat="Barcelona",
            provincia="Barcelona"
        )
        
        self.charging_station = EstacioCarrega.objects.create(
            id_estacio="12345",
            gestio="Public",
            tipus_acces="targeta",
            ubicacio_estacio = self.uubicacio,
            nplaces="2",
        )

        self.reservation_user = Reserva.objects.create(
            user=self.user,
            estacio_carrega=self.charging_station,
            hora_inici=now() + timedelta(hours=1),
            hora_fi=now() + timedelta(hours=2),
        )
        
        self.reservation_admin = Reserva.objects.create(
            user=self.admin_user,
            estacio_carrega=self.charging_station,
            hora_inici=now() + timedelta(hours=3),
            hora_fi=now() + timedelta(hours=4),
        )

        self.reservation_url = "/api_punts_carrega/reservas/"
        
    # TODO: Add tests for creating, updating and deleting reservations
    # TODO: Remove comments when the users are made
    
    def test_get_all_reservations(self):
        """Test if you get all the reservations"""
        response = self.client.get(self.reservation_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
    
    # def test_admin_get_all_reservations(self):
    #     """Test if an admin user can get all the reservations"""
    #     self.client.login(username="superuser", password="testpass2")
    #     response = self.client.get(self.reservation_url)
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response.data), 2)

    # def test_get_reservations(self):
    #     """Test if a user can retrieve their reservations"""
    #     self.client.login(username="testuser", password="testpass")
    #     response = self.client.get(self.reservation_url)
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response.data), 1)
    #     self.assertEqual(response.data[0]["estacio_carrega"], self.charging_station.id_estacio)

    # def test_get_reservations_empty(self):
    #     """Test if a user with no reservations gets an empty list"""
    #     new_user = User.objects.create_user(username="newuser", password="newpass")
    #     self.client.login(username="newuser", password="newpass")
    #     response = self.client.get(self.reservation_url)
        
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(len(response.data), 0)

    # def test_unauthorized_user_cannot_access_reservations(self):
    #     """Test that an unauthenticated user cannot access reservations"""
    #     self.client.logout()  # Make sure no user is logged in
    #     response = self.client.get(self.reservation_url)
    #     self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)  # Or 401 if using Token Auth    
    
    def test_get_reservation_by_id(self):
        """Test if a user can retrieve a reservation by its ID"""
        # self.client.login(username="testuser", password="testpass")
        response = self.client.get(f"{self.reservation_url}{self.reservation_user.id}/")
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["estacio_carrega"], self.charging_station.id_estacio)
