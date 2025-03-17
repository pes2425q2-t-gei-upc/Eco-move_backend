from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UbicacioViewSet, PuntViewSet, EstacioCarregaViewSet, PuntCarregaViewSet, punt_mes_proper, \
    TipusCarregadorViewSet, crear_reserva, modificar_reserva, eliminar_reserva

router = DefaultRouter()
router.register(r'ubicacions', UbicacioViewSet)
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'punts_de_carrega', PuntCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
    path('reservar/', crear_reserva, name='crear_reserva'),
    path('reservas/<int:reserva_id>/modificar/', modificar_reserva, name='modificar_reserva'),
    path('reservas/<int:reserva_id>/eliminar/', eliminar_reserva, name='eliminar_reserva'),
]