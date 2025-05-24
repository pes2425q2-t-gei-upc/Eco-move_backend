from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django.views.decorators.csrf import csrf_protect
from datetime import timedelta
import requests

import json
from api_punts_carrega.models import (
    EstacioCarrega, Reserva, Vehicle, Usuario, RefugioClimatico, ValoracionEstacion,UsuarioTrofeo,Trofeo
)

from social_community.models import (
    Report, Chat, Missatge,
)

@staff_member_required
@require_GET
def admin_dashboard(request):
    # Estadísticas generales
    total_estaciones = EstacioCarrega.objects.count()
    total_reservas = Reserva.objects.count()
    total_vehiculos = Vehicle.objects.count()
    total_usuarios = Usuario.objects.count()
    
    # Reservas recientes
    reservas_recientes = Reserva.objects.select_related('estacion', 'vehicle').order_by('-fecha', '-hora')[:10]
    
    # Estaciones más reservadas
    estaciones_populares = Reserva.objects.values('estacion__id_punt').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    estaciones_ids = [item['estacion__id_punt'] for item in estaciones_populares]
    estaciones_populares_data = []
    
    for estacion_id in estaciones_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            reservas = Reserva.objects.filter(estacion=estacion).count()
            estaciones_populares_data.append({
                'estacion': estacion,
                'reservas': reservas
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    # Valoraciones recientes
    valoraciones_recientes = ValoracionEstacion.objects.select_related('estacion', 'usuario').order_by('-fecha_creacion')[:5]
    
    context = {
        'total_estaciones': total_estaciones,
        'total_reservas': total_reservas,
        'total_vehiculos': total_vehiculos,
        'total_usuarios': total_usuarios,
        'reservas_recientes': reservas_recientes,
        'estaciones_populares': estaciones_populares_data,
        'valoraciones_recientes': valoraciones_recientes,
    }
    
    return render(request, 'admin_connect/dashboard.html', context)

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def sincronizar_refugios_admin(request):
    if request.method == 'POST':
        try:
            response = requests.get('http://nattech.fib.upc.edu:40430/api/refugios/listar/', timeout=10)
            response.raise_for_status()
            
            refugios_data = response.json()
            contador_nuevos = 0
            contador_actualizados = 0
            
            for refugio_data in refugios_data:
                refugio_id = refugio_data['id']
                
                created = RefugioClimatico.objects.update_or_create(
                    id_punt=refugio_id,
                    defaults={
                        'nombre': refugio_data['nombre'],
                        'lat': float(refugio_data['latitud']),
                        'lng': float(refugio_data['longitud']),
                        'direccio': refugio_data['direccion'],
                        'numero_calle': refugio_data['numero_calle'],
                    }
                )
                
                if created:
                    contador_nuevos += 1
                else:
                    contador_actualizados += 1
            
            messages.success(
                request, 
                f'Sincronización completada. {contador_nuevos} refugios nuevos, {contador_actualizados} actualizados.'
            )
            
        except Exception as e:
            messages.error(request, f'Error al sincronizar refugios: {str(e)}')
        
        return redirect('admin_connect:sincronizar_refugios')
    
    # GET request - mostrar la página
    refugios = RefugioClimatico.objects.all().order_by('nombre')
    
    context = {
        'refugios': refugios,
    }
    
    return render(request, 'admin_connect/sincronizar_refugios.html', context)

GESTIONAR_USUARIOS_URL = 'admin_connect:gestionar_usuarios'

@staff_member_required
@require_GET
def gestionar_usuarios(request):
    usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'usuarios': usuarios,
    }
    
    return render(request, 'admin_connect/gestionar_usuarios.html', context)

EDITAR_USUARIO_TEMPLATE = 'admin_connect/editar_usuario.html'
EDITAR_USUARIO_URL = 'admin_connect:editar_usuario'  # Constant for editar_usuario URL name

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    trofeos_usuario = UsuarioTrofeo.objects.filter(usuario=usuario).select_related('trofeo')
    todos_los_trofeos = Trofeo.objects.all().order_by('puntos_necesarios')
    trofeos_disponibles = todos_los_trofeos.exclude(
        id_trofeo__in=trofeos_usuario.values_list('trofeo__id_trofeo', flat=True)
    )

    if request.method == 'POST':
        # Obtener datos del formulario
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        telefon = request.POST.get('telefon')
        idioma = request.POST.get('idioma')
        descripcio = request.POST.get('descripcio')
        is_admin = request.POST.get('is_admin') == 'on'
        is_active = request.POST.get('is_active') == 'on'
        new_password = request.POST.get('new_password')
         
        # Verificar si el username ya existe (excluyendo el usuario actual)
        if Usuario.objects.filter(username=username).exclude(id=usuario_id).exists():
             messages.error(request, f'El nombre de usuario {username} ya está en uso.')
             return redirect(EDITAR_USUARIO_URL, usuario_id=usuario_id)
         
        # Verificar si el email ya existe (excluyendo el usuario actual)
        if Usuario.objects.filter(email=email).exclude(id=usuario_id).exists():
             messages.error(request, f'El email {email} ya está en uso.')
             return redirect(EDITAR_USUARIO_URL, usuario_id=usuario_id)
         
         # Actualizar datos del usuario
        usuario.username = username
        usuario.email = email
        usuario.first_name = first_name
        usuario.last_name = last_name
        usuario.telefon = telefon
        usuario.idioma = idioma
        usuario.descripcio = descripcio
        usuario.is_admin = is_admin
        usuario.is_staff = is_admin  # Actualizar is_staff junto con is_admin
        usuario.is_active = is_active
         
         # Actualizar contraseña si se proporciona una nueva
        if new_password:
            usuario.set_password(new_password)
        
        usuario.save()
         
        messages.success(request, f'Usuario {username} actualizado correctamente.')
        return redirect(GESTIONAR_USUARIOS_URL)
     
    # GET request - mostrar formulario de edición
    context = {
        'usuario': usuario,
        'trofeos_usuario': trofeos_usuario,
        'trofeos_disponibles': trofeos_disponibles,
    }

    return render(request, EDITAR_USUARIO_TEMPLATE, context)

def _handle_trofeo_action(request, usuario, usuario_id):
    action = request.POST.get('action')
    trofeo_id = request.POST.get('trofeo_id')
    if action == 'eliminar_trofeo':
        try:
            usuario_trofeo = UsuarioTrofeo.objects.get(
                usuario=usuario,
                trofeo__id_trofeo=trofeo_id
            )
            usuario_trofeo.delete()
            messages.success(request, 'Trofeo eliminado correctamente.')
        except UsuarioTrofeo.DoesNotExist:
            messages.error(request, 'El trofeo no existe o ya fue eliminado.')
    elif action == 'añadir_trofeo':
        try:
            trofeo = Trofeo.objects.get(id_trofeo=trofeo_id)
            usuario_trofeo, created = UsuarioTrofeo.objects.get_or_create(
                usuario=usuario,
                trofeo=trofeo
            )
            if created:
                messages.success(request, f'Trofeo "{trofeo.nombre}" añadido correctamente.')
            else:
                messages.info(request, f'El usuario ya tiene el trofeo "{trofeo.nombre}".')
        except Trofeo.DoesNotExist:
            return redirect(EDITAR_USUARIO_URL, usuario_id=usuario_id)

def _handle_usuario_update(request, usuario, usuario_id):
    is_admin = request.POST.get('is_admin') == 'on'
    is_active = request.POST.get('is_active') == 'on'
    new_password = request.POST.get('new_password')

    usuario.is_admin = is_admin
    usuario.is_staff = is_admin
    usuario.is_active = is_active

    if new_password:
        usuario.set_password(new_password)

    usuario.save()
    messages.success(request, 'Permisos de usuario actualizados correctamente.')
    return redirect('admin_connect:editar_usuario', usuario_id=usuario_id)

@staff_member_required
@csrf_protect
@require_POST
def bloquear_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if usuario.is_admin == True:
        messages.error(request, f'No se puede bloquear al usuario {usuario.username} porque es administrador.')
        return redirect(GESTIONAR_USUARIOS_URL)
    
    usuario.bloqueado = True
    usuario.save()
    
    messages.success(request, f'Usuario {usuario.username} bloqueado correctamente.')
    return redirect(GESTIONAR_USUARIOS_URL)

@staff_member_required
@csrf_protect
@require_POST
def desbloquear_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    usuario.bloqueado = False
    usuario.save()
    
    messages.success(request, f'Usuario {usuario.username} desbloqueado correctamente.')
    return redirect(GESTIONAR_USUARIOS_URL)

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def modificar_puntos_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        accion = request.POST.get('accion')
        puntos = request.POST.get('puntos')
        #print(f"Acción: {accion}, Puntos: {puntos}")
        try:
            puntos = int(puntos)
            if accion == 'sumar':
                usuario.sumar_punts(puntos)
                messages.success(request, f'Se han sumado {puntos} puntos a {usuario.username}')
            
        except ValueError as e:
            messages.error(request, str(e))
        
        return redirect(GESTIONAR_USUARIOS_URL)
    
    # GET request - mostrar formulario
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'admin_connect/modificar_puntos.html', context)

