from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PuntViewSet,
    EstacioCarregaViewSet,
    punt_mes_proper,
    TipusCarregadorViewSet,
    ReservaViewSet, 
    obtenir_preu_actual_kwh,
    VehicleViewSet,
    ModelCotxeViewSet,
    RefugioClimaticoViewSet,
    sincronizar_refugios,
    refugios_mas_cercanos,
    PuntEmergenciaViewSet,
    filtrar_per_potencia,
    filtrar_per_velocitat,
    filtrar_per_carregador,
)

router = DefaultRouter()
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'models', ModelCotxeViewSet)
router.register(r'refugios', RefugioClimaticoViewSet)
router.register(r'punts_emergencia', PuntEmergenciaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
    path('preu_kwh/', obtenir_preu_actual_kwh, name='obtenir_preu_actual_kwh'),
    path('sincronizar_refugios/', sincronizar_refugios, name='sincronizar_refugios'),
    path('refugios_mas_cercanos/', refugios_mas_cercanos, name='refugios_mas_cercanos'),
    path('filtrar_per_potencia/', filtrar_per_potencia, name='filtrar_per_potencia'),
    path('filtrar_per_velocitat/', filtrar_per_velocitat, name='filtrar_per_velocitat'),
    path('filtrar_per_carregador/', filtrar_per_carregador, name='filtrar_per_carregador'),
]