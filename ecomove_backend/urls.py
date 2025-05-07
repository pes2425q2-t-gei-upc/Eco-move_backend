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
from api_punts_carrega.views import RegisterView, MeView, PerfilPublicoViewSet, PerfilFotoView
from admin_connect import admin_views
from api_punts_carrega.views_social_login import GoogleLogin

urlpatterns = [
    path('admin/', admin.site.urls),

    path('admin_connect/', include('admin_connect.urls')),

    path('api_punts_carrega/', include('api_punts_carrega.urls')),
    path('api/social/', include('social_community.urls')),
    path('api-auth/', include('rest_framework.urls')),
    path('social/', include('social_community.urls')),

    path('me/', MeView.as_view(), name='me'),
    path('profile/foto/', PerfilFotoView.as_view(), name='perfil-foto'),
    path('profile/<str:username>/',
         PerfilPublicoViewSet.as_view({'get': 'retrieve'}),
         name='perfil-publico'),
    path('register/', RegisterView.as_view(), name='register'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #login social
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/', include('allauth.socialaccount.urls')),
    path('auth/social/google/', GoogleLogin.as_view(), name='google_login'),

]