@staff_member_required
@require_GET
def estadisticas_estaciones(request):
    # Estaciones con más reservas
    estaciones_con_reservas = Reserva.objects.values('estacion__id_punt').annotate(
        total_reservas=Count('id')
    ).order_by('-total_reservas')[:10]
    
    estaciones_ids = [item['estacion__id_punt'] for item in estaciones_con_reservas]
    estaciones_data = []
    
    for estacion_id in estaciones_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            reservas = Reserva.objects.filter(estacion=estacion).count()
            valoracion_media = ValoracionEstacion.objects.filter(estacion=estacion).aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
            
            estaciones_data.append({
                'estacion': estacion,
                'reservas': reservas,
                'valoracion_media': round(valoracion_media, 1)
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    # Estaciones mejor valoradas
    estaciones_valoradas = ValoracionEstacion.objects.values('estacion__id_punt').annotate(
        valoracion_media=Avg('puntuacion'),
        total_valoraciones=Count('id')
    ).order_by('-valoracion_media')[:10]
    
    estaciones_valoradas_ids = [item['estacion__id_punt'] for item in estaciones_valoradas]
    estaciones_valoradas_data = []
    
    for estacion_id in estaciones_valoradas_ids:
        try:
            estacion = EstacioCarrega.objects.get(id_punt=estacion_id)
            valoraciones = ValoracionEstacion.objects.filter(estacion=estacion)
            valoracion_media = valoraciones.aggregate(Avg('puntuacion'))['puntuacion__avg'] or 0
            total_valoraciones = valoraciones.count()
            
            estaciones_valoradas_data.append({
                'estacion': estacion,
                'valoracion_media': round(valoracion_media, 1),
                'total_valoraciones': total_valoraciones
            })
        except EstacioCarrega.DoesNotExist:
            continue
    
    context = {
        'estaciones_data': estaciones_data,
        'estaciones_valoradas_data': estaciones_valoradas_data,
    }
    
    return render(request, 'admin_connect/estadisticas_estaciones.html', context)

@staff_member_required
@require_GET
def gestionar_puntos(request):
    """Vista para gestionar los puntos de carga"""
    # Obtener parámetro de búsqueda
    query = request.GET.get('q', '')
    
    # Filtrar estaciones según la búsqueda
    if query:
        estaciones = EstacioCarrega.objects.filter(
            Q(id_punt__icontains=query) | 
            Q(direccio__icontains=query) |
            Q(ciutat__icontains=query)
        ).order_by('id_punt')
    else:
        estaciones = EstacioCarrega.objects.all().order_by('id_punt')
    
    context = {
        'estaciones': estaciones,
        'title': 'Gestionar Puntos de Carga',
    }
    
    return render(request, 'admin_connect/gestionar_puntos.html', context)

AÑADIR_PUNTO_TEMPLATE = 'admin_connect/añadir_punto.html'
AÑADIR_PUNTO_TITLE = 'Añadir Punto de Carga'
GESTIONAR_PUNTOS_URL = 'admin_connect:gestionar_puntos'

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def añadir_punto(request):
    """Vista para añadir un nuevo punto de carga"""
    if request.method == 'POST':
        # Obtener datos del formulario
        id_punt = request.POST.get('id_punt')
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')
        direccio = request.POST.get('direccio')
        ciutat = request.POST.get('ciutat')
        provincia = request.POST.get('provincia')
        gestio = request.POST.get('gestio')
        tipus_acces = request.POST.get('tipus_acces')
        nplaces = request.POST.get('nplaces')
        potencia = request.POST.get('potencia')
        fuera_de_servicio = 'fuera_de_servicio' in request.POST
        motivo_fuera_servicio = request.POST.get('motivo_fuera_servicio', '')
        
        # Validar que el ID no exista ya
        if EstacioCarrega.objects.filter(id_punt=id_punt).exists():
            messages.error(request, f"Ya existe un punto de carga con el ID {id_punt}")
            return render(request, AÑADIR_PUNTO_TEMPLATE, {
                'title': AÑADIR_PUNTO_TITLE,
                'error': f"Ya existe un punto de carga con el ID {id_punt}"
            })
        
        try:
            # Convertir coordenadas reemplazando comas por puntos
            lat = float(lat.replace(',', '.'))
            lng = float(lng.replace(',', '.'))
            
            # Crear el nuevo punto de carga
            estacion = EstacioCarrega(
                id_punt=id_punt,
                lat=lat,
                lng=lng,
                direccio=direccio,
                ciutat=ciutat,
                provincia=provincia,
                gestio=gestio,
                tipus_acces=tipus_acces,
                nplaces=nplaces,
                potencia=int(potencia) if potencia and potencia.strip() else None,
                fuera_de_servicio=fuera_de_servicio,
                motivo_fuera_servicio=motivo_fuera_servicio if fuera_de_servicio else None
            )
            estacion.save()
            
            messages.success(request, f"Punto de carga {id_punt} añadido correctamente")
            return redirect(GESTIONAR_PUNTOS_URL)
        except Exception as e:
            messages.error(request, f"Error al añadir el punto de carga: {str(e)}")
            return render(request, AÑADIR_PUNTO_TEMPLATE, {
                'title': AÑADIR_PUNTO_TITLE,
                'error': f"Error al añadir el punto de carga: {str(e)}"
            })
    
    # GET request - mostrar el formulario
    return render(request, AÑADIR_PUNTO_TEMPLATE, {
        'title': AÑADIR_PUNTO_TITLE
    })

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def editar_punto(request, punto_id):
    """Vista para editar un punto de carga existente"""
    estacion = get_object_or_404(EstacioCarrega, id_punt=punto_id)
    
    if request.method == 'POST':
        # Obtener datos del formulario
        lat = request.POST.get('lat', '')
        lng = request.POST.get('lng', '')
        direccio = request.POST.get('direccio')
        ciutat = request.POST.get('ciutat')
        provincia = request.POST.get('provincia')
        gestio = request.POST.get('gestio')
        tipus_acces = request.POST.get('tipus_acces')
        nplaces = request.POST.get('nplaces')
        potencia = request.POST.get('potencia')
        fuera_de_servicio = 'fuera_de_servicio' in request.POST
        motivo_fuera_servicio = request.POST.get('motivo_fuera_servicio', '')
        
        try:
            # Convertir coordenadas reemplazando comas por puntos
            lat = float(lat.replace(',', '.'))
            lng = float(lng.replace(',', '.'))
            
            # Actualizar el punto de carga
            estacion.lat = lat
            estacion.lng = lng
            estacion.direccio = direccio
            estacion.ciutat = ciutat
            estacion.provincia = provincia
            estacion.gestio = gestio
            estacion.tipus_acces = tipus_acces
            estacion.nplaces = nplaces
            estacion.potencia = int(potencia) if potencia and potencia.strip() else None
            estacion.fuera_de_servicio = fuera_de_servicio
            estacion.motivo_fuera_servicio = motivo_fuera_servicio if fuera_de_servicio else None
            estacion.save()
            
            messages.success(request, f"Punto de carga {punto_id} actualizado correctamente")
            return redirect(GESTIONAR_PUNTOS_URL)
        except Exception as e:
            messages.error(request, f"Error al actualizar el punto de carga: {str(e)}")
    
    # GET request - mostrar formulario de edición
    context = {
        'estacion': estacion,
        'title': 'Editar Punto de Carga',
    }
    
    return render(request, 'admin_connect/editar_punto.html', context)

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def cambiar_estado_punto(request, punto_id):
    """Vista para cambiar el estado de servicio de un punto de carga"""
    estacion = get_object_or_404(EstacioCarrega, id_punt=punto_id)
    
    if request.method == 'POST':
        # Si se envía el formulario con el motivo para desactivar
        if 'desactivar' in request.POST:
            motivo = request.POST.get('motivo_fuera_servicio', '')
            estacion.fuera_de_servicio = True
            estacion.motivo_fuera_servicio = motivo
            estacion.save()
            
            messages.warning(request, f"Punto de carga {punto_id} marcado como fuera de servicio")
            return redirect(GESTIONAR_PUNTOS_URL)
        # Si se confirma la activación
        elif 'activar' in request.POST:
            estacion.fuera_de_servicio = False
            estacion.motivo_fuera_servicio = None
            estacion.save()
            messages.success(request, f"Punto de carga {punto_id} marcado como en servicio")
            return redirect(GESTIONAR_PUNTOS_URL)
    
    # GET request - mostrar formulario según el estado actual
    if estacion.fuera_de_servicio:
        # Mostrar formulario de confirmación para activar
        return render(request, 'admin_connect/activar_punto.html', {
            'estacion': estacion,
            'title': 'Activar Punto de Carga',
        })
    else:
        # Mostrar formulario para indicar motivo de desactivación
        return render(request, 'admin_connect/desactivar_punto.html', {
            'estacion': estacion,
            'title': 'Desactivar Punto de Carga',
        })

@staff_member_required
@csrf_protect
@require_POST
def eliminar_punto(request, punto_id):
    """Vista para eliminar un punto de carga"""
    estacion = get_object_or_404(EstacioCarrega, id_punt=punto_id)
    
    # Verificar si hay reservas asociadas
    reservas_count = Reserva.objects.filter(estacion=estacion).count()
    if reservas_count > 0:
        messages.error(request, f"No se puede eliminar el punto de carga {punto_id} porque tiene {reservas_count} reservas asociadas")
        return redirect(GESTIONAR_PUNTOS_URL)
    
    try:
        # Eliminar valoraciones asociadas
        ValoracionEstacion.objects.filter(estacion=estacion).delete()
        
        # Eliminar el punto de carga
        estacion.delete()
        
        messages.success(request, f"Punto de carga {punto_id} eliminado correctamente")
    except Exception as e:
        messages.error(request, f"Error al eliminar el punto de carga: {str(e)}")
    
    return redirect(GESTIONAR_PUNTOS_URL)

@staff_member_required
@require_GET
def gestionar_reports(request):
    """
    Vista para administrar los reportes de usuarios
    """
    # Obtener parámetro de estado (activo/resuelto)
    estado = request.GET.get('estado', 'activos')
    
    # Filtrar reportes según el estado
    if estado == 'resueltos':
        reports = Report.objects.filter(is_active=False).order_by('-timestamp')
        titulo = 'Reportes Resueltos'
    else:  # Por defecto, mostrar activos
        reports = Report.objects.filter(is_active=True).order_by('-timestamp')
        titulo = 'Reportes Activos'
    
    context = {
        'reports': reports,
        'title': titulo,
        'estado_actual': estado
    }
    
    return render(request, 'admin_connect/gestionar_reports.html', context)

@staff_member_required
@require_GET
def detalle_report(request, report_id):
    """
    Vista para ver el detalle de un reporte específico
    """
    report = get_object_or_404(Report, id_report=report_id)
    
    # Obtener los mensajes del chat entre estos usuarios si existe alguno
    chats = Chat.objects.filter(
        Q(creador=report.creador, receptor=report.receptor) | 
        Q(creador=report.receptor, receptor=report.creador)
    )
    
    chat_messages = []
    if chats.exists():
        # Usar el chat más reciente si hay varios
        chat = chats.order_by('-inicida_en').first()
        # Obtener los mensajes recientes (últimos 20) ordenados por fecha
        chat_messages = Missatge.objects.filter(chat=chat).order_by('-timestamp')[:20]
        # Revertir para mostrar en orden cronológico
        chat_messages = reversed(list(chat_messages))
    
    context = {
        'report': report,
        'chat_messages': chat_messages,
        'title': f'Detalle del Reporte #{report.id_report}'
    }
    
    return render(request, 'admin_connect/detalle_report.html', context)

# Mantenemos la función original para compatibilidad con las plantillas existentes
@staff_member_required
@csrf_protect
@require_http_methods(["GET", "POST"])
def resolver_report(request, report_id):
    """
    Vista para marcar un reporte como resuelto
    """
    report = get_object_or_404(Report, id_report=report_id)
    
    if request.method == 'POST':
        report.is_active = False
        report.save()
        messages.success(request, f'Reporte #{report.id_report} marcado como resuelto')
        return redirect('admin_connect:gestionar_reports')
    
    # GET request - mostrar formulario de confirmación
    context = {
        'report': report,
        'title': f'Resolver Reporte #{report.id_report}'
    }
    
    return render(request, 'admin_connect/resolver_report.html', context)

@staff_member_required
@csrf_protect
@require_POST
def reactivar_report(request, report_id):
    """
    Vista para reactivar un reporte que estaba resuelto
    """
    report = get_object_or_404(Report, id_report=report_id)
    
    report.is_active = True
    report.save()
    
    messages.success(request, f'Reporte #{report.id_report} reactivado correctamente')
    return redirect('admin_connect:gestionar_reports')