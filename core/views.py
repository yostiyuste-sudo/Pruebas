import imaplib
import email
import os
import traceback
from email.header import decode_header
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail, EmailMultiAlternatives
from django.urls import reverse
import uuid
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum
from django.db.models.functions import TruncMonth
from .models import Contacto, TipoContacto, TipoIdentificacion, Interaccion, TipoInteraccion, Usuario, Rol, FirmaDigital, MensajeWhatsApp

def enviar_correo_seguro(asunto, texto_plano, destinatarios, html_content=None, attachments=None):
    import json, urllib.request, urllib.error, re, base64, uuid
    api_key = getattr(settings, 'BREVO_API_KEY', '')
    if not api_key:
        return "No hay BREVO_API_KEY configurada en las variables de entorno de Render"
    try:
        from_email = settings.DEFAULT_FROM_EMAIL
        if not from_email:
            return "No hay DEFAULT_FROM_EMAIL configurado en las variables de entorno de Render."
        if not html_content:
            html_body = texto_plano.replace('\n', '<br>')
            html_content = f"""<html><body style="font-family:Segoe UI,Tahoma,sans-serif;color:#333;background:#F4F7FE;padding:20px"><div style="max-width:600px;margin:0 auto;background:#fff;padding:30px;border-radius:12px"><h1 style="color:#D32F2F;margin:0;font-size:24px">Constructora Dyco</h1><p style="color:#A3AED0;font-size:14px">Gesti&oacute;n y CRM</p><hr style="border:none;border-top:1px solid #E9EDF7;margin:20px 0"><div style="font-size:15px;color:#1B2559">{html_body}</div></div></body></html>"""

        brevo_attachments = []
        if attachments:
            for att in attachments:
                entry = {"name": att["name"], "content": att["content"]}
                if att.get("cid"):
                    entry["cid"] = att["cid"]
                brevo_attachments.append(entry)

        payload_data = {
            "sender": {"name": "Constructora Dyco", "email": from_email},
            "to": [{"email": d} for d in destinatarios],
            "subject": asunto,
            "htmlContent": html_content
        }
        if brevo_attachments:
            payload_data["attachment"] = brevo_attachments

        payload = json.dumps(payload_data).encode()
        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=payload,
            headers={
                "api-key": api_key,
                "Content-Type": "application/json"
            },
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            print(f"[BREVO] Email enviado: {resp.read().decode()}")
            return None
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[BREVO ERROR {e.code}] {body}")
        return f"Brevo rechazó el email (código {e.code}): {body}"
    except Exception as e:
        print(f"[BREVO ERROR] {e}")
        return f"Error al enviar correo: {e}"

def registro_view(request):
    error = ""
    roles = Rol.objects.all()
    try:
        Rol.objects.get_or_create(nombre_rol="Administrador")
        Rol.objects.get_or_create(nombre_rol="Usuario")
        
        if request.method == "POST":
            nombre = request.POST.get("usuario")
            email = request.POST.get("email")
            
            rol_obj = Rol.objects.filter(nombre_rol="Usuario").first()
            rol_id = rol_obj.id if rol_obj else None
            
            passw = request.POST.get("password")
            
            usuario_sin_verificar = Usuario.objects.filter(email=email, activo=False).first()
            if usuario_sin_verificar:
                import random
                pin = str(random.randint(100000, 999999))
                usuario_sin_verificar.token_verificacion = pin
                usuario_sin_verificar.save()
                email_err = enviar_correo_seguro(
                    'Verifica tu cuenta (reenvío) - CRM',
                    f'Hola {usuario_sin_verificar.nombre_usuario},\n\nTu nuevo código de verificación es: {pin}\n\nIntroduce este código en la web para activar tu cuenta.',
                    [usuario_sin_verificar.email]
                )
                print(f"\n[SOPORTE] Código de verificación (reenvío) para {usuario_sin_verificar.nombre_usuario}: {pin}\n")
                return render(request, "registro.html", {
                    "success": "Te hemos reenviado un nuevo código de verificación. Revisa tu correo.",
                    "error": email_err or "",
                    "roles": roles,
                    "show_pin": True,
                    "email_reg": email
                })
            elif Usuario.objects.filter(nombre_usuario=nombre).exists():
                error = "Este nombre de usuario ya está ocupado."
            elif Usuario.objects.filter(email=email, activo=True).exists():
                error = "Este correo electrónico ya está registrado y verificado."
            else:
                import random
                pin = str(random.randint(100000, 999999))
                Usuario.objects.create(
                    nombre_usuario=nombre,
                    email=email,
                    rol_id=rol_id,
                    password_hash=passw,
                    activo=False,
                    token_verificacion=pin
                )
                email_err = enviar_correo_seguro(
                    'Bienvenido al CRM - Código de Verificación',
                    f'Hola {nombre},\n\nTu código para activar tu cuenta es: {pin}\n\nIntroduce este código en la web para terminar tu registro.',
                    [email]
                )
                print(f"\n[SOPORTE] Código de verificación para {nombre}: {pin}\n")
                return render(request, "registro.html", {
                    "success": "Registro exitoso. Introduce el código de 6 dígitos que enviamos a tu correo para activar tu cuenta.",
                    "error": email_err or "",
                    "roles": roles,
                    "show_pin": True,
                    "email_reg": email
                })
    except Exception as e:
        error = f"Error interno: {e}"
        traceback.print_exc()
                
    return render(request, "registro.html", {"roles": roles, "error": error})

def verificar_correo(request):
    """Vista manejadora para verificar el código PIN de registro."""
    if request.method == "POST":
        pin = request.POST.get("pin", "").strip()
        email = request.POST.get("email", "").strip()
        
        if not pin or not email:
            return render(request, "login.html", {"error": "Faltan datos de verificación.", "roles": Rol.objects.all()})
            
        u = Usuario.objects.filter(email__iexact=email, token_verificacion=pin).first()
        if u:
            u.activo = True
            u.token_verificacion = ""
            u.save()
            return render(request, "login.html", {"success": "Cuenta verificada con éxito. Ya puedes iniciar sesión.", "roles": Rol.objects.all()})
        else:
            return render(request, "registro.html", {
                "error": "Código de verificación incorrecto.", 
                "roles": Rol.objects.all(),
                "show_pin": True,
                "email_reg": email
            })
            
    return redirect('/registro/')

def reenviar_pin(request):
    """Reenvía el PIN de verificación al correo registrado."""
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        u = Usuario.objects.filter(email__iexact=email, activo=False).first()
        if u:
            import random
            pin = str(random.randint(100000, 999999))
            u.token_verificacion = pin
            u.save()
            enviar_correo_seguro(
                'Nuevo código de verificación - Constructora Dyco',
                f'Hola {u.nombre_usuario},\n\nTu nuevo código de verificación es: {pin}\n\nEste código expirará en 5 minutos.',
                [u.email]
            )
            print(f"\n[SOPORTE] Nuevo PIN reenviado para {u.nombre_usuario}: {pin}\n")
            return render(request, "registro.html", {
                "success": "Se ha reenviado un nuevo código a tu correo.",
                "roles": Rol.objects.all(),
                "show_pin": True,
                "email_reg": email
            })
        else:
            return render(request, "registro.html", {
                "error": "No encontramos una cuenta pendiente con ese correo.",
                "roles": Rol.objects.all(),
                "show_pin": True,
                "email_reg": email
            })
    return redirect('/registro/')

def cambiar_correo_registro(request):
    """Permite al usuario cambiar el correo antes de verificar."""
    error = ""
    if request.method == "POST":
        email_viejo = request.POST.get("email_viejo", "").strip()
        email_nuevo = request.POST.get("email_nuevo", "").strip()
        u = Usuario.objects.filter(email__iexact=email_viejo, activo=False).first()
        if not u:
            return render(request, "registro.html", {
                "error": "No se encontró la cuenta pendiente de verificación.",
                "roles": Rol.objects.all(),
                "show_pin": True,
                "email_reg": email_viejo
            })
        if Usuario.objects.filter(email__iexact=email_nuevo, activo=True).exists():
            return render(request, "registro.html", {
                "error": "Ese correo ya está en uso por otra cuenta verificada.",
                "roles": Rol.objects.all(),
                "show_pin": True,
                "email_reg": email_viejo
            })
        import random
        pin = str(random.randint(100000, 999999))
        u.email = email_nuevo
        u.token_verificacion = pin
        u.save()
        try:
            enviar_correo_seguro(
                'Código de verificación - Constructora Dyco',
                f'Hola {u.nombre_usuario},\n\nTu código de verificación para tu nuevo correo es: {pin}\n\nEste código expirará en 5 minutos.',
                [email_nuevo]
            )
            print(f"\n[SOPORTE] PIN enviado al nuevo correo {email_nuevo} para {u.nombre_usuario}: {pin}\n")
        except Exception as e:
            print(f"[EMAIL ERROR] {e}")
            error = f"No se pudo enviar el correo: {e}"
        return render(request, "registro.html", {
            "success": f"Correo actualizado. Hemos enviado un nuevo código a {email_nuevo}.",
            "error": error,
            "roles": Rol.objects.all(),
            "show_pin": True,
            "email_reg": email_nuevo
        })
    return redirect('/registro/')

def login_view(request):
    error = ""
    # Asegurar roles base
    admin_rol, _ = Rol.objects.get_or_create(nombre_rol="Administrador")
    user_rol, _ = Rol.objects.get_or_create(nombre_rol="Usuario")
    
    # Usuario admin de prueba
    if not Usuario.objects.filter(nombre_usuario="admin").exists():
        Usuario.objects.create(nombre_usuario="admin", email="admin@crm.com", password_hash="admin123", rol=admin_rol, activo=True)
    
    if request.method == "POST":
        user_input = request.POST.get("usuario", "").strip()
        pass_input = request.POST.get("password", "")
        
        u = Usuario.objects.filter(
            Q(nombre_usuario__iexact=user_input) | Q(email__iexact=user_input),
            password_hash=pass_input
        ).first()
        
        if u:
            if u.activo:
                request.session['user_id'] = u.id
                request.session['user_name'] = u.nombre_usuario
                request.session['rol_name'] = u.rol.nombre_rol
                return redirect('/')
            else:
                error = "Tu cuenta se encuentra inactiva o sin verificar. Revisa tu correo o contacta al administrador."
        else:
            error = "Cuidado! Datos o rol incorrectos."

    roles = Rol.objects.all()
    return render(request, "login.html", {"roles": roles, "error": error})

def logout_view(request):
    request.session.flush()
    return redirect('/login/')

def recuperar_contrasena_view(request):
    error = ""
    success = ""
    step = 1 # Paso 1: Pedir Email
    
    if request.method == "POST":
        if "email" in request.POST and "pin" not in request.POST:
            # Paso 1: Verificar email y generar PIN
            email = request.POST.get("email", "").strip()
            u = Usuario.objects.filter(email__iexact=email).first()
            if u:
                import random
                pin = str(random.randint(100000, 999999))
                u.token_password = pin
                u.save()
                
                # Enviar correo (simplificado, sin links de ngrok)
                try:
                    enviar_correo_seguro(
                        'Código de Recuperación - Constructora Dyco',
                        f'Hola {u.nombre_usuario},\n\nTu código de recuperación de contraseña es: {pin}\n\nIntroduce este código en la ventana de recuperación para continuar.',
                        [email]
                    )
                    # Atajo para desarrollo: imprimir el código en la consola
                    print(f"\n[SOPORTE] Código de recuperación para {u.nombre_usuario}: {pin}\n")
                    
                    success = f"¡Código generado! Revisa tu correo (o la consola de este servidor). Introduce el código de 6 dígitos para continuar."
                    step = 2 # Pasar al paso de introducir el PIN
                    request.session['resetting_email'] = email
                except Exception as e:
                    error = f"Error al enviar el correo: {e}. (Revisa la consola del servidor para ver el código)."
                    # Aun si falla el mail, mostramos el paso 2 por si el user mira la consola
                    step = 2
                    request.session['resetting_email'] = email
            else:
                error = "No encontramos ningún usuario con ese correo electrónico."
        
        elif "pin" in request.POST:
            # Paso 2: Verificar el PIN
            pin_input = request.POST.get("pin", "").strip()
            email = request.session.get('resetting_email')
            if not email:
                return redirect('/recuperar-contrasena/')
                
            u = Usuario.objects.filter(email__iexact=email, token_password=pin_input).first()
            if u:
                # Éxito: Redirigir a la pantalla de cambio de clave usando el PIN como token
                return redirect(reverse('resetear_contrasena', args=[pin_input]))
            else:
                error = "El código ingresado es incorrecto."
                step = 2
                success = "Introduce el código de 6 dígitos que recibiste."
            
    return render(request, "recuperar_contrasena.html", {"error": error, "success": success, "step": step})

def resetear_contrasena_view(request, token):
    error = ""
    # Asegurar roles para que el login.html no falle al renderizar
    Rol.objects.get_or_create(nombre_rol="Administrador")
    Rol.objects.get_or_create(nombre_rol="Usuario")
    
    if not token:
        return render(request, "login.html", {
            "error": "El enlace de recuperación es inválido.", 
            "roles": Rol.objects.all()
        })
    
    u = Usuario.objects.filter(token_password=token).first()
    if not u or not token:
        return render(request, "login.html", {
            "error": "El enlace de recuperación es inválido o ha caducado por una nueva solicitud.", 
            "roles": Rol.objects.all()
        })
    
    if request.method == "POST":
        passw = request.POST.get("password")
        confirm_passw = request.POST.get("confirm_password")
        
        if not passw or len(passw) < 4:
            error = "La contraseña debe tener al menos 4 caracteres."
        elif passw != confirm_passw:
            error = "Las contraseñas no coinciden."
        else:
            u.password_hash = passw
            u.token_password = "" 
            u.save()
            return render(request, "login.html", {
                "success": "Tu contraseña ha sido actualizada. Ya puedes entrar al sistema.", 
                "roles": Rol.objects.all(),
                "error": ""
            })
            
    return render(request, "resetear_contrasena.html", {"error": error, "token": token})

