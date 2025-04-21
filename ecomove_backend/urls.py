from django.contrib import admin
from django.urls import include, path
from api_punts_carrega.views_social import GoogleLogin
from rest_framework_simplejwt.views import TokenRefreshView
from api_punts_carrega.token import CustomTokenObtainPairView 


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api_punts_carrega/', include('api_punts_carrega.urls')),
    path('api/social/', include('social_community.urls')),
    path('api-auth/', include('rest_framework.urls')),

    path('api/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/auth/social/google/', GoogleLogin.as_view(), name='google_login'),
    path('api/auth/social/', include('allauth.socialaccount.urls')),
]