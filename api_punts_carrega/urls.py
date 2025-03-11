from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UbicacioViewSet, PuntViewSet,EstacioCarregaViewSet, PuntCarregaViewSet, punt_mes_proper,TipusCarregadorViewSet


router = DefaultRouter()
router.register(r'ubicacions', UbicacioViewSet)
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'punts_de_carrega', PuntCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
]