def dashboard(request):
    user_id = request.session.get('user_id')
    if not user_id: return redirect('/login/')
    u = Usuario.objects.get(id=user_id)
    
    # Estadísticas generales
    total_contactos = Contacto.objects.count()
    contactos_activos = Contacto.objects.filter(activo=True).count()
    contactos_inactivos = Contacto.objects.filter(activo=False).count()
    
    # Interacciones
    total_interacciones = Interaccion.objects.count()
    reuniones_programadas = Interaccion.objects.filter(tipo_interaccion__nombre_tipo='Reunión', estado='Programada').count()
    
    # Interacciones por tipo
    stats_interacciones = Interaccion.objects.values('tipo_interaccion__nombre_tipo').annotate(total=Count('id'))
    
    # Actividad reciente
    recientes = Interaccion.objects.all().order_by('-fecha_interaccion')[:8]
    
    # Mis contactos
    mis_contactos = Contacto.objects.filter(usuario_asignado=u).count()
    
    # Stats de usuarios (Para administrador)
    total_usuarios = Usuario.objects.count() if u.rol.nombre_rol == "Administrador" else 0
    usuarios_activos = Usuario.objects.filter(activo=True).count() if u.rol.nombre_rol == "Administrador" else 0
    usuarios_inactivos = Usuario.objects.filter(activo=False).count() if u.rol.nombre_rol == "Administrador" else 0
    
    usuarios_activos_perc = (usuarios_activos / total_usuarios * 100) if total_usuarios > 0 else 0
    usuarios_inactivos_perc = 100 - usuarios_activos_perc if total_usuarios > 0 else 0

    # 1. Diagrama circular (Natural vs Jurídica)
    natural_count = Contacto.objects.filter(tipo_contacto__nombre_tipo="Persona Natural").count()
    juridica_count = total_contactos - natural_count
    natural_perc = (natural_count / total_contactos * 100) if total_contactos > 0 else 0
    juridica_perc = 100 - natural_perc if total_contactos > 0 else 0
    
    # 2. Diagrama de barras (Llamadas, Correos, Reuniones, Notas, Otros)
    stats_acciones = Interaccion.objects.values('tipo_interaccion__nombre_tipo')\
        .annotate(total=Count('id'))
    
    # Mapear a 5 categorías fijas
    tipo_map = {'Llamada': 0, 'Correo': 0, 'Reunión': 0, 'Nota': 0}
    otros_acciones = 0
    for s in stats_acciones:
        name = s['tipo_interaccion__nombre_tipo']
        count = s['total']
        if name in tipo_map:
            tipo_map[name] = count
        else:
            otros_acciones += count
    
    acciones_labels = list(tipo_map.keys())
    acciones_counts = list(tipo_map.values())
    if otros_acciones > 0:
        acciones_labels.append('Otros')
        acciones_counts.append(otros_acciones)
    
    # 3. Diagrama lineal (Interacciones por mes)
    import locale
    # Intentar establecer locale a español para nombres de meses si es necesario, 
    # pero para mayor robustez usaremos un mapeo manual.
    meses_nombres = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEP", "OCT", "NOV", "DIC"]
    stats_mensual = Interaccion.objects.annotate(month=TruncMonth('fecha_interaccion'))\
        .values('month').annotate(total=Count('id')).order_by('month')

    # Diccionario para asegurar que todos los meses tengan entrada (opcional, pero mejor para el gráfico)
    # Por ahora simplemente los meses que tienen datos:
    tendencia_labels = []
    tendencia_counts = []
    
    if stats_mensual:
        for s in stats_mensual:
            # s['month'] es un objeto datetime o date truncado al mes
            m_idx = s['month'].month - 1
            tendencia_labels.append(meses_nombres[m_idx])
            tendencia_counts.append(s['total'])
    else:
        # Datos de prueba si está vacío
        tendencia_labels = meses_nombres[:6]
        tendencia_counts = [5, 12, 8, 15, 10, 20]
    
    # 4. Top Contactos
    top_contactos = Contacto.objects.annotate(num_inter=Count('interaccion'))\
        .order_by('-num_inter')[:5]

    return render(request, "dashboard.html", {
        "usuario_logueado": u,
        "total_contactos": total_contactos,
        "contactos_activos": contactos_activos,
        "contactos_inactivos": contactos_inactivos,
        "total_interacciones": total_interacciones,
        "reuniones_programadas": reuniones_programadas,
        "stats_interacciones": stats_interacciones,
        "recientes": recientes,
        "mis_contactos": mis_contactos,
        "total_usuarios": total_usuarios,
        "usuarios_activos": usuarios_activos,
        "usuarios_inactivos": usuarios_inactivos,
        "usuarios_activos_perc": usuarios_activos_perc,
        "usuarios_inactivos_perc": usuarios_inactivos_perc,
        "natural_count": natural_count,
        "juridica_count": juridica_count,
        "natural_perc": natural_perc,
        "juridica_perc": juridica_perc,
        "acciones_labels": acciones_labels,
        "acciones_counts": acciones_counts,
        "tendencia_labels": tendencia_labels,
        "tendencia_counts": tendencia_counts,
        "top_contactos": top_contactos,
    })

def contactos(request):
    # Verificación de sesión
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    
    error = ""
    # Asegurar tipos base
    if not TipoContacto.objects.exists():
        TipoContacto.objects.create(nombre_tipo="Persona Natural")
        TipoContacto.objects.create(nombre_tipo="Persona Jurídica")
    
    # Asegurar tipos de identificación
    if not TipoIdentificacion.objects.filter(nombre_tipo="CC").exists(): TipoIdentificacion.objects.get_or_create(nombre_tipo="CC")
    if not TipoIdentificacion.objects.filter(nombre_tipo="NIT").exists(): TipoIdentificacion.objects.get_or_create(nombre_tipo="NIT")
    if not TipoIdentificacion.objects.filter(nombre_tipo="TI").exists(): TipoIdentificacion.objects.get_or_create(nombre_tipo="TI")
    if not TipoIdentificacion.objects.filter(nombre_tipo="Pasaporte").exists(): TipoIdentificacion.objects.get_or_create(nombre_tipo="Pasaporte")
    if not TipoIdentificacion.objects.filter(nombre_tipo="CE").exists(): TipoIdentificacion.objects.get_or_create(nombre_tipo="CE")
    
    if request.method == "POST":
        tipo_contacto_id = request.POST.get("tipo_contacto")
        tipo_doc_id = request.POST.get("tipo_doc")
        documento_nit = request.POST.get("documento_nit")
        celular = request.POST.get("celular")
        direccion = request.POST.get("direccion")
        ciudad = request.POST.get("ciudad")
        correo = request.POST.get("correo")
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        razon_social = request.POST.get("razon_social")
        nombre_rep_legal = request.POST.get("nombre_rep_legal")
        
        identificador = nombre if nombre else razon_social
        
        if not identificador or not documento_nit:
            error = "Nombre/Razón Social y Identificación son obligatorios."
        elif Contacto.objects.filter(documento_nit=documento_nit).exists():
            error = f"El documento/NIT '{documento_nit}' ya se encuentra registrado."
        elif not correo and not celular:
            error = "Ingrese al menos Correo o Celular."
        else:
            try:
                Contacto.objects.create(
                    tipo_contacto_id=tipo_contacto_id, tipo_doc_id=tipo_doc_id,
                    documento_nit=documento_nit, celular=celular,
                    direccion=direccion, ciudad=ciudad, correo=correo,
                    usuario_asignado=usuario_logueado, nombre=nombre,
                    apellido=apellido, razon_social=razon_social, 
                    nombre_rep_legal=nombre_rep_legal, activo=True,
                    historial_cambios=f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Registrado por {usuario_logueado.nombre_usuario}"
                )
                return redirect('/')
            except Exception as e: error = f"Error: {e}"
            
    query = request.GET.get('q', '')
    activos = Contacto.objects.all().order_by('-fecha_registro')
    if query:
        activos = activos.filter(
            Q(nombre__icontains=query) | 
            Q(apellido__icontains=query) | 
            Q(razon_social__icontains=query) | 
            Q(documento_nit__icontains=query) | 
            Q(correo__icontains=query)
        )

    # Lista estática de proyectos activos
    proyectos = [
        {"id": 1, "nombre_proyecto": "Satori (Ibagué)"},
        {"id": 2, "nombre_proyecto": "Mandala (Ibagué)"},
        {"id": 3, "nombre_proyecto": "Selvia (Armenia)"},
        {"id": 4, "nombre_proyecto": "Ícono 60 (Ibagué)"},
        {"id": 5, "nombre_proyecto": "Ática (Ibagué)"},
        {"id": 6, "nombre_proyecto": "Vivalto (Ibagué)"},
        {"id": 7, "nombre_proyecto": "Morada Pinaos (Ibagué)"},
    ]

    return render(request, "index.html", {
        "activos": activos,
        "inactivos": Contacto.objects.filter(activo=False),
        "tipos_contacto": TipoContacto.objects.all(),
        "tipos_doc": TipoIdentificacion.objects.all(),
        "proyectos": proyectos,
        "error": error,
        "usuario_logueado": usuario_logueado,
        "query": query
    })

def editar_contacto(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion: return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    
    p = get_object_or_404(Contacto, id=id_contacto)
    
    # Valores anteriores para auditoría
    old = {
        'documento_nit': p.documento_nit, 'correo': p.correo, 'celular': p.celular,
        'ciudad': p.ciudad, 'direccion': p.direccion,
        'nombre': p.nombre, 'apellido': p.apellido,
        'razon_social': p.razon_social, 'nombre_rep_legal': p.nombre_rep_legal
    }
    
    error = ""
    if request.method == "POST":
        p.documento_nit = request.POST.get("documento_nit")
        p.correo = request.POST.get("correo")
        p.celular = request.POST.get("celular")
        p.ciudad = request.POST.get("ciudad")
        p.direccion = request.POST.get("direccion")
        p.tipo_contacto_id = request.POST.get("tipo_contacto")
        p.tipo_doc_id = request.POST.get("tipo_doc")
        
        es_natural = TipoContacto.objects.get(id=p.tipo_contacto_id).nombre_tipo == "Persona Natural"
        if es_natural:
            p.nombre = request.POST.get("nombre")
            p.apellido = request.POST.get("apellido")
            p.razon_social = None
            p.nombre_rep_legal = None
        else:
            p.nombre = None
            p.apellido = None
            p.razon_social = request.POST.get("razon_social")
            p.nombre_rep_legal = request.POST.get("nombre_rep_legal")

        if not (p.nombre if p.nombre else p.razon_social): error = "Nombre o Razón Social es obligatorio."
        elif Contacto.objects.filter(documento_nit=p.documento_nit).exclude(id=p.id).exists():
            error = f"El documento/NIT '{p.documento_nit}' ya está registrado en otro contacto."
        elif not p.correo and not p.celular: error = "Email o Celular obligatorio."
        else:
            # Comparar y loggear cambios
            now_str = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')
            cambios_log = []
            
            # Mapeo de campos a nombres legibles
            fields = {
                'documento_nit': 'Número ID/NIT', 'correo': 'Email', 'celular': 'Celular',
                'ciudad': 'Ciudad', 'direccion': 'Dirección', 'nombre': 'Nombre',
                'apellido': 'Apellido', 'razon_social': 'Razón Social', 'nombre_rep_legal': 'Rep. Legal'
            }
            
            for field, label in fields.items():
                old_val = str(old.get(field) or "").strip()
                new_val = str(getattr(p, field) or "").strip()
                if old_val != new_val:
                    cambios_log.append(f"[{now_str}] Modificó {label} por {usuario_logueado.nombre_usuario}")
            
            if not cambios_log: # Si no hubo cambios en campos, log genérico
                cambios_log.append(f"[{now_str}] Editado por {usuario_logueado.nombre_usuario}")
                
            for log in cambios_log:
                p.historial_cambios = (p.historial_cambios + "\n" + log) if p.historial_cambios else log
            
            p.save()
            return redirect('/')
                
    return render(request, "editar_contacto.html", {
        "c": p, "error": error, 
        "tipos_contacto": TipoContacto.objects.all(),
        "tipos_doc": TipoIdentificacion.objects.all(),
        "usuario_logueado": usuario_logueado
    })

def cambiar_estado(request, id_contacto):
    if not request.session.get('user_id'): return redirect('/login/')
    c = get_object_or_404(Contacto, id=id_contacto)
    c.activo = not c.activo
    accion = "Reactivado" if c.activo else "Inactivado"
    log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] {accion} por {Usuario.objects.get(id=request.session.get('user_id')).nombre_usuario}"
    c.historial_cambios = (c.historial_cambios + "\n" + log) if c.historial_cambios else log
    c.save()
    
    # Redirigir de vuelta a la página de origen para una mejor experiencia
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('/')


def deduplicar_correos(contacto):
    """Elimina correos duplicados para un contacto."""
    tipo_correo = TipoInteraccion.objects.filter(nombre_tipo='Correo').first()
    if not tipo_correo:
        return
        
    import re
    def clean_html(text):
        return re.sub(r'<[^>]*>', '', text or '')

    seen = [] # list of tuples: (mensaje_id, asunto_normalized, fecha_interaccion, body_snippet_normalized)
    duplicates_to_delete = []

    # Ordenamos por id para conservar el registro original (el primero creado)
    correos = Interaccion.objects.filter(contacto=contacto, tipo_interaccion=tipo_correo).order_by('id')
    for c in correos:
        mid = (c.mensaje_id or '').strip().lower()
        asunto = (c.asunto or '').strip().lower()
        if not asunto and c.detalle_actividad:
            if c.detalle_actividad.startswith("Asunto:"):
                lines = c.detalle_actividad.split("\n", 1)
                asunto = lines[0].replace("Asunto:", "").strip().lower()

        # Limpiar texto del cuerpo para comparar contenido real
        body_text = clean_html(c.detalle_actividad or '')
        body_text = "".join(body_text.split()).lower()
        body_snippet = body_text[:100]

        is_duplicate = False
        
        # 1. Comparar por mensaje_id si existe
        if mid:
            for s_mid, _, _, _ in seen:
                if s_mid == mid:
                    is_duplicate = True
                    break

        # 2. Si no coincide por message_id, comparar por asunto + fecha cercana, o asunto + contenido idéntico
        if not is_duplicate:
            for s_mid, s_asunto, s_date, s_body in seen:
                if asunto and s_asunto == asunto:
                    date_diff = abs((c.fecha_interaccion - s_date).total_seconds()) if c.fecha_interaccion and s_date else 999999
                    if date_diff < 300:
                        is_duplicate = True
                        break
                    if body_snippet and s_body == body_snippet:
                        is_duplicate = True
                        break

        if is_duplicate:
            duplicates_to_delete.append(c.id)
        else:
            seen.append((mid, asunto, c.fecha_interaccion, body_snippet))

    if duplicates_to_delete:
        Interaccion.objects.filter(id__in=duplicates_to_delete).delete()
        print(f"[Deduplicar] Eliminados {len(duplicates_to_delete)} correos duplicados para el contacto {contacto.id}")

