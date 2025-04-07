from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PuntViewSet,
    EstacioCarregaViewSet,
    punt_mes_proper,
    TipusCarregadorViewSet,
    ReservaViewSet, obtenir_preu_actual_kwh,
    PuntViewSet,
    EstacioCarregaViewSet,
    punt_mes_proper,
    TipusCarregadorViewSet,
    ReservaViewSet,
    VehicleViewSet,
    ModelCotxeViewSet,
)

router = DefaultRouter()
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)
router.register(r'reservas', ReservaViewSet)
router.register(r'vehicles', VehicleViewSet)
router.register(r'models', ModelCotxeViewSet)
urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
    path('api/preu_kwh/', obtenir_preu_actual_kwh, name='obtenir_preu_actual_kwh'),
]