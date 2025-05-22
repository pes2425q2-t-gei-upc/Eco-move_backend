from django.urls import path
from django.shortcuts import redirect
from . import admin_views

app_name = 'admin_connect'

urlpatterns = [
    path('', lambda request: redirect('dashboard/')),

    path('dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),

    # Mantenemos la URL original para compatibilidad con las plantillas
    path('refugios/sync/', admin_views.sincronizar_refugios_admin, name='sincronizar_refugios'),

    path('usuarios/', admin_views.gestionar_usuarios, name='gestionar_usuarios'),

    # Mantenemos la URL original para compatibilidad con las plantillas
    path('usuarios/editar/<int:usuario_id>/', admin_views.editar_usuario, name='editar_usuario'),

    # Mantenemos la URL original para compatibilidad con las plantillas
    path('usuarios/modificar_puntos/<int:usuario_id>/', admin_views.modificar_puntos_usuario, name='modificar_puntos_usuario'),

    path('estadisticas/estaciones/', admin_views.estadisticas_estaciones, name='estadisticas_estaciones'),

    path('gestionar-puntos/', admin_views.gestionar_puntos, name='gestionar_puntos'),
    
    # Mantenemos la URL original para compatibilidad con las plantillas
    path('añadir-punto/', admin_views.añadir_punto, name='añadir_punto'),
    
    # Mantenemos la URL original para compatibilidad con las plantillas
    path('editar-punto/<str:punto_id>/', admin_views.editar_punto, name='editar_punto'),
    
    path('eliminar-punto/<str:punto_id>/', admin_views.eliminar_punto, name='eliminar_punto'),
    
    # Mantenemos la URL original para compatibilidad con las plantillas
    path('cambiar-estado-punto/<str:punto_id>/', admin_views.cambiar_estado_punto, name='cambiar_estado_punto'),
    
    path('reports/', admin_views.gestionar_reports, name='gestionar_reports'),
    path('reports/<int:report_id>/', admin_views.detalle_report, name='detalle_report'),
    
    # Mantenemos la URL original para compatibilidad con las plantillas
    path('reports/<int:report_id>/resolver/', admin_views.resolver_report, name='resolver_report'),
    
    path('reports/<int:report_id>/reactivar/', admin_views.reactivar_report, name='reactivar_report'),
    path('usuarios/editar/<int:usuario_id>/bloquear/', admin_views.bloquear_usuario, name='bloquear_usuario'),
    path('usuarios/editar/<int:usuario_id>/desbloquear/', admin_views.desbloquear_usuario, name='desbloquear_usuario'),
]