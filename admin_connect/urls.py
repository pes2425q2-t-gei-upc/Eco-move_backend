from django.urls import path
from . import admin_views

app_name = 'admin_connect'

urlpatterns = [
    # Vista para el dashboard de administración
    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Vista para sincronizar refugios
    path('refugios/sync/', admin_views.sincronizar_refugios_admin, name='sincronizar_refugios'),

    # Vista para gestionar usuarios
    path('usuarios/', admin_views.gestionar_usuarios, name='gestionar_usuarios'),

    # Vista para editar un usuario específico
    path('usuarios/editar/<int:usuario_id>/', admin_views.editar_usuario, name='editar_usuario'),

    # Vista para modificar puntos de usuario
    path('usuarios/modificar_puntos/<int:usuario_id>/', admin_views.modificar_puntos_usuario, name='modificar_puntos_usuario'),

    # Vista para las estadísticas de las estaciones
    path('estadisticas/estaciones/', admin_views.estadisticas_estaciones, name='estadisticas_estaciones'),
    
    # Aquí puedes añadir más URLs si necesitas
]
