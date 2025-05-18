from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EstacionBiciLiteViewSet, forzar_importar_estaciones, forzar_actualizar_disponibilidad, ReservaBiciViewSet

router = DefaultRouter()
router.register(r'estaciones', EstacionBiciLiteViewSet)
router.register(r'reservas', ReservaBiciViewSet, basename='reserva-bici')

urlpatterns = [
    path('estaciones/forzar-importar/', forzar_importar_estaciones),
    path('estaciones/forzar-actualizar/', forzar_actualizar_disponibilidad),
    path('', include(router.urls)),
]
