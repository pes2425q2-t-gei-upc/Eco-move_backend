from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Count, Avg,Q
from django.utils import timezone
from datetime import timedelta
import requests

import json
from api_punts_carrega.models import (
    EstacioCarrega, Reserva, Vehicle, Usuario, RefugioClimatico, ValoracionEstacion,UsuarioTrofeo,Trofeo, ReporteEstacion
)

from social_community.models import (
    Report, Chat, Missatge,
)

# Definir constantes para las URLs
GESTIONAR_USUARIOS_URL = 'admin_connect:gestionar_usuarios'
GESTIONAR_PUNTOS_URL = 'admin_connect:gestionar_puntos'

@staff_member_required
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

@staff_member_required
def gestionar_usuarios(request):
    # Obtener parámetro de búsqueda
    query = request.GET.get('q', '')
    
    # Filtrar usuarios según la búsqueda
    if query:
        usuarios = Usuario.objects.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query)
        ).order_by('username')
    else:
        usuarios = Usuario.objects.all().order_by('username')
    
    context = {
        'usuarios': usuarios,
        'query': query,  # Para mantener el valor en el input de búsqueda
    }
    
    return render(request, 'admin_connect/gestionar_usuarios.html', context)

EDITAR_USUARIO_TEMPLATE = 'admin_connect/editar_usuario.html'

@staff_member_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)

    trofeos_usuario = UsuarioTrofeo.objects.filter(usuario=usuario).select_related('trofeo')
    todos_los_trofeos = Trofeo.objects.all().order_by('puntos_necesarios')
    trofeos_disponibles = todos_los_trofeos.exclude(
        id_trofeo__in=trofeos_usuario.values_list('trofeo__id_trofeo', flat=True)
    )

    if request.method == 'POST':
        if 'action' in request.POST:
            return _handle_trofeo_action(request, usuario, usuario_id)
        else:
            return _handle_usuario_update(request, usuario, usuario_id)

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
            messages.error(request, 'El trofeo seleccionado no existe.')
    return redirect('admin_connect:editar_usuario', usuario_id=usuario_id)

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
def bloquear_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        if usuario.is_admin == True:
            messages.error(request, f'No se puede bloquear al usuario {usuario.username} porque es administrador.')
            return redirect(GESTIONAR_USUARIOS_URL)
        usuario.bloqueado = True
        usuario.save()
        
        messages.success(request, f'Usuario {usuario.username} bloqueado correctamente.')
        return redirect(GESTIONAR_USUARIOS_URL)
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, EDITAR_USUARIO_TEMPLATE, context)


@staff_member_required
def desbloquear_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        usuario.bloqueado = False
        usuario.save()
        
        messages.success(request, f'Usuario {usuario.username} desbloqueado correctamente.')
        return redirect(GESTIONAR_USUARIOS_URL)
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, EDITAR_USUARIO_TEMPLATE, context)

@staff_member_required
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
    
    context = {
        'usuario': usuario,
    }
    
    return render(request, 'admin_connect/modificar_puntos.html', context)

@staff_member_required
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
    
    # Añadir conteo de reportes activos para cada estación
    estaciones = estaciones.annotate(
        reportes_count=Count(
            'reportes_errores',
            filter=Q(reportes_errores__estado__in=['ABIERTO', 'EN_PROGRESO'])
        )
    )
    
    context = {
        'estaciones': estaciones,
        'title': 'Gestionar Puntos de Carga',
    }
    
    return render(request, 'admin_connect/gestionar_puntos.html', context)

# Nueva vista para ver reportes de una estación específica
@staff_member_required
def ver_reportes_estacion(request, estacion_id):
    """Vista para ver todos los reportes de una estación específica"""
    estacion = get_object_or_404(EstacioCarrega, id_punt=estacion_id)
    
    # Filtro por estado
    estado_filtro = request.GET.get('estado', 'todos')
    
    # Obtener reportes según el filtro
    reportes = ReporteEstacion.objects.filter(estacion=estacion).select_related('usuario_reporta')
    
    if estado_filtro == 'abiertos':
        reportes = reportes.filter(estado='ABIERTO')
    elif estado_filtro == 'en_progreso':
        reportes = reportes.filter(estado='EN_PROGRESO')
    elif estado_filtro == 'resueltos':
        reportes = reportes.filter(estado='RESUELTO')
    
    reportes = reportes.order_by('-fecha_reporte')
    
    # Estadísticas de reportes
    reportes_abiertos = ReporteEstacion.objects.filter(estacion=estacion, estado='ABIERTO').count()
    reportes_en_progreso = ReporteEstacion.objects.filter(estacion=estacion, estado='EN_PROGRESO').count()
    reportes_resueltos = ReporteEstacion.objects.filter(estacion=estacion, estado='RESUELTO').count()
    total_reportes = ReporteEstacion.objects.filter(estacion=estacion).count()
    
    context = {
        'estacion': estacion,
        'reportes': reportes,
        'estado_filtro': estado_filtro,
        'reportes_abiertos': reportes_abiertos,
        'reportes_en_progreso': reportes_en_progreso,
        'reportes_resueltos': reportes_resueltos,
        'total_reportes': total_reportes,
    }
    
    return render(request, 'admin_connect/reportes_estacion.html', context)

