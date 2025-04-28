"""
URL configuration for ecomove_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from api_punts_carrega.views import RegisterView, MeView, PerfilPublicoViewSet
from api_punts_carrega import admin_views

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('adminn/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('adminn/refugios/', admin_views.sincronizar_refugios_admin, name='admin_refugios'),
    path('adminn/usuarios/', admin_views.gestionar_usuarios, name='gestionar_usuarios'),
    path('adminn/usuarios/<int:usuario_id>/editar/', admin_views.editar_usuario, name='editar_usuario'),
    path('adminn/usuarios/<int:usuario_id>/puntos/', admin_views.modificar_puntos_usuario, name='modificar_puntos_usuario'),
    path('adminn/estadisticas/estaciones/', admin_views.estadisticas_estaciones, name='estadisticas_estaciones'),


    path('api_punts_carrega/', include('api_punts_carrega.urls')),
    path('api/social/', include('social_community.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('social/', include('social_community.urls')),

    #gestion usuario
    path('me/', MeView.as_view(), name='me'),
    path('profile/<str:username>/', PerfilPublicoViewSet.as_view({'get': 'retrieve'}), name='perfil-publico'),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]