def sincronizar_correos_imap(request, contacto, usuario_logueado):
    """Sincroniza correos entrantes Y enviados para un contacto específico."""
    if not contacto.correo:
        print(f"[IMAP] Contacto {contacto.id} no tiene correo registrado.")
        return 0

    try:
        import re
        def unescape_unicode(text):
            return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)

        # Conectar al servidor IMAP
        mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)

        # Asegurar que el tipo 'Correo' exista
        tipo_correo, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Correo')
        count = 0

        def procesar_correos(mail_conn, folder, search_criteria, tipo_com):
            """Procesa correos de una carpeta específica."""
            nonlocal count
            try:
                status, _ = mail_conn.select(folder, readonly=True)
                if status != "OK":
                    print(f"[IMAP] No se pudo abrir carpeta: {folder}")
                    return
            except Exception as e:
                print(f"[IMAP] Error abriendo carpeta {folder}: {e}")
                return

            try:
                status, messages_ids = mail_conn.search(None, search_criteria)
                if status != "OK" or not messages_ids[0]:
                    return
            except Exception as e:
                print(f"[IMAP] Error buscando en {folder}: {e}")
                return

            for num in messages_ids[0].split():
                try:
                    status, data = mail_conn.fetch(num, "(RFC822)")
                    if status != "OK":
                        continue

                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    # Extraer Asunto
                    raw_subject = msg.get("Subject", "Sin Asunto")
                    asunto_parts = decode_header(raw_subject)
                    asunto = ""
                    for part, enc in asunto_parts:
                        if isinstance(part, bytes):
                            asunto += part.decode(enc if enc else "utf-8", errors="replace")
                        else:
                            asunto += part

                    # Extraer cuerpo
                    cuerpo = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            content_disposition = str(part.get("Content-Disposition"))
                            if content_type == "text/plain" and "attachment" not in content_disposition:
                                charset = part.get_content_charset() or "utf-8"
                                try:
                                    payload = part.get_payload(decode=True)
                                    if payload:
                                        cuerpo = payload.decode(charset, errors="replace")
                                except:
                                    try:
                                        cuerpo = part.get_payload(decode=True).decode("utf-8", errors="replace")
                                    except:
                                        cuerpo = "[No se pudo leer el contenido]"
                                break
                    else:
                        charset = msg.get_content_charset() or "utf-8"
                        try:
                            payload = msg.get_payload(decode=True)
                            if payload:
                                cuerpo = payload.decode(charset, errors="replace")
                        except:
                            try:
                                cuerpo = msg.get_payload(decode=True).decode("utf-8", errors="replace")
                            except:
                                cuerpo = "[No se pudo leer el contenido]"

                    # Obtener ID del mensaje único
                    mid = msg.get("Message-ID")
                    if mid:
                        mid = str(mid).strip().strip('<>')
                    else:
                        import hashlib
                        date_hdr = msg.get("Date") or ""
                        hash_src = f"{contacto.correo}-{asunto}-{cuerpo[:500]}-{date_hdr}"
                        mid = "hash-" + hashlib.md5(hash_src.encode('utf-8', errors='ignore')).hexdigest()

                    clean_detalle = unescape_unicode(f"Asunto: {asunto}\n\n{cuerpo}") if asunto else unescape_unicode(cuerpo)

                    # Verificar si ya existe por ID de mensaje o por contenido idéntico
                    if Interaccion.objects.filter(mensaje_id=mid).exists():
                        continue
                    if Interaccion.objects.filter(contacto=contacto, tipo_interaccion=tipo_correo, detalle_actividad=clean_detalle).exists():
                        continue

                    # Buscar actividad activa
                    active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()

                    if not active_activity:
                        if not clean_detalle.startswith("interacción suelta."):
                            clean_detalle = f"interacción suelta. {clean_detalle}"
                    else:
                        if clean_detalle.startswith("interacción suelta."):
                            clean_detalle = clean_detalle.replace("interacción suelta.", "", 1).strip()

                    # Obtener fecha real del correo
                    from email.utils import parsedate_to_datetime
                    real_datetime = timezone.now()
                    date_hdr = msg.get("Date")
                    if date_hdr:
                        try:
                            real_datetime = parsedate_to_datetime(date_hdr)
                        except Exception as e:
                            print(f"[IMAP] Error parsing date '{date_hdr}': {e}")

                    # Crear Interacción
                    inter_obj = Interaccion.objects.create(
                        contacto=contacto,
                        usuario_responsable=usuario_logueado,
                        tipo_interaccion=tipo_correo,
                        detalle_actividad=clean_detalle,
                        tipo_comunicacion=tipo_com,
                        mensaje_id=mid,
                        parent=active_activity,
                        historial_cambios=f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Sincronizada automáticamente vía IMAP ({tipo_com})",
                        canal_comunicacion=tipo_correo,
                        duracion_minutos=1,
                        temperatura_emocional=3
                    )
                    inter_obj.fecha_interaccion = real_datetime
                    inter_obj.save()
                    count += 1
                except Exception as e:
                    print(f"[IMAP] Error procesando mensaje {num} en {folder}: {e}")
                    continue

        # 1. Buscar correos RECIBIDOS del contacto (en inbox)
        procesar_correos(mail, "inbox", f'(FROM "{contacto.correo}")', 'Entrante')

        # 2. Buscar correos ENVIADOS al contacto (en carpeta de enviados)
        # Gmail usa "[Gmail]/Sent Mail" o "[Gmail]/Enviados" según el idioma
        carpetas_enviados = ['"[Gmail]/Sent Mail"', '"[Gmail]/Enviados"', '"Sent"', '"INBOX.Sent"']
        for carpeta in carpetas_enviados:
            try:
                status, _ = mail.select(carpeta, readonly=True)
                if status == "OK":
                    # Restaurar y procesar
                    procesar_correos(mail, carpeta, f'(TO "{contacto.correo}")', 'Saliente')
                    break
            except:
                continue

        mail.logout()
        print(f"[IMAP] Sincronizados {count} correos nuevos para contacto {contacto.id} ({contacto.correo})")
        return count
    except Exception as e:
        print(f"[IMAP] Error general: {str(e)}")
        return -1