# Nueva vista para cambiar el estado de un reporte
@staff_member_required
def cambiar_estado_reporte(request):
    """Vista para cambiar el estado de un reporte"""
    if request.method == 'POST':
        reporte_id = request.POST.get('reporte_id')
        nuevo_estado = request.POST.get('nuevo_estado')
        
        try:
            reporte = ReporteEstacion.objects.get(id=reporte_id)
            reporte.estado = nuevo_estado
            reporte.save()
            
            messages.success(request, f'Estado del reporte #{reporte_id} actualizado a {reporte.get_estado_display()}')
            return redirect('admin_connect:ver_reportes_estacion', estacion_id=reporte.estacion.id_punt)
        except ReporteEstacion.DoesNotExist:
            messages.error(request, 'El reporte no existe')
        except Exception as e:
            messages.error(request, f'Error al actualizar el reporte: {str(e)}')
    
    return redirect('admin_connect:gestionar_puntos')

AÑADIR_PUNTO_TEMPLATE = 'admin_connect/añadir_punto.html'
AÑADIR_PUNTO_TITLE = 'Añadir Punto de Carga'

@staff_member_required
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
    
    # Si es GET, mostrar el formulario
    return render(request, AÑADIR_PUNTO_TEMPLATE, {
        'title': AÑADIR_PUNTO_TITLE
    })

@staff_member_required
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
    
    context = {
        'estacion': estacion,
        'title': 'Editar Punto de Carga',
    }
    
    return render(request, 'admin_connect/editar_punto.html', context)

@staff_member_required
def cambiar_estado_punto(request, punto_id):
    """Vista para cambiar el estado de servicio de un punto de carga"""
    estacion = get_object_or_404(EstacioCarrega, id_punt=punto_id)
    
    if request.method == 'POST':
        # Si se envía POST, puede ser para desactivar con motivo o para reactivar
        motivo = request.POST.get('motivo_fuera_servicio', '')
        accion = request.POST.get('accion', '')
        
        if accion == 'reactivar' or not estacion.fuera_de_servicio:
            # Desactivar estación
            estacion.fuera_de_servicio = True
            estacion.motivo_fuera_servicio = motivo
            estacion.save()
            messages.warning(request, f"Punto de carga {punto_id} marcado como fuera de servicio")
        else:
            # Reactivar estación
            estacion.fuera_de_servicio = False
            estacion.motivo_fuera_servicio = None
            estacion.save()
            messages.success(request, f"Punto de carga {punto_id} reactivado correctamente")
        
        # Redirigir de vuelta a la página de reportes si venimos de ahí
        if 'HTTP_REFERER' in request.META and 'reportes' in request.META['HTTP_REFERER']:
            return redirect('admin_connect:ver_reportes_estacion', estacion_id=punto_id)
        else:
            return redirect(GESTIONAR_PUNTOS_URL)
    else:
        # GET request - solo para mostrar formulario de desactivación
        if estacion.fuera_de_servicio:
            # Si ya está fuera de servicio, reactivar directamente
            estacion.fuera_de_servicio = False
            estacion.motivo_fuera_servicio = None
            estacion.save()
            messages.success(request, f"Punto de carga {punto_id} reactivado correctamente")
            return redirect(GESTIONAR_PUNTOS_URL)
        else:
            # Si está en servicio, mostrar formulario para desactivar
            return render(request, 'admin_connect/desactivar_punto.html', {
                'estacion': estacion,
                'title': 'Desactivar Punto de Carga',
            })

@staff_member_required
def eliminar_punto(request, punto_id):
    """Vista para eliminar un punto de carga"""
    if request.method == 'POST':
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
    
    # Si es GET, redirigir a la página de gestión
    return redirect(GESTIONAR_PUNTOS_URL)


@staff_member_required
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

@staff_member_required
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
    
    context = {
        'report': report,
        'title': f'Resolver Reporte #{report.id_report}'
    }
    
    return render(request, 'admin_connect/resolver_report.html', context)

@staff_member_required
def reactivar_report(request, report_id):
    """
    Vista para reactivar un reporte que estaba resuelto
    """
    report = get_object_or_404(Report, id_report=report_id)
    
    report.is_active = True
    report.save()
    
    messages.success(request, f'Reporte #{report.id_report} reactivado correctamente')
    return redirect('admin_connect:gestionar_reports')
