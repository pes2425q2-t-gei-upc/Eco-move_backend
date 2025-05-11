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
    RefugioClimaticoViewSet,
    sincronizar_refugios,
    refugios_mas_cercanos,
    filtrar_per_potencia,
    filtrar_per_velocitat,
    filtrar_per_carregador,
    obtenir_opcions_filtres,
    filtrar_estacions,
    UsuarioViewSet,
    ValoracionEstacionViewSet,
    TextItemViewSet,
)

router = DefaultRouter()
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'refugios', RefugioClimaticoViewSet)
router.register(r'usuari', UsuarioViewSet)
router.register(r'valoraciones_estaciones', ValoracionEstacionViewSet)
router.register(r'text_items', TextItemViewSet, basename='textitem')

urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
    path('preu_kwh/', obtenir_preu_actual_kwh, name='obtenir_preu_actual_kwh'),
    path('sincronizar_refugios/', sincronizar_refugios, name='sincronizar_refugios'),
    path('refugios_mas_cercanos/', refugios_mas_cercanos, name='refugios_mas_cercanos'),
    path('filtrar_per_potencia/', filtrar_per_potencia, name='filtrar_per_potencia'),
    path('filtrar_per_velocitat/', filtrar_per_velocitat, name='filtrar_per_velocitat'),
    path('filtrar_per_carregador/', filtrar_per_carregador, name='filtrar_per_carregador'),
    path('opcions_filtres/', obtenir_opcions_filtres, name='obtenir_opcions_filtres'),
    path('filtrar_estacions/', filtrar_estacions, name='filtrar_estacions'),
    path('estacions/<str:estacion_id>/valoraciones/', ValoracionEstacionViewSet.as_view({'get': 'list', 'post': 'create'}), name='estacion-valoraciones'),
]