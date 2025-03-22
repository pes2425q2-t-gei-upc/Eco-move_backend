from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PuntViewSet, 
    EstacioCarregaViewSet, 
    PuntCarregaViewSet, 
    punt_mes_proper, 
    TipusCarregadorViewSet, 
    ReservaViewSet,
    tots_els_punts
)

router = DefaultRouter()
router.register(r'punts', PuntViewSet)
router.register(r'estacions', EstacioCarregaViewSet)
router.register(r'punts_de_carrega', PuntCarregaViewSet)
router.register(r'tipus_carregador', TipusCarregadorViewSet)
router.register(r'reservas', ReservaViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('punt_mes_proper/', punt_mes_proper, name='punt_mes_proper'),
    path('tots_els_punts/', tots_els_punts, name='tots_els_punts'),
]