def detalle_contacto(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion: return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    
    contacto = get_object_or_404(Contacto, id=id_contacto)
    
    # Programmatic migration run to make sure all analytics columns are applied
    try:
        from django.core.management import call_command
        call_command('migrate', interactive=False)
    except Exception as e:
        print(f"[Migration Error] {e}")
        
    # Write debug interactions to a scratch file for inspection
    try:
        import os
        debug_path = r"c:\Users\Jary\OneDrive\Documentos\Pruebas\scratch\debug_inters.txt"
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(f"Contacto: {contacto}\n")
            f.write(f"Total interacciones: {Interaccion.objects.filter(contacto=contacto).count()}\n")
            for inter in Interaccion.objects.filter(contacto=contacto):
                f.write(f"ID: {inter.id} | Tipo: {inter.tipo_interaccion.nombre_tipo} | Canal: {inter.canal_comunicacion.nombre_tipo if inter.canal_comunicacion else 'None'} | Duracion: {inter.duracion_minutos} | Temp: {inter.temperatura_emocional} | Estado: {inter.estado}\n")
    except Exception as e:
        print(f"[Debug log error] {e}")
    
    # Deduplicar correos del contacto
    deduplicar_correos(contacto)
    
    if request.method == "POST":
        # Opción Registrar Llamada Automática (vía AJAX)
        if request.POST.get('accion') == 'registrar_llamada':
            tipo_llamada, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Llamada')
            num = request.POST.get('numero', 'desconocido')
            motivo = request.POST.get('detalle', '').strip()
            
            detalle = f"[Motivo]: {motivo}" if motivo else f"[SISTEMA] Llamada iniciada al número {num} desde el CRM mediante marcación directa."
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            
            if not active_activity:
                if not detalle.startswith("interacción suelta."):
                    detalle = f"interacción suelta. {detalle}"
            else:
                if detalle.startswith("interacción suelta."):
                    detalle = detalle.replace("interacción suelta.", "", 1).strip()
            
            new_call = Interaccion.objects.create(
                contacto=contacto,
                usuario_responsable=usuario_logueado,
                tipo_interaccion=tipo_llamada,
                detalle_actividad=detalle,
                estado='En curso',
                fecha_reunion=timezone.localtime(timezone.now()).date(),
                hora_reunion=timezone.localtime(timezone.now()).time(),
                parent=active_activity,
                historial_cambios=f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Llamada iniciada por {usuario_logueado.nombre_usuario}"
            )
            return JsonResponse({'status': 'success', 'call_id': new_call.id})

        # Opción Programar Llamada
        if request.POST.get('accion') == 'programar_llamada':
            tipo_llamada, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Llamada')
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            
            detalle = request.POST.get('detalle', '')
            if not active_activity:
                if not detalle.startswith("interacción suelta."):
                    detalle = f"interacción suelta. {detalle}"
            else:
                if detalle.startswith("interacción suelta."):
                    detalle = detalle.replace("interacción suelta.", "", 1).strip()
            
            canal_llamada, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Llamada')
            duracion_val = request.POST.get('duracion_minutos')
            duracion_min = int(duracion_val) if duracion_val else None
            temp_val = request.POST.get('temperatura_emocional')
            temp_emocional = int(temp_val) if temp_val else None

            Interaccion.objects.create(
                contacto=contacto,
                usuario_responsable=usuario_logueado,
                tipo_interaccion=tipo_llamada,
                detalle_actividad=detalle,
                fecha_reunion=request.POST.get('fecha_reunion') or None,
                hora_reunion=request.POST.get('hora_reunion') or None,
                estado='Programada',
                parent=active_activity,
                historial_cambios=f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Llamada programada por {usuario_logueado.nombre_usuario}",
                canal_comunicacion=canal_llamada,
                duracion_minutos=duracion_min,
                temperatura_emocional=temp_emocional
            )
            return redirect('detalle_contacto', id_contacto=id_contacto)

        # Iniciar Llamada Programada
        if request.POST.get('accion') == 'iniciar_llamada_programada':
            id_inter = request.POST.get('interaccion_id')
            call = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            call.estado = 'En curso'
            call.fecha_interaccion = timezone.now()
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            if active_activity and not call.parent:
                call.parent = active_activity
                if call.detalle_actividad and call.detalle_actividad.startswith("interacción suelta."):
                    call.detalle_actividad = call.detalle_actividad.replace("interacción suelta.", "", 1).strip()
                if call.asunto and call.asunto.startswith("interacción suelta."):
                    call.asunto = call.asunto.replace("interacción suelta.", "", 1).strip()
            elif not active_activity and not call.parent:
                if call.detalle_actividad and not call.detalle_actividad.startswith("interacción suelta."):
                    call.detalle_actividad = f"interacción suelta. {call.detalle_actividad}"
                if call.asunto and not call.asunto.startswith("interacción suelta."):
                    call.asunto = f"interacción suelta. {call.asunto}"
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Llamada iniciada por {usuario_logueado.nombre_usuario}"
            call.historial_cambios = (call.historial_cambios + "\n" + log) if call.historial_cambios else log
            call.save()
            
            messages.success(request, "Llamada programada iniciada.")
            return redirect(f'/contacto/{id_contacto}/?tab=llamadas')

        # Opción Eliminar Interacción
        if request.POST.get('accion') == 'eliminar_interaccion':
            id_inter = request.POST.get('interaccion_id')
            inter_a_eliminar = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            tipo_n = inter_a_eliminar.tipo_interaccion.nombre_tipo
            
            # Si es una nota, desactivamos en lugar de borrar
            if tipo_n == 'Nota':
                inter_a_eliminar.estado = 'Inactiva'
                log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Nota marcada como Inactiva por {usuario_logueado.nombre_usuario}"
                inter_a_eliminar.historial_cambios = (inter_a_eliminar.historial_cambios + "\n" + log) if inter_a_eliminar.historial_cambios else log
                inter_a_eliminar.save()
                messages.success(request, "Nota desactivada correctamente.")
            else:
                inter_a_eliminar.delete()
                messages.success(request, f"{tipo_n} eliminada correctamente.")
            
            # Redirigir a la pestaña correspondiente
            tabname = 'correos' if tipo_n == 'Correo' else ('notas' if tipo_n == 'Nota' else ('reuniones' if tipo_n == 'Reunión' else 'actividad'))
            return redirect(f'/contacto/{id_contacto}/?tab={tabname}')
        # Cancelar reunión
        if request.POST.get('accion') == 'cancelar_reunion':
            id_inter = request.POST.get('interaccion_id')
            motivo = request.POST.get('motivo_cancelacion', '').strip()
            reunion = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            reunion.estado = 'Cancelada'
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            if active_activity and not reunion.parent:
                reunion.parent = active_activity
                
            if reunion.parent:
                if reunion.detalle_actividad and reunion.detalle_actividad.startswith("interacción suelta."):
                    reunion.detalle_actividad = reunion.detalle_actividad.replace("interacción suelta.", "", 1).strip()
                if reunion.asunto and reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = reunion.asunto.replace("interacción suelta.", "", 1).strip()
            else:
                if reunion.detalle_actividad and not reunion.detalle_actividad.startswith("interacción suelta."):
                    reunion.detalle_actividad = f"interacción suelta. {reunion.detalle_actividad}"
                if reunion.asunto and not reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = f"interacción suelta. {reunion.asunto}"
            
            if motivo:
                reunion.detalle_actividad = f"{reunion.detalle_actividad}\n\n[CANCELADA] Motivo: {motivo}"
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Cancelada por {usuario_logueado.nombre_usuario}"
            reunion.historial_cambios = (reunion.historial_cambios + "\n" + log) if reunion.historial_cambios else log
            
            reunion.save()
            messages.success(request, "Reunión cancelada correctamente.")
            return redirect(f'/contacto/{id_contacto}/?tab=reuniones')

        # Finalizar Llamada
        if request.POST.get('accion') == 'finalizar_llamada':
            id_inter = request.POST.get('interaccion_id')
            call = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            call.estado = 'Finalizada'
            
            # Save es_exitosa status
            exitosa_val = request.POST.get('es_exitosa', 'True')
            call.es_exitosa = (exitosa_val == 'True')
            
            # Calculate duration
            duration_seconds = (timezone.now() - call.fecha_interaccion).total_seconds()
            if duration_seconds < 0:
                duration_seconds = 0
            minutes, seconds = divmod(int(duration_seconds), 60)
            duration_str = f"{minutes} min {seconds} s" if minutes > 0 else f"{seconds} s"
            
            desc = request.POST.get('detalle', '').strip()
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            if active_activity and not call.parent:
                call.parent = active_activity
                
            if call.parent:
                if desc.startswith("interacción suelta."):
                    desc = desc.replace("interacción suelta.", "", 1).strip()
                if call.detalle_actividad and call.detalle_actividad.startswith("interacción suelta."):
                    call.detalle_actividad = call.detalle_actividad.replace("interacción suelta.", "", 1).strip()
                if call.asunto and call.asunto.startswith("interacción suelta."):
                    call.asunto = call.asunto.replace("interacción suelta.", "", 1).strip()
            else:
                if not desc.startswith("interacción suelta."):
                    desc = f"interacción suelta. {desc}"
            
            final_detail = f"{desc}\n\n[Duración de la llamada]: {duration_str}"
            call.detalle_actividad = final_detail
            
            # Save analytics fields
            canal_llamada, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Llamada')
            call.canal_comunicacion = canal_llamada
            duracion_val = request.POST.get('duracion_minutos')
            call.duracion_minutos = int(duracion_val) if duracion_val else max(1, minutes)
            temp_val = request.POST.get('temperatura_emocional')
            if temp_val:
                call.temperatura_emocional = int(temp_val)
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Llamada finalizada. Duración: {duration_str} por {usuario_logueado.nombre_usuario}"
            call.historial_cambios = (call.historial_cambios + "\n" + log) if call.historial_cambios else log
            
            call.save()
            messages.success(request, f"Llamada finalizada correctamente (Duración: {duration_str}).")
            return redirect(f'/contacto/{id_contacto}/?tab=llamadas')

        # Finalizar Actividad
        if request.POST.get('accion') == 'finalizar_actividad':
            id_inter = request.POST.get('interaccion_id')
            actividad = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            actividad.estado = 'Finalizada'
            
            informe = request.POST.get('informe_final', '').strip()
            if informe:
                actividad.detalle_actividad = f"{actividad.detalle_actividad}\n\n[INFORME FINAL]: {informe}"
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Actividad Finalizada por {usuario_logueado.nombre_usuario}"
            actividad.historial_cambios = (actividad.historial_cambios + "\n" + log) if actividad.historial_cambios else log
            
            actividad.save()
            messages.success(request, "Actividad finalizada correctamente con informe.")
            return redirect(f'/contacto/{id_contacto}/?tab=actividad')

        # Finalizar reunión
        if request.POST.get('accion') == 'finalizar_reunion':
            id_inter = request.POST.get('interaccion_id')
            reunion = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            reunion.estado = 'Finalizada'
            reunion.fecha_interaccion = timezone.now()
            reunion.fecha_reunion = timezone.localtime(timezone.now()).date()
            reunion.hora_reunion = timezone.localtime(timezone.now()).time()
            
            desc = request.POST.get('detalle', '').strip()
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            if active_activity and not reunion.parent:
                reunion.parent = active_activity
                
            if reunion.parent:
                if desc.startswith("interacción suelta."):
                    desc = desc.replace("interacción suelta.", "", 1).strip()
                if reunion.detalle_actividad and reunion.detalle_actividad.startswith("interacción suelta."):
                    reunion.detalle_actividad = reunion.detalle_actividad.replace("interacción suelta.", "", 1).strip()
                if reunion.asunto and reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = reunion.asunto.replace("interacción suelta.", "", 1).strip()
            else:
                if reunion.detalle_actividad and not reunion.detalle_actividad.startswith("interacción suelta."):
                    reunion.detalle_actividad = f"interacción suelta. {reunion.detalle_actividad}"
                if reunion.asunto and not reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = f"interacción suelta. {reunion.asunto}"
            
            if desc:
                reunion.detalle_actividad = f"{reunion.detalle_actividad}\n\n[RESUMEN FINAL]: {desc}"
            
            # Save analytics fields
            canal_id = request.POST.get('canal_comunicacion')
            if canal_id:
                try:
                    reunion.canal_comunicacion = TipoInteraccion.objects.get(id=canal_id)
                except TipoInteraccion.DoesNotExist:
                    pass
            
            duracion_val = request.POST.get('duracion_minutos')
            if duracion_val:
                reunion.duracion_minutos = int(duracion_val)
                
            temp_val = request.POST.get('temperatura_emocional')
            if temp_val:
                reunion.temperatura_emocional = int(temp_val)
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Finalizada por {usuario_logueado.nombre_usuario}"
            reunion.historial_cambios = (reunion.historial_cambios + "\n" + log) if reunion.historial_cambios else log
            
            reunion.save()
            messages.success(request, "Reunión marcada como finalizada.")
            return redirect(f'/contacto/{id_contacto}/?tab=reuniones')

        # Cancelar Actividad
        if request.POST.get('accion') == 'cancelar_actividad':
            id_inter = request.POST.get('interaccion_id')
            motivo = request.POST.get('motivo_cancelacion', '').strip()
            actividad = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            actividad.estado = 'Cancelada'
            if motivo:
                actividad.detalle_actividad = f"{actividad.detalle_actividad}\n\n[CANCELADA] Motivo: {motivo}"
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Cancelada por {usuario_logueado.nombre_usuario}"
            actividad.historial_cambios = (actividad.historial_cambios + "\n" + log) if actividad.historial_cambios else log
            
            actividad.save()
            messages.success(request, "Actividad cancelada correctamente.")
            return redirect(f'/contacto/{id_contacto}/?tab=actividad')

        # Editar reunión
        if request.POST.get('accion') == 'editar_reunion':
            id_inter = request.POST.get('interaccion_id')
            reunion = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            
            reunion.asunto = request.POST.get('asunto', reunion.asunto)
            reunion.fecha_reunion = request.POST.get('fecha_reunion') or None
            reunion.hora_reunion = request.POST.get('hora_reunion') or None
            reunion.modalidad = request.POST.get('modalidad', reunion.modalidad)
            reunion.direccion = request.POST.get('direccion', '') if reunion.modalidad == 'Presencial' else None
            reunion.enlace_reunion = request.POST.get('enlace_reunion', '') if reunion.modalidad == 'Virtual' else None
            
            detalle = request.POST.get('detalle', reunion.detalle_actividad)
            
            active_activity = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
            if active_activity and not reunion.parent:
                reunion.parent = active_activity
                
            if reunion.parent:
                if detalle.startswith("interacción suelta."):
                    detalle = detalle.replace("interacción suelta.", "", 1).strip()
                if reunion.asunto and reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = reunion.asunto.replace("interacción suelta.", "", 1).strip()
            else:
                if not detalle.startswith("interacción suelta."):
                    detalle = f"interacción suelta. {detalle}"
                if reunion.asunto and not reunion.asunto.startswith("interacción suelta."):
                    reunion.asunto = f"interacción suelta. {reunion.asunto}"
                    
            reunion.detalle_actividad = detalle
            
            log = f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Editada por {usuario_logueado.nombre_usuario}"
            reunion.historial_cambios = (reunion.historial_cambios + "\n" + log) if reunion.historial_cambios else log
            
            reunion.save()
            messages.success(request, "Reunión actualizada correctamente.")
            return redirect(f'/contacto/{id_contacto}/?tab=reuniones')

        # Opción Sincronizar Correos
        if request.POST.get('accion') == 'sincronizar_correos':
            nuevos = sincronizar_correos_imap(request, contacto, usuario_logueado)
            if nuevos >= 0:
                messages.success(request, f"Se han sincronizado {nuevos} correos nuevos.")
            else:
                messages.error(request, "Hubo un problema al conectar con el servidor de correo.")
            return redirect(f'/contacto/{id_contacto}/?tab=correos')

        # Verificar si se especificó el nombre del tipo (para el modal de notas y correos)
        tipo_nombre = request.POST.get('tipo_interaccion_nombre')
        if tipo_nombre:
            tipo_obj, _ = TipoInteraccion.objects.get_or_create(nombre_tipo=tipo_nombre)
        else:
            tipo_id = request.POST.get('tipo_interaccion')
            tipo_obj = get_object_or_404(TipoInteraccion, id=tipo_id)
        
        es_actividad_principal = request.POST.get('es_actividad_principal') == '1'
        target_type_name = tipo_obj.nombre_tipo
        if es_actividad_principal:
            tipo_obj, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Actividad')
        
        # Capturar asunto si es un correo o una reunión
        asunto = request.POST.get('asunto', '')
        detalle = request.POST.get('detalle', '')
        
        if es_actividad_principal:
            fase_actividad = request.POST.get('fase_actividad', '')
            tipo_proyecto = request.POST.get('tipo_proyecto', '')
            if tipo_proyecto == 'otros':
                tipo_proyecto = request.POST.get('tipo_proyecto_otro', '')
            asunto = tipo_proyecto or 'Otro'
            if fase_actividad:
                detalle = f"[{fase_actividad}] {detalle}"
        
        attachments_html = request.POST.get('attachments_html', '')
        
        db_detalle = detalle + attachments_html
        # Si hay asunto de correo, lo prefijamos al detalle
        m_detalle = f"Asunto: {asunto}\n\n{db_detalle}" if (asunto and tipo_nombre == 'Correo') else (db_detalle or asunto or '-')

        # Campos de reunión
        fecha_reunion = request.POST.get('fecha_reunion') or None
        hora_reunion = request.POST.get('hora_reunion') or None
        
        parent_id = request.POST.get('parent_id')
        
        if parent_id:
            parent_obj = Interaccion.objects.filter(id=parent_id).first()
        elif not es_actividad_principal:
            # Si no es actividad principal ni tiene parent, buscamos la actividad abierta
            parent_obj = Interaccion.objects.filter(contacto=contacto, parent__isnull=True, estado='Abierta', tipo_interaccion__nombre_tipo='Actividad').order_by('-fecha_interaccion').first()
        else:
            parent_obj = None

        if not parent_obj and not es_actividad_principal:
            if not m_detalle.startswith("interacción suelta."):
                m_detalle = f"interacción suelta. {m_detalle}"
            if asunto and not asunto.startswith("interacción suelta."):
                asunto = f"interacción suelta. {asunto}"

        if es_actividad_principal:
            estado_inter = 'Abierta'
            prefix = 'Actividad iniciada'
        else:
            estado_inter = 'Programada' if tipo_obj.nombre_tipo == 'Reunión' else 'Finalizada'
            prefix = 'Programada' if tipo_obj.nombre_tipo == 'Reunión' else 'Registrada'
            
        # Capture analytics fields from POST
        canal_id = request.POST.get('canal_comunicacion')
        duracion_val = request.POST.get('duracion_minutos')
        temp_val = request.POST.get('temperatura_emocional')

        canal_obj = None
        if canal_id:
            try:
                canal_obj = TipoInteraccion.objects.get(id=canal_id)
            except TipoInteraccion.DoesNotExist:
                pass
        
        # Fallback to current type if it is a communication channel
        if not canal_obj and tipo_obj.nombre_tipo in ['Llamada', 'Reunión', 'Correo']:
            canal_obj = tipo_obj
        elif not canal_obj and tipo_nombre in ['Llamada', 'Reunión', 'Correo']:
            canal_obj, _ = TipoInteraccion.objects.get_or_create(nombre_tipo=tipo_nombre)

        duracion_minutos = None
        if duracion_val:
            try:
                duracion_minutos = int(duracion_val)
            except ValueError:
                pass
        
        # Default duration to 1 for email if not specified
        if not duracion_minutos and (tipo_obj.nombre_tipo == 'Correo' or tipo_nombre == 'Correo'):
            duracion_minutos = 1

        temperatura_emocional = None
        if temp_val:
            try:
                temperatura_emocional = int(temp_val)
            except ValueError:
                pass

        inter = Interaccion.objects.create(
            contacto=contacto,
            usuario_responsable=usuario_logueado,
            tipo_interaccion=tipo_obj,
            detalle_actividad=m_detalle,
            estado=estado_inter,
            modalidad=request.POST.get('modalidad', ''),
            asunto=asunto if asunto else None,
            fecha_reunion=fecha_reunion,
            hora_reunion=hora_reunion,
            direccion=request.POST.get('direccion', '') or None,
            enlace_reunion=request.POST.get('enlace_reunion', '') or None,
            parent=parent_obj,
            historial_cambios=f"[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] {prefix} por {usuario_logueado.nombre_usuario}",
            canal_comunicacion=canal_obj,
            duracion_minutos=duracion_minutos,
            temperatura_emocional=temperatura_emocional
        )

        # Redirección inteligente por tipo de interacción
        if es_actividad_principal:
            messages.success(request, "Actividad principal iniciada.")
            if target_type_name == 'Reunión': tabname = 'reuniones'
            elif target_type_name == 'Correo': tabname = 'correos'
            elif target_type_name == 'Llamada': tabname = 'llamadas'
            else: tabname = 'actividad'
            
            open_modal = 'reunion' if target_type_name == 'Reunión' else ('correo' if target_type_name == 'Correo' else ('llamada' if target_type_name == 'Llamada' else ''))
            redirect_url = f'/contacto/{id_contacto}/?tab={tabname}'
            if open_modal:
                redirect_url += f'&open_modal={open_modal}'
            return redirect(redirect_url)

        if tipo_obj.nombre_tipo == 'Correo':
            destinatario = request.POST.get('para_correo') or contacto.correo
            if destinatario:
                try:
                    html_body = detalle
                    firma = getattr(usuario_logueado, 'firma_digital', None)
                    if firma and firma.html_content:
                        html_body += f"<br><br>{firma.html_content}"

                    attachments_list = []
                    import re, base64, uuid

                    # Extraer imágenes base64 inline → adjuntos CID
                    def replace_base64(m):
                        ext = m.group(1)
                        b64 = m.group(2)
                        cid = str(uuid.uuid4())
                        attachments_list.append({"name": f"img.{ext}", "content": b64, "cid": cid})
                        return f'src="cid:{cid}"'
                    html_body = re.sub(r'src=["\']data:image/([^;]+);base64,([^"\' >]+)["\']', replace_base64, html_body)

                    # Adjuntar archivos del servidor
                    adjuntos_paths = request.POST.getlist('adjuntos_correo_paths')
                    if not adjuntos_paths:
                        paths_str = request.POST.get('adjuntos_correo_paths', '')
                        if paths_str:
                            adjuntos_paths = [p.strip() for p in paths_str.split(',') if p.strip()]
                    for p in adjuntos_paths:
                        if os.path.exists(p):
                            with open(p, 'rb') as f:
                                b64 = base64.b64encode(f.read()).decode()
                            attachments_list.append({"name": os.path.basename(p), "content": b64})

                    email_err = enviar_correo_seguro(
                        asunto if asunto else f"Mensaje de {usuario_logueado.nombre_usuario}",
                        html_body,
                        [destinatario],
                        html_content=html_body,
                        attachments=attachments_list if attachments_list else None
                    )

                    if email_err:
                        inter.historial_cambios = (inter.historial_cambios or '') + f"\n[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] ERROR: {email_err}"
                        inter.save()
                        messages.error(request, f"Error al enviar correo: {email_err}")
                    else:
                        inter.historial_cambios = (inter.historial_cambios or '') + f"\n[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] Correo enviado exitosamente a {destinatario}"
                        inter.save()
                        messages.success(request, f"¡Correo enviado con éxito a {destinatario}")
                except Exception as e:
                    inter.historial_cambios = (inter.historial_cambios or '') + f"\n[{timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}] ERROR: {str(e)}"
                    inter.save()
                    messages.error(request, f"Error al enviar correo: {str(e)}")
            else:
                messages.warning(request, "El contacto no tiene correo electrónico registrado.")
            return redirect(f'/contacto/{id_contacto}/?tab=correos')
        elif tipo_obj.nombre_tipo == 'Llamada':
            messages.success(request, f"Actividad de llamada registrada. Se abrirá tu aplicación de teléfono.")
            return redirect(f'/contacto/{id_contacto}/?tab=llamadas&open_tel=1')
        else:
            messages.success(request, f"{tipo_obj.nombre_tipo} registrada correctamente.")
            # Redirección inteligente por pestaña
            if tipo_obj.nombre_tipo == 'Nota': tabname = 'notas'
            elif tipo_obj.nombre_tipo == 'Reunión': tabname = 'reuniones'
            elif tipo_obj.nombre_tipo == 'Tarea': tabname = 'tareas'
            elif tipo_obj.nombre_tipo == 'Correo': tabname = 'correos'
            elif tipo_obj.nombre_tipo == 'Llamada': tabname = 'llamadas'
            else: tabname = 'actividad'
            
            return redirect(f'/contacto/{id_contacto}/?tab={tabname}')
            
    interacciones = Interaccion.objects.filter(contacto=contacto).order_by('-fecha_interaccion', '-id')
    interacciones_asc = Interaccion.objects.filter(contacto=contacto).order_by('-fecha_interaccion', '-id')
    interacciones_roots = interacciones.filter(parent__isnull=True)
    tipos_interaccion = TipoInteraccion.objects.all()
    
    # --- CALCULATE STATISTICS FOR DASHBOARD ---
    import json
    from django.db.models import Avg, Sum, Q
    from datetime import timedelta

    # Helper to resolve type/val defaults
    reg_date = contacto.fecha_registro or timezone.now()
    reg_local = timezone.localtime(reg_date)
    now_local = timezone.localtime(timezone.now())

    available_years = list(range(reg_local.year, now_local.year + 1))
    
    available_months = []
    curr_year = reg_local.year
    curr_month = reg_local.month
    
    month_names = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    
    while (curr_year < now_local.year) or (curr_year == now_local.year and curr_month <= now_local.month):
        val_str = f"{curr_year}-{curr_month:02d}"
        label_str = f"{month_names[curr_month - 1]} {curr_year}"
        available_months.append({'value': val_str, 'label': label_str})
        curr_month += 1
        if curr_month > 12:
            curr_month = 1
            curr_year += 1
    available_months.reverse()

    def resolve_filter_params(filter_type, filter_val):
        if filter_type not in ['desde_creacion', 'anio', 'mes', 'dia']:
            filter_type = 'desde_creacion'
        if filter_type == 'desde_creacion':
            filter_val = ''
        elif filter_type == 'anio':
            if not filter_val:
                filter_val = str(now_local.year)
        elif filter_type == 'mes':
            if not filter_val:
                filter_val = f"{now_local.year}-{now_local.month:02d}"
        elif filter_type == 'dia':
            if not filter_val:
                filter_val = '7'
            else:
                try:
                    days = int(filter_val)
                    if days < 7:
                        filter_val = '7'
                except (ValueError, TypeError):
                    filter_val = '7'
        return filter_type, filter_val

    def apply_stats_filter(queryset, filter_type, filter_val):
        if filter_type == 'anio':
            try:
                year = int(filter_val)
                q_event = (
                    (Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión']) | Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    (Q(fecha_reunion__year=year) | Q(fecha_reunion__isnull=True, fecha_interaccion__year=year))
                )
                q_other = (
                    ~Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión']) & 
                    (Q(canal_comunicacion__isnull=True) | ~Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    Q(fecha_interaccion__year=year)
                )
                return queryset.filter(q_event | q_other)
            except (ValueError, TypeError):
                pass
        elif filter_type == 'mes':
            try:
                parts = filter_val.split('-')
                year = int(parts[0])
                month = int(parts[1])
                q_event = (
                    (Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión']) | Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    (Q(fecha_reunion__year=year, fecha_reunion__month=month) | Q(fecha_reunion__isnull=True, fecha_interaccion__year=year, fecha_interaccion__month=month))
                )
                q_other = (
                    ~Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión']) & 
                    (Q(canal_comunicacion__isnull=True) | ~Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    Q(fecha_interaccion__year=year, fecha_interaccion__month=month)
                )
                return queryset.filter(q_event | q_other)
            except (ValueError, TypeError, IndexError):
                pass
        elif filter_type == 'dia':
            try:
                days = int(filter_val)
                if days < 7:
                    days = 7
                limit_date = timezone.now() - timedelta(days=days)
                limit_date_date = limit_date.date()
                q_event = (
                    (Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión']) | Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    (Q(fecha_reunion__gte=limit_date_date) | Q(fecha_reunion__isnull=True, fecha_interaccion__gte=limit_date))
                )
                q_other = (
                    ~Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión']) & 
                    (Q(canal_comunicacion__isnull=True) | ~Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión'])) &
                    Q(fecha_interaccion__gte=limit_date)
                )
                return queryset.filter(q_event | q_other)
            except (ValueError, TypeError):
                pass
        return queryset

    def get_timeseries_points(filter_type, filter_val):
        import calendar
        from datetime import datetime
        points = []
        if filter_type == 'dia':
            try:
                days = int(filter_val)
            except (ValueError, TypeError):
                days = 7
            if days < 7:
                days = 7
            day_names = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB']
            for i in range(days - 1, -1, -1):
                d = now_local - timedelta(days=i)
                start = timezone.make_aware(datetime.combine(d.date(), datetime.min.time()))
                end = timezone.make_aware(datetime.combine(d.date(), datetime.max.time()))
                label = f"{d.strftime('%d')} {day_names[d.weekday()] if d.weekday() < 7 else ''}"
                points.append({'label': label, 'start': start, 'end': end})
        elif filter_type == 'mes':
            try:
                parts = filter_val.split('-')
                year = int(parts[0])
                month = int(parts[1])
            except (ValueError, TypeError, IndexError):
                year = now_local.year
                month = now_local.month
            _, last_day = calendar.monthrange(year, month)
            for day in range(1, last_day + 1):
                start = timezone.make_aware(datetime(year, month, day, 0, 0, 0))
                end = timezone.make_aware(datetime(year, month, day, 23, 59, 59))
                label = f"{day:02d}"
                points.append({'label': label, 'start': start, 'end': end})
        elif filter_type == 'anio':
            try:
                year = int(filter_val)
            except (ValueError, TypeError):
                year = now_local.year
            months_names = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
            start_month = reg_local.month if year == reg_local.year else 1
            end_month = now_local.month if year == now_local.year else 12
            for m in range(start_month, end_month + 1):
                _, last_day = calendar.monthrange(year, m)
                start = timezone.make_aware(datetime(year, m, 1, 0, 0, 0))
                end = timezone.make_aware(datetime(year, m, last_day, 23, 59, 59))
                label = months_names[m - 1]
                points.append({'label': label, 'start': start, 'end': end})
        else: # desde_creacion
            months_names = ['ENE', 'FEB', 'MAR', 'ABR', 'MAY', 'JUN', 'JUL', 'AGO', 'SEP', 'OCT', 'NOV', 'DIC']
            curr_year = reg_local.year
            curr_month = reg_local.month
            while (curr_year < now_local.year) or (curr_year == now_local.year and curr_month <= now_local.month):
                _, last_day = calendar.monthrange(curr_year, curr_month)
                start = timezone.make_aware(datetime(curr_year, curr_month, 1, 0, 0, 0))
                end = timezone.make_aware(datetime(curr_year, curr_month, last_day, 23, 59, 59))
                label = f"{months_names[curr_month - 1]} '{str(curr_year)[2:]}"
                points.append({'label': label, 'start': start, 'end': end})
                curr_month += 1
                if curr_month > 12:
                    curr_month = 1
                    curr_year += 1
        return points

    f_esfuerzo_type, f_esfuerzo_val = resolve_filter_params(request.GET.get('f_esfuerzo_type', 'desde_creacion'), request.GET.get('f_esfuerzo_val', ''))
    f_temperatura_type, f_temperatura_val = resolve_filter_params(request.GET.get('f_temperatura_type', 'desde_creacion'), request.GET.get('f_temperatura_val', ''))
    f_eficiencia_type, f_eficiencia_val = resolve_filter_params(request.GET.get('f_eficiencia_type', 'desde_creacion'), request.GET.get('f_eficiencia_val', ''))
    f_proyectos_type, f_proyectos_val = resolve_filter_params(request.GET.get('f_proyectos_type', 'desde_creacion'), request.GET.get('f_proyectos_val', ''))
    f_cumplimiento_type, f_cumplimiento_val = resolve_filter_params(request.GET.get('f_cumplimiento_type', 'desde_creacion'), request.GET.get('f_cumplimiento_val', ''))
    f_desglose_type, f_desglose_val = resolve_filter_params(request.GET.get('f_desglose_type', 'desde_creacion'), request.GET.get('f_desglose_val', ''))
    f_acumulado_type, f_acumulado_val = resolve_filter_params(request.GET.get('f_acumulado_type', 'desde_creacion'), request.GET.get('f_acumulado_val', ''))
    f_promedio_type, f_promedio_val = resolve_filter_params(request.GET.get('f_promedio_type', 'desde_creacion'), request.GET.get('f_promedio_val', ''))

    stats_inters = Interaccion.objects.filter(contacto=contacto)

    # 1. Effort Distribution (Canales x Propósito)
    dist_effort = {
        'Información y Calificación': {'Llamada': 0, 'Reunión': 0, 'Correo': 0},
        'Negociación de Precio y Separación.': {'Llamada': 0, 'Reunión': 0, 'Correo': 0},
        'Trámites Legales y Contractuals': {'Llamada': 0, 'Reunión': 0, 'Correo': 0},
        'Construcción y Seguimiento': {'Llamada': 0, 'Reunión': 0, 'Correo': 0},
        'Escrituración y Entrega.': {'Llamada': 0, 'Reunión': 0, 'Correo': 0}
    }

    inters_esfuerzo = apply_stats_filter(stats_inters, f_esfuerzo_type, f_esfuerzo_val)

    for inter in inters_esfuerzo:
        dur = (inter.duracion_minutos or 0) / 60.0 # in hours
        if dur == 0:
            continue
        
        channel = 'Llamada'
        if inter.canal_comunicacion:
            channel = inter.canal_comunicacion.nombre_tipo
        elif inter.tipo_interaccion:
            channel = inter.tipo_interaccion.nombre_tipo
            
        if channel not in ['Llamada', 'Reunión', 'Correo']:
            if inter.tipo_interaccion.nombre_tipo == 'Correo':
                channel = 'Correo'
            elif inter.tipo_interaccion.nombre_tipo == 'Reunión':
                channel = 'Reunión'
            else:
                channel = 'Llamada'

        # Determinar fase / propósito
        purpose = 'Información y Calificación'
        obj_check = inter.parent if inter.parent else inter
        det = (obj_check.detalle_actividad or '').strip()
        
        if det.startswith('[Información y Calificación]') or det.startswith('[Fase 1:'):
            purpose = 'Información y Calificación'
        elif det.startswith('[Negociación de Precio y Separación.]') or det.startswith('[Fase 2:'):
            purpose = 'Negociación de Precio y Separación.'
        elif det.startswith('[Trámites Legales y Contractuals]') or det.startswith('[Fase 3:'):
            purpose = 'Trámites Legales y Contractuals'
        elif det.startswith('[Construcción y Seguimiento]') or det.startswith('[Fase 4:'):
            purpose = 'Construcción y Seguimiento'
        elif det.startswith('[Escrituración y Entrega.]') or det.startswith('[Fase 5:'):
            purpose = 'Escrituración y Entrega.'
        else:
            # Fallback a búsqueda de palabras clave
            text_to_search = f"{(inter.asunto or '')} {(inter.detalle_actividad or '')}".lower()
            kw_f5 = ['escrituracion', 'escrituración', 'entrega', 'entregar', 'cierre', 'final', 'llaves']
            kw_f4 = ['construccion', 'construcción', 'seguimiento', 'obra', 'avance', 'fidelizacion', 'fidelización', 'visita']
            kw_f3 = ['legal', 'tramite', 'trámite', 'papeles', 'contrato', 'firma', 'promesa', 'documento', 'licencia', 'licencias', 'formalizacion', 'formalización']
            kw_f2 = ['precio', 'negociacion', 'negociación', 'cotizacion', 'cotización', 'valor', 'descuento', 'oferta', 'negociar', 'separacion', 'separación', 'separar', 'acuerdo']
            
            if any(kw in text_to_search for kw in kw_f5):
                purpose = 'Escrituración y Entrega.'
            elif any(kw in text_to_search for kw in kw_f4):
                purpose = 'Construcción y Seguimiento'
            elif any(kw in text_to_search for kw in kw_f3):
                purpose = 'Trámites Legales y Contractuals'
            elif any(kw in text_to_search for kw in kw_f2):
                purpose = 'Negociación de Precio y Separación.'
            
        dist_effort[purpose][channel] += round(dur, 2)

    # 2. Nivel de Interacción (Nivel de Interacción con el Cliente)
    interaction_labels = []
    interaction_counts = []
    
    inters_temp = apply_stats_filter(stats_inters, f_temperatura_type, f_temperatura_val)
    temp_points = get_timeseries_points(f_temperatura_type, f_temperatura_val)
    for p in temp_points:
        interaction_labels.append(p['label'])
        q_event = (
            (Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión']) | Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'])) &
            (Q(fecha_reunion__range=(p['start'].date(), p['end'].date())) | Q(fecha_reunion__isnull=True, fecha_interaccion__range=(p['start'], p['end'])))
        )
        q_other = (
            ~Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión']) & 
            (Q(canal_comunicacion__isnull=True) | ~Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión'])) &
            Q(fecha_interaccion__range=(p['start'], p['end']))
        )
        cnt = inters_temp.filter(q_event | q_other).count()
        interaction_counts.append(cnt)

    total_interacciones_count = inters_temp.count()

    # 3. Volumen de Interacciones por Canal (Llamadas, Reuniones, Correos)
    inters_eficiencia = apply_stats_filter(stats_inters, f_eficiencia_type, f_eficiencia_val)
        
    calls_count = inters_eficiencia.filter(Q(canal_comunicacion__nombre_tipo='Llamada') | Q(tipo_interaccion__nombre_tipo='Llamada')).count()
    meetings_count = inters_eficiencia.filter(Q(canal_comunicacion__nombre_tipo='Reunión') | Q(tipo_interaccion__nombre_tipo='Reunión')).count()
    emails_count = inters_eficiencia.filter(Q(canal_comunicacion__nombre_tipo='Correo') | Q(tipo_interaccion__nombre_tipo='Correo')).count()
    
    max_val = max(calls_count, meetings_count, emails_count)
    if max_val == 0:
        canal_preferido = "Ninguno"
    elif max_val == calls_count:
        canal_preferido = "Llamada"
    elif max_val == meetings_count:
        canal_preferido = "Reunión"
    else:
        canal_preferido = "Correo"

    # 4. Proyectos por Mes (Grouped Bar Chart por Mes)
    proj_points = get_timeseries_points(f_proyectos_type, f_proyectos_val)
    project_months_labels = [p['label'] for p in proj_points]

    project_datasets = {
        'Construcción desde cero en terreno propio': [0] * len(proj_points),
        'Diseño y construcción de casas personalizadas': [0] * len(proj_points),
        'Trámites legales y licencias': [0] * len(proj_points),
        'Adecuaciones o remodelaciones': [0] * len(proj_points),
        'Apartamento': [0] * len(proj_points),
        'Otros Proyectos': [0] * len(proj_points)
    }
    
    actividades_proyectos = stats_inters.filter(tipo_interaccion__nombre_tipo='Actividad')
    if proj_points:
        actividades_proyectos = actividades_proyectos.filter(fecha_interaccion__range=(proj_points[0]['start'], proj_points[-1]['end']))
        
    for act in actividades_proyectos:
        act_date = act.fecha_interaccion
        for idx, p in enumerate(proj_points):
            if p['start'] <= act_date <= p['end']:
                proj_name = (act.asunto or '').strip()
                if not proj_name:
                    continue
                if proj_name in project_datasets:
                    project_datasets[proj_name][idx] += 1
                else:
                    project_datasets['Otros Proyectos'][idx] += 1

    # 5. Key Metrics
    inters_kpis = stats_inters
        
    total_time_min = inters_kpis.aggregate(total=Sum('duracion_minutos'))['total'] or 0
    t_hours = total_time_min // 60
    t_mins = total_time_min % 60
    total_tiempo_str = f"{t_hours}h {t_mins}min" if t_hours > 0 else f"{t_mins}min"

    llamadas_cnt = inters_kpis.filter(Q(canal_comunicacion__nombre_tipo='Llamada') | Q(tipo_interaccion__nombre_tipo='Llamada')).count()
    reuniones_cnt = inters_kpis.filter(Q(canal_comunicacion__nombre_tipo='Reunión') | Q(tipo_interaccion__nombre_tipo='Reunión')).count()
    correos_cnt = inters_kpis.filter(Q(canal_comunicacion__nombre_tipo='Correo') | Q(tipo_interaccion__nombre_tipo='Correo')).count()

    # 6. Activities Statistics
    actividades_qs = Interaccion.objects.filter(contacto=contacto, tipo_interaccion__nombre_tipo='Actividad')
    sueltas_qs = Interaccion.objects.filter(contacto=contacto, parent__isnull=True).exclude(tipo_interaccion__nombre_tipo='Actividad')
    
    actividades_qs = apply_stats_filter(actividades_qs, f_cumplimiento_type, f_cumplimiento_val)
    sueltas_qs = apply_stats_filter(sueltas_qs, f_cumplimiento_type, f_cumplimiento_val)
        
    act_finalizadas = actividades_qs.filter(estado='Finalizada').count()
    act_en_curso = actividades_qs.filter(Q(estado='Abierta') | Q(estado='En curso')).count()
    act_canceladas = actividades_qs.filter(estado='Cancelada').count()
    act_sueltas = sueltas_qs.count()
    act_total = act_finalizadas + act_en_curso + act_canceladas + act_sueltas

    # 7. Desglose por Canal (Pie Charts)
    inters_desglose = apply_stats_filter(stats_inters, f_desglose_type, f_desglose_val)
        
    correos_qs = inters_desglose.filter(Q(canal_comunicacion__nombre_tipo='Correo') | Q(tipo_interaccion__nombre_tipo='Correo'))
    correos_enviados = correos_qs.filter(tipo_comunicacion='Saliente').count()
    correos_respondidos = correos_qs.filter(tipo_comunicacion='Entrante').count()
    total_correos_qs = correos_qs.count()
    if total_correos_qs > 0 and (correos_enviados + correos_respondidos) == 0:
        correos_enviados = total_correos_qs

    llamadas_qs = inters_desglose.filter(Q(canal_comunicacion__nombre_tipo='Llamada') | Q(tipo_interaccion__nombre_tipo='Llamada'))
    llamadas_programadas = llamadas_qs.filter(estado__in=['Programada', 'En curso']).count()
    llamadas_canceladas = llamadas_qs.filter(estado='Cancelada').count()
    llamadas_exitosas = llamadas_qs.filter(estado='Finalizada', es_exitosa=True).count()
    llamadas_sin_exito = llamadas_qs.filter(estado='Finalizada', es_exitosa=False).count()

    reuniones_qs = inters_desglose.filter(Q(canal_comunicacion__nombre_tipo='Reunión') | Q(tipo_interaccion__nombre_tipo='Reunión'))
    reuniones_finalizadas = reuniones_qs.filter(estado='Finalizada').count()
    reuniones_canceladas = reuniones_qs.filter(estado='Cancelada').count()
    reuniones_programadas = reuniones_qs.filter(estado__in=['Programada', 'En curso']).count()

    # 8. Cumulative Hours (Tiempo Acumulado)
    cumulative_labels = []
    cumulative_data = []
    
    acum_points = get_timeseries_points(f_acumulado_type, f_acumulado_val)
    cumulative_labels = [p['label'] for p in acum_points]
    for p in acum_points:
        q_event = (
            (Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión']) | Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'])) &
            (Q(fecha_reunion__lte=p['end'].date()) | Q(fecha_reunion__isnull=True, fecha_interaccion__lte=p['end']))
        )
        q_other = (
            ~Q(tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión']) & 
            (Q(canal_comunicacion__isnull=True) | ~Q(canal_comunicacion__nombre_tipo__in=['Llamada', 'Reunión'])) &
            Q(fecha_interaccion__lte=p['end'])
        )
        mins = Interaccion.objects.filter(
            contacto=contacto
        ).filter(q_event | q_other).aggregate(total=Sum('duracion_minutos'))['total'] or 0
        cumulative_data.append(round(mins / 60.0, 1))
            
    total_horas_acumulado = cumulative_data[-1] if cumulative_data else 0.0

    # 9. Average Interaction Duration
    inters_promedio = apply_stats_filter(stats_inters, f_promedio_type, f_promedio_val)
        
    calls_promedio = inters_promedio.filter(Q(canal_comunicacion__nombre_tipo='Llamada') | Q(tipo_interaccion__nombre_tipo='Llamada')).filter(duracion_minutos__gt=0)
    meetings_promedio = inters_promedio.filter(Q(canal_comunicacion__nombre_tipo='Reunión') | Q(tipo_interaccion__nombre_tipo='Reunión')).filter(duracion_minutos__gt=0)
    
    call_durations = [c.duracion_minutos or 0 for c in calls_promedio]
    avg_call_raw = sum(call_durations) / len(call_durations) if call_durations else 0.0
    avg_call_min = round(avg_call_raw, 1)
    
    meeting_durations = [m.duracion_minutos or 0 for m in meetings_promedio]
    avg_meeting_raw = sum(meeting_durations) / len(meeting_durations) if meeting_durations else 0.0
    avg_meeting_min = round(avg_meeting_raw, 1)
    avg_meeting_hrs = round(avg_meeting_min / 60.0, 2)
    
    active_categories = []
    if call_durations:
        active_categories.append(avg_call_raw)
    if meeting_durations:
        active_categories.append(avg_meeting_raw)
        
    overall_avg_min = round(sum(active_categories) / len(active_categories), 1) if active_categories else 0.0

    # Write debug file
    try:
        debug_path = r"c:\Users\Jary\OneDrive\Documentos\Pruebas\scratch\db_debug.txt"
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write(f"f_promedio_type={f_promedio_type}, f_promedio_val={f_promedio_val}\n")
            f.write(f"avg_call_min={avg_call_min}, avg_meeting_min={avg_meeting_min}\n")
            f.write(f"overall_avg_min={overall_avg_min}\n")
            f.write("Calls:\n")
            for c in calls_promedio:
                f.write(f"  id={c.id}, dur={c.duracion_minutos}, fecha_reunion={c.fecha_reunion}, fecha_interaccion={c.fecha_interaccion}\n")
            f.write("Meetings:\n")
            for m in meetings_promedio:
                f.write(f"  id={m.id}, dur={m.duracion_minutos}, fecha_reunion={m.fecha_reunion}, fecha_interaccion={m.fecha_interaccion}\n")
    except Exception as e:
        pass

    stats_data = {
        'dist_effort': dist_effort,
        'interaction_labels': interaction_labels,
        'interaction_counts': interaction_counts,
        'total_interacciones_count': total_interacciones_count,
        'calls_count': calls_count,
        'meetings_count': meetings_count,
        'emails_count': emails_count,
        'canal_preferido': canal_preferido,
        'project_months_labels': project_months_labels,
        'project_datasets': project_datasets,
        'total_tiempo_str': total_tiempo_str,
        'llamadas_cnt': llamadas_cnt,
        'reuniones_cnt': reuniones_cnt,
        'correos_cnt': correos_cnt,
        'act_total': act_total,
        'act_finalizadas': act_finalizadas,
        'act_en_curso': act_en_curso,
        'act_canceladas': act_canceladas,
        'act_sueltas': act_sueltas,
        'f_esfuerzo_type': f_esfuerzo_type,
        'f_esfuerzo_val': f_esfuerzo_val,
        'f_temperatura_type': f_temperatura_type,
        'f_temperatura_val': f_temperatura_val,
        'f_eficiencia_type': f_eficiencia_type,
        'f_eficiencia_val': f_eficiencia_val,
        'f_proyectos_type': f_proyectos_type,
        'f_proyectos_val': f_proyectos_val,
        'f_cumplimiento_type': f_cumplimiento_type,
        'f_cumplimiento_val': f_cumplimiento_val,
        'f_desglose_type': f_desglose_type,
        'f_desglose_val': f_desglose_val,
        'correos_enviados': correos_enviados,
        'correos_respondidos': correos_respondidos,
        'llamadas_programadas': llamadas_programadas,
        'llamadas_canceladas': llamadas_canceladas,
        'llamadas_exitosas': llamadas_exitosas,
        'llamadas_sin_exito': llamadas_sin_exito,
        'reuniones_finalizadas': reuniones_finalizadas,
        'reuniones_canceladas': reuniones_canceladas,
        'reuniones_programadas': reuniones_programadas,
        'cumulative_labels': cumulative_labels,
        'cumulative_data': cumulative_data,
        'total_horas_acumulado': total_horas_acumulado,
        'avg_call_min': avg_call_min,
        'avg_meeting_min': avg_meeting_min,
        'avg_meeting_hrs': avg_meeting_hrs,
        'overall_avg_min': overall_avg_min,
        'f_acumulado_type': f_acumulado_type,
        'f_acumulado_val': f_acumulado_val,
        'f_promedio_type': f_promedio_type,
        'f_promedio_val': f_promedio_val,
    }

    if request.GET.get('ajax_stats') == '1':
        return JsonResponse(stats_data)

    stats_json = json.dumps(stats_data)
    
    from_page = request.GET.get('from', 'interacciones')
    
    return render(request, "detalle_contacto.html", {
        "c": contacto,
        "interacciones": interacciones,
        "interacciones_asc": interacciones_asc,
        "interacciones_roots": interacciones_roots,
        "tipos": tipos_interaccion,
        "usuario_logueado": usuario_logueado,
        "stats_json": stats_json,
        "available_years": available_years,
        "available_months": available_months,
        "from_page": from_page,
    })

@csrf_exempt
def ajax_sincronizar_correos(request, id_contacto):
    """AJAX endpoint: sincroniza correos y devuelve la lista actualizada como HTML."""
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)

    usuario_logueado = Usuario.objects.get(id=id_sesion)
    contacto = get_object_or_404(Contacto, id=id_contacto)

    # Deduplicar correos existentes
    deduplicar_correos(contacto)

    # Sincronizar correos vía IMAP
    nuevos = sincronizar_correos_imap(request, contacto, usuario_logueado)

    # Obtener todos los correos actualizados
    tipo_correo = TipoInteraccion.objects.filter(nombre_tipo='Correo').first()
    correos = Interaccion.objects.filter(
        contacto=contacto,
        tipo_interaccion=tipo_correo
    ).order_by('-fecha_interaccion', '-id') if tipo_correo else []

    # Construir HTML de la lista de correos
    html_correos = ''
    for inter in correos:
        destacado_class = 'active' if inter.destacado else ''

        if inter.tipo_comunicacion == 'Entrante':
            nombre_display = f"{contacto.nombre} {contacto.apellido}" if contacto.nombre else (contacto.razon_social or '')
            avatar_initial = (contacto.nombre or contacto.razon_social or 'C')[0].upper()
            avatar_style = 'background: #eef2ff; color: #4338ca;'
            sender_name = nombre_display
            to_line = f'a mí ({usuario_logueado.nombre_usuario}) ▼'
            status_badge_html = '''
                <div class="email-status-badge" style="color: #6366f1;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                    </svg>
                    Recibidos
                </div>'''
        else:
            avatar_initial = (inter.usuario_responsable.nombre_usuario or 'U')[0].upper()
            avatar_style = ''
            sender_name = f'Tú ({inter.usuario_responsable.nombre_usuario})'
            nombre_display = f"{contacto.nombre} {contacto.apellido}" if contacto.nombre else (contacto.razon_social or '')
            to_line = f'para: {nombre_display} ▼'
            status_badge_html = '''
                <div class="email-status-badge">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    Enviado
                </div>'''

        fecha_fmt = timezone.localtime(inter.fecha_interaccion).strftime('%d %b a las %I:%M %p') if inter.fecha_interaccion else ''
        detalle_trunc = (inter.detalle_actividad or '')[:40]
        detalle_full = inter.detalle_actividad or ''

        reply_forward_html = ''
        if inter.tipo_comunicacion == 'Entrante':
            asunto_val = inter.asunto if inter.asunto else ''
            asunto_js = asunto_val.replace("'", "\\'").replace('"', '\\"')
            detalle_js = detalle_full.replace("'", "\\'").replace('"', '\\"').replace("\n", "\\n").replace("\r", "")
            reply_forward_html = f"""
                <div class="email-reply-forward-actions" style="margin-top: 15px; display: flex; gap: 12px;">
                    <button type="button" class="btn-email-action reply" onclick="responderEmail({inter.id}, '{asunto_js}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px; vertical-align: middle;"><polyline points="9 17 4 12 9 7"></polyline><path d="M20 18v-2a4 4 0 0 0-4-4H4"></path></svg>
                        Responder
                    </button>
                    <button type="button" class="btn-email-action forward" onclick="reenviarEmail({inter.id}, '{asunto_js}', '{detalle_js}')">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 6px; vertical-align: middle;"><polyline points="15 17 20 12 15 7"></polyline><path d="M4 18v-2a4 4 0 0 1 4-4h12"></path></svg>
                        Reenviar
                    </button>
                </div>"""

        html_correos += f'''
        <div class="email-card">
            <div class="email-card-header" onclick="toggleEmail({inter.id})">
                <div class="email-subject-row">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
                        fill="none" stroke="#10b981" stroke-width="3" id="arrow-{inter.id}">
                        <polyline points="6 9 12 15 18 9"></polyline>
                    </svg>
                    Correo - {detalle_trunc}
                </div>
                <div style="display: flex; align-items: center; gap: 15px;">
                    <button class="btn-star {destacado_class}"
                        onclick="toggleDestacar(event, {inter.id})">
                        <svg class="star-icon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                        </svg>
                        
                    </button>
                    <div class="email-date-row">
                        {fecha_fmt}
                    </div>
                </div>
            </div>
            <div class="email-card-body" id="mail-body-{inter.id}">
                <div class="email-sender-info">
                    <div class="email-avatar-v2" style="{avatar_style}">{avatar_initial}</div>
                    <div class="email-names">
                        <div class="email-sender-name">{sender_name}</div>
                        <div class="email-to-list">{to_line}</div>
                        {status_badge_html}
                    </div>
                    <div class="email-actions-inline">
                        <button onclick="cerrarEmail({inter.id})">✖</button>
                    </div>
                </div>
                <div class="email-text-content">{detalle_full}</div>
                {reply_forward_html}
            </div>
        </div>'''

    return JsonResponse({
        'status': 'success',
        'nuevos': nuevos if nuevos >= 0 else 0,
        'total': len(correos) if correos else 0,
        'html': html_correos,
        'error': nuevos < 0
    })

@csrf_exempt
def destacar_interaccion(request, id_contacto, id_interaccion):
    if request.method == "POST":
        inter = get_object_or_404(Interaccion, id=id_interaccion, contacto_id=id_contacto)
        inter.destacado = not inter.destacado
        inter.save()
        return JsonResponse({'status': 'ok', 'destacado': inter.destacado})
    return JsonResponse({'status': 'error'}, status=400)

def interacciones(request):
    id_sesion = request.session.get('user_id')
    if not id_sesion: return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    error = ""
    
    if not TipoInteraccion.objects.exists():
        for t in ["Nota", "Tarea", "Reunión", "Llamada", "Correo"]:
            TipoInteraccion.objects.create(nombre_tipo=t)

    if request.method == "POST":
        contacto_id = request.POST.get("contacto")
        tipo_id = request.POST.get("tipo_interaccion")
        canal_id = request.POST.get("canal_comunicacion")
        duracion_val = request.POST.get("duracion_minutos")
        temp_val = request.POST.get("temperatura_emocional")
        es_exitosa = request.POST.get("es_exitosa") == "on" or "es_exitosa" in request.POST
        detalle = request.POST.get("detalle", "")

        if not contacto_id or not tipo_id or not detalle:
            error = "Por favor, complete todos los campos obligatorios."
        else:
            try:
                contacto = get_object_or_404(Contacto, id=contacto_id)
                tipo_obj = get_object_or_404(TipoInteraccion, id=tipo_id)
                
                canal_obj = None
                if canal_id:
                    try:
                        canal_obj = TipoInteraccion.objects.get(id=canal_id)
                    except TipoInteraccion.DoesNotExist:
                        pass
                
                duracion_minutos = None
                if duracion_val:
                    try:
                        duracion_minutos = int(duracion_val)
                    except ValueError:
                        pass
                
                temperatura_emocional = None
                if temp_val:
                    try:
                        temperatura_emocional = int(temp_val)
                    except ValueError:
                        pass
                
                estado_inter = 'Programada' if tipo_obj.nombre_tipo == 'Reunión' else 'Finalizada'
                
                Interaccion.objects.create(
                    contacto=contacto,
                    usuario_responsable=usuario_logueado,
                    tipo_interaccion=tipo_obj,
                    detalle_actividad=detalle,
                    es_exitosa=es_exitosa,
                    estado=estado_inter,
                    canal_comunicacion=canal_obj,
                    duracion_minutos=duracion_minutos,
                    temperatura_emocional=temperatura_emocional
                )
                messages.success(request, f"Interacción registrada correctamente.")
                return redirect(f'/contacto/{contacto_id}/')
            except Exception as e:
                error = f"Error al guardar la interacción: {str(e)}"

    return render(request, "interacciones.html", {
        "interacciones": Interaccion.objects.all().order_by('-fecha_interaccion'),
        "contactos": Contacto.objects.filter(activo=True),
        "tipos": TipoInteraccion.objects.all(),
        "error": error,
        "usuario_logueado": usuario_logueado
    })

def eliminar_interaccion(request, id_inter):
    if not request.session.get('user_id'): return redirect('/login/')
    get_object_or_404(Interaccion, id=id_inter).delete()
    return redirect('/interacciones/')

def usuarios_view(request):
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect('login')
    
    usuario_logueado = Usuario.objects.get(id=user_id)
    if usuario_logueado.rol.nombre_rol != "Administrador":
        return redirect('dashboard')
        
    usuarios = Usuario.objects.select_related('rol').all()
    roles = Rol.objects.all()
    
    if request.method == "POST":
        accion = request.POST.get("accion")
        if accion == "eliminar":
            uid = request.POST.get("usuario_id")
            Usuario.objects.filter(id=uid).delete()
        elif accion == "modificar":
            uid = request.POST.get("usuario_id")
            u = Usuario.objects.get(id=uid)
            u.nombre_usuario = request.POST.get("nombre")
            u.email = request.POST.get("email")
            u.rol_id = request.POST.get("rol_id")
            u.save()
        elif accion == "cambiar_estado":
            uid = request.POST.get("usuario_id")
            u = Usuario.objects.get(id=uid)
            u.activo = not u.activo
            u.save()
            
    return render(request, "usuarios.html", {
        "usuario_logueado": usuario_logueado,
        "usuarios": usuarios,
        "roles": roles
    })

def calendario_view(request):
    usuario_id = request.session.get('usuario_id') or request.session.get('user_id')
    if not usuario_id:
        return redirect('login')
    
    usuario_logueado = Usuario.objects.get(id=usuario_id)
    # Obtener todas las interacciones (o solo reuniones) para el calendario
    interacciones = Interaccion.objects.select_related('contacto', 'tipo_interaccion').all().order_by('-fecha_interaccion')
    
    return render(request, "calendario.html", {
        "usuario_logueado": usuario_logueado,
        "interacciones": interacciones,
        "hoy": timezone.now()
    })

@csrf_exempt
def configurar_firma(request):
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
    
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    firma, _ = FirmaDigital.objects.get_or_create(usuario=usuario_logueado)

    if request.method == "POST":
        firma.html_content = request.POST.get("html_content", "")
        if "pdf_attachment" in request.FILES:
            firma.pdf_attachment = request.FILES["pdf_attachment"]
        firma.save()
        return JsonResponse({'status': 'success', 'message': 'Firma actualizada correctamente'})
    
    # Si es GET, retornar los datos actuales para popular el editor
    pdf_url = firma.pdf_attachment.url if firma.pdf_attachment else None
    return JsonResponse({
        'status': 'success', 
        'html_content': firma.html_content,
        'pdf_url': pdf_url
    })

@csrf_exempt
def subir_adjunto(request):
    """AJAX endpoint to upload a file attachment for emails."""
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)

    if request.method == "POST" and request.FILES.get("file"):
        from django.core.files.storage import default_storage
        file = request.FILES["file"]
        
        # Save file to adjuntos_correo under BASE_DIR
        name = default_storage.save(f'adjuntos_correo/{file.name}', file)
        url = f'/media/{name}'
        path = default_storage.path(name)
        
        return JsonResponse({
            'status': 'success',
            'url': url,
            'name': file.name,
            'path': path
        })
    return JsonResponse({'status': 'error', 'message': 'Método no permitido o archivo no enviado'}, status=400)


from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
import json
import uuid
import urllib.request
import urllib.error

def _log_whatsapp_debug(message):
    try:
        import os
        from django.utils import timezone
        log_path = r"c:\Users\Jary\OneDrive\Documentos\Pruebas\scratch\whatsapp_debug.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"[{timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except Exception as e:
        print(f"[Debug Log Error] {e}")

def format_whatsapp_number(phone):
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    if len(digits) == 10 and digits.startswith('3'):
        return f"57{digits}"
    return digits

def find_contact_by_phone(wa_phone):
    digits_only = "".join(c for c in wa_phone if c.isdigit())
    if not digits_only:
        return None
    contacts = Contacto.objects.filter(activo=True)
    for c in contacts:
        c_phone = "".join(char for char in (c.celular or c.telefono or '') if char.isdigit())
        if c_phone and (digits_only.endswith(c_phone) or c_phone.endswith(digits_only)):
            return c
    return None

@csrf_exempt
def whatsapp_webhook(request):
    if request.method == "GET":
        mode = request.GET.get('hub.mode')
        challenge = request.GET.get('hub.challenge')
        token = request.GET.get('hub.verify_token')
        
        verify_token = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', 'VERIFY_TOKEN_PLACEHOLDER')
        _log_whatsapp_debug(f"Webhook GET verification request: mode={mode}, token={token}, expected={verify_token}")
        if mode == 'subscribe' and token == verify_token:
            _log_whatsapp_debug("Webhook verification SUCCESS")
            return HttpResponse(challenge)
        _log_whatsapp_debug("Webhook verification FAILED")
        return HttpResponse('Verification failed', status=403)
        
    elif request.method == "POST":
        try:
            data = json.loads(request.body.decode('utf-8'))
            _log_whatsapp_debug(f"Webhook POST received: {json.dumps(data)}")
            entries = data.get('entry', [])
            for entry in entries:
                changes = entry.get('changes', [])
                for change in changes:
                    value = change.get('value', {})
                    messages = value.get('messages', [])
                    for msg in messages:
                        from_phone = msg.get('from')
                        msg_id = msg.get('id')
                        msg_type = msg.get('type')
                        
                        text_body = ""
                        if msg_type == 'text':
                            text_body = msg.get('text', {}).get('body', '')
                        elif msg_type == 'interactive':
                            text_body = msg.get('interactive', {}).get('button_reply', {}).get('title', '')
                        else:
                            text_body = f"[{msg_type.upper()} message]"
                        
                        _log_whatsapp_debug(f"Parsing message: from={from_phone}, text={text_body}")
                        if from_phone and text_body:
                            contacto = find_contact_by_phone(from_phone)
                            if contacto:
                                _log_whatsapp_debug(f"Found matching contact: {contacto.nombre} {contacto.apellido} (ID={contacto.id})")
                                MensajeWhatsApp.objects.create(
                                    contacto=contacto,
                                    texto=text_body,
                                    direccion='Entrante',
                                    whatsapp_id=msg_id,
                                    estado='leido'
                                )
                            else:
                                _log_whatsapp_debug(f"No contact found matching phone: {from_phone}")
        except Exception as e:
            _log_whatsapp_debug(f"Webhook POST Error: {str(e)}")
            print(f"[Webhook Parse Error] {e}")
            
        return HttpResponse('EVENT_RECEIVED', status=200)

@csrf_exempt
def enviar_mensaje_whatsapp(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    contacto = get_object_or_404(Contacto, id=id_contacto)
    
    if request.method == "POST":
        texto = request.POST.get('texto', '').strip()
        if not texto:
            return JsonResponse({'status': 'error', 'message': 'El mensaje no puede estar vacío'}, status=400)
            
        phone_to_use = contacto.celular or contacto.telefono
        _log_whatsapp_debug(f"Sending message to contact ID={id_contacto} ({contacto.nombre} {contacto.apellido}): raw_phone='{phone_to_use}', text='{texto}'")
        if not phone_to_use:
            _log_whatsapp_debug(f"Error: contact ID={id_contacto} has no phone number")
            return JsonResponse({'status': 'error', 'message': 'El contacto no tiene un número de celular/teléfono registrado'}, status=400)
            
        formatted_phone = format_whatsapp_number(phone_to_use)
        _log_whatsapp_debug(f"Formatted phone: '{formatted_phone}'")
        
        success = False
        whatsapp_id = None
        
        token = getattr(settings, 'WHATSAPP_ACCESS_TOKEN', '')
        phone_id = getattr(settings, 'WHATSAPP_PHONE_NUMBER_ID', '')
        
        _log_whatsapp_debug(f"Credentials status: token_exists={bool(token)}, phone_id='{phone_id}'")
        
        if token and token != 'EAAG_PLACEHOLDER' and phone_id and phone_id != 'PHONE_ID_PLACEHOLDER':
            url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": formatted_phone,
                "type": "text",
                "text": {"preview_url": False, "body": texto}
            }
            _log_whatsapp_debug(f"Meta request payload: {json.dumps(payload)}")
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            try:
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_body = response.read().decode('utf-8')
                    _log_whatsapp_debug(f"Meta API Success Response: status={response.status}, body={res_body}")
                    if response.status in [200, 201]:
                        res_data = json.loads(res_body)
                        whatsapp_id = res_data.get('messages', [{}])[0].get('id')
                        success = True
                    else:
                        print(f"WhatsApp Cloud API Error: {res_body}")
            except urllib.error.HTTPError as e:
                res_body = e.read().decode('utf-8') if e.fp else str(e)
                _log_whatsapp_debug(f"Meta API HTTP Error: code={e.code}, body={res_body}")
                print(f"WhatsApp Cloud API Error: {res_body}")
            except Exception as e:
                _log_whatsapp_debug(f"Meta API request exception: {str(e)}")
                print(f"WhatsApp Request Exception: {e}")
        else:
            _log_whatsapp_debug("Skipping Meta request: credentials not set or placeholder.")
                
        if not success:
            whatsapp_id = f"mock-{uuid.uuid4()}"
            _log_whatsapp_debug(f"Falling back to mock reply: generated mock id='{whatsapp_id}'")
            
        MensajeWhatsApp.objects.create(
            contacto=contacto,
            remitente_usuario=usuario_logueado,
            texto=texto,
            direccion='Saliente',
            whatsapp_id=whatsapp_id,
            estado='enviado'
        )
        
        if not success:
            mock_replies = [
                f"Hola {usuario_logueado.nombre_usuario}, entiendo perfectamente. Vamos a revisarlo en la Constructora DYCO.",
                "Recibido. Me parece una excelente propuesta de proyecto.",
                "Gracias por la información. ¿Cuándo podríamos programar una visita?",
                "Vale, estaré pendiente de tu llamada."
            ]
            import random
            reply_text = random.choice(mock_replies)
            
            MensajeWhatsApp.objects.create(
                contacto=contacto,
                texto=reply_text,
                direccion='Entrante',
                whatsapp_id=f"mock-reply-{uuid.uuid4()}",
                estado='leido'
            )
            
        return JsonResponse({'status': 'success', 'whatsapp_id': whatsapp_id})
        
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

def obtener_mensajes_whatsapp(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    contacto = get_object_or_404(Contacto, id=id_contacto)
    mensajes = MensajeWhatsApp.objects.filter(contacto=contacto).order_by('fecha_envio')
    
    data = []
    for m in mensajes:
        data.append({
            'id': m.id,
            'texto': m.texto,
            'fecha': timezone.localtime(m.fecha_envio).strftime('%I:%M %p'),
            'direccion': m.direccion,
            'remitente': m.remitente_usuario.nombre_usuario if m.remitente_usuario else 'Cliente',
            'estado': m.estado
        })
    return JsonResponse({'status': 'success', 'mensajes': data})

def obtener_notificaciones_contacto(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return JsonResponse({'status': 'error', 'message': 'No autenticado'}, status=401)
        
    contacto = get_object_or_404(Contacto, id=id_contacto)
    
    # Bell items (calls, received emails, meetings)
    from django.db.models import Q
    bell_inters = Interaccion.objects.filter(
        Q(contacto=contacto) & (
            Q(tipo_interaccion__nombre_tipo='Llamada', estado='Programada') |
            Q(tipo_interaccion__nombre_tipo='Correo', tipo_comunicacion='Entrante') |
            Q(tipo_interaccion__nombre_tipo='Reunión', estado='Programada')
        )
    ).order_by('-fecha_interaccion')
    
    bell_list = []
    for inter in bell_inters:
        t = inter.tipo_interaccion.nombre_tipo
        title = ""
        body = ""
        if t == 'Correo':
            is_saliente = inter.tipo_comunicacion == 'Saliente'
            title = "Correo enviado" if is_saliente else "Correo recibido"
            body = f"Asunto: {inter.asunto}" if inter.asunto else (inter.detalle_actividad[:100] if inter.detalle_actividad else "Sin asunto")
        elif t == 'Llamada':
            title = "Llamada programada"
            f_str = inter.fecha_reunion.strftime('%d/%m/%Y') if inter.fecha_reunion else ""
            h_str = inter.hora_reunion.strftime('%I:%M %p') if inter.hora_reunion else ""
            body = f"Programada para el {f_str} a las {h_str}"
        elif t == 'Reunión':
            title = "Reunión programada"
            f_str = inter.fecha_reunion.strftime('%d/%m/%Y') if inter.fecha_reunion else ""
            h_str = inter.hora_reunion.strftime('%I:%M %p') if inter.hora_reunion else ""
            body = f"Programada para el {f_str} a las {h_str}"
            
        bell_list.append({
            'tipo': t,
            'title': title,
            'body': body,
            'fecha': timezone.localtime(inter.fecha_interaccion).strftime('%d/%m/%Y %I:%M %p')
        })
        
    # Clock items
    scheduled = Interaccion.objects.filter(
        contacto=contacto,
        tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'],
        estado='Programada',
        fecha_reunion__isnull=False
    )
    
    clock_list = []
    from datetime import datetime, time
    now = timezone.localtime(timezone.now())
    
    for inter in scheduled:
        f = inter.fecha_reunion
        h = inter.hora_reunion or time(0, 0)
        try:
            event_dt = timezone.make_aware(datetime.combine(f, h), timezone.get_current_timezone())
            diff = event_dt - now
            diff_hours = diff.total_seconds() / 3600.0
            
            if diff_hours <= 24:
                notice = "Atrasado" if diff_hours <= 0 else ("Falta menos de 1 hora" if diff_hours <= 1 else ("Falta menos de 6 horas" if diff_hours <= 6 else "Falta menos de 1 día"))
                f_str = f.strftime('%d/%m/%Y')
                h_str = h.strftime('%I:%M %p')
                t = inter.tipo_interaccion.nombre_tipo
                clock_list.append({
                    'tipo': t,
                    'title': f"⏰ Recordatorio: {t}",
                    'body': f"{t} programada para el {f_str} a las {h_str} ({notice})",
                    'fecha': event_dt.strftime('%d/%m/%Y %I:%M %p')
                })
        except Exception:
            pass
            
    return JsonResponse({
        'status': 'success',
        'bell_list': bell_list,
        'clock_list': clock_list
    })

@csrf_exempt
def actualizar_perfil(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"ok": False, "error": "No autenticado"}, status=401)

    u = Usuario.objects.get(id=user_id)
    campo = request.POST.get("campo", "")
    valor = request.POST.get("valor", "").strip()

    if not valor:
        return JsonResponse({"ok": False, "error": "El valor no puede estar vacío"})

    if campo == "nombre_usuario":
        if Usuario.objects.filter(nombre_usuario=valor).exclude(id=u.id).exists():
            return JsonResponse({"ok": False, "error": "Ese nombre de usuario ya está en uso"})
        u.nombre_usuario = valor
        u.save()
        request.session['user_name'] = valor
        return JsonResponse({"ok": True, "valor": valor})

    elif campo == "email":
        if Usuario.objects.filter(email=valor).exclude(id=u.id).exists():
            return JsonResponse({"ok": False, "error": "Ese correo ya está registrado por otro usuario"})
            
        if valor == u.email:
            return JsonResponse({"ok": True, "valor": valor})
            
        import random
        from datetime import timedelta
        pin = f"{random.randint(0, 999999):06d}"
        
        u.nuevo_email_pendiente = valor
        u.token_cambio_email = pin
        u.token_cambio_email_expiracion = timezone.now() + timedelta(minutes=5)
        u.save()
        
        try:
            enviar_correo_seguro(
                'Código de Verificación - Cambio de Correo',
                f'Hola {u.nombre_usuario},\n\nHas solicitado cambiar tu correo electrónico. Tu código de verificación es: {pin}\n\nEste código expirará en 5 minutos.',
                [valor]
            )
            print(f"\n[SOPORTE] Código de cambio de correo para {u.nombre_usuario} a {valor}: {pin}\n")
            return JsonResponse({"ok": True, "requiere_verificacion": True, "mensaje": "Se ha enviado un código de 6 dígitos a tu nuevo correo."})
        except Exception as e:
            u.nuevo_email_pendiente = None
            u.token_cambio_email = None
            u.token_cambio_email_expiracion = None
            u.save()
            return JsonResponse({"ok": False, "error": f"Error al enviar el correo: {str(e)}"})

    return JsonResponse({"ok": False, "error": "Campo no válido"})

@csrf_exempt
def verificar_cambio_email(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"ok": False, "error": "No autenticado"}, status=401)

    u = Usuario.objects.get(id=user_id)
    pin = request.POST.get("pin", "").strip()

    if not pin:
        return JsonResponse({"ok": False, "error": "Debes ingresar un código"})

    if not u.token_cambio_email or not u.token_cambio_email_expiracion or not u.nuevo_email_pendiente:
        return JsonResponse({"ok": False, "error": "No hay una solicitud de cambio de correo pendiente"})

    if timezone.now() > u.token_cambio_email_expiracion:
        return JsonResponse({"ok": False, "error": "El código ha expirado"})

    if pin != u.token_cambio_email:
        return JsonResponse({"ok": False, "error": "Código incorrecto"})

    nuevo_email = u.nuevo_email_pendiente
    u.email = nuevo_email
    u.nuevo_email_pendiente = None
    u.token_cambio_email = None
    u.token_cambio_email_expiracion = None
    u.save()

    return JsonResponse({"ok": True, "valor": nuevo_email, "mensaje": "Correo actualizado correctamente"})

@csrf_exempt
def reenviar_codigo_email(request):
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Método no permitido"}, status=405)

    user_id = request.session.get("user_id")
    if not user_id:
        return JsonResponse({"ok": False, "error": "No autenticado"}, status=401)

    u = Usuario.objects.get(id=user_id)

    if not u.nuevo_email_pendiente:
        return JsonResponse({"ok": False, "error": "No hay un correo pendiente"})

    import random
    from datetime import timedelta
    pin = f"{random.randint(0, 999999):06d}"
    
    u.token_cambio_email = pin
    u.token_cambio_email_expiracion = timezone.now() + timedelta(minutes=5)
    u.save()
    
    try:
        enviar_correo_seguro(
            'Código de Verificación (Reenvío) - Cambio de Correo',
            f'Hola {u.nombre_usuario},\n\nTu nuevo código de verificación es: {pin}\n\nEste código expirará en 5 minutos.',
            [u.nuevo_email_pendiente]
        )
        print(f"\n[SOPORTE] Nuevo código de cambio de correo para {u.nombre_usuario} a {u.nuevo_email_pendiente}: {pin}\n")
        return JsonResponse({"ok": True, "mensaje": "Código reenviado correctamente"})
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Error al enviar el correo: {str(e)}"})


def usuarios_view(request):
    """Vista de gestión de usuarios — solo para administradores."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/login/')
    u = Usuario.objects.get(id=user_id)
    if u.rol.nombre_rol != 'Administrador':
        return redirect('/')

    todos = Usuario.objects.select_related('rol').order_by('rol__nombre_rol', 'nombre_usuario')

    from django.db.models.functions import TruncYear, TruncMonth, TruncWeek
    from django.utils import timezone as tz
    now = tz.now()

    stats = (
        Interaccion.objects
        .values('usuario_responsable__nombre_usuario')
        .annotate(total=Count('id'))
        .order_by('-total')[:8]
    )

    chart_labels = [s['usuario_responsable__nombre_usuario'] or 'Sin asignar' for s in stats]
    chart_data   = [s['total'] for s in stats]

    return render(request, 'usuarios.html', {
        'usuario_logueado': u,
        'todos_usuarios': todos,
        'admins': todos.filter(rol__nombre_rol='Administrador'),
        'usuarios': todos.filter(rol__nombre_rol='Usuario'),
        'total_usuarios': todos.count(),
        'activos': todos.filter(activo=True).count(),
        'inactivos': todos.filter(activo=False).count(),
        'chart_labels': chart_labels,
        'chart_data': chart_data,
    })


def incidencias_view(request):
    """Vista de gestión de incidencias (placeholder — módulo futuro)."""
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('/login/')
    u = Usuario.objects.get(id=user_id)
    return render(request, 'incidencias.html', {
        'usuario_logueado': u,
    })
