import imaplib
import email
from email.header import decode_header
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.mail import send_mail
from django.urls import reverse
import uuid
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import Contacto, TipoContacto, TipoIdentificacion, Interaccion, TipoInteraccion, Usuario, Rol

def registro_view(request):
    error = ""
    # Asegurar que los roles existan
    Rol.objects.get_or_create(nombre_rol="Administrador")
    Rol.objects.get_or_create(nombre_rol="Usuario")
    
    if request.method == "POST":
        nombre = request.POST.get("usuario")
        email = request.POST.get("email")
        rol_id = request.POST.get("rol_id")
        if not rol_id:
            error = "Debes seleccionar un rol para registrarte."
            roles = Rol.objects.all()
            return render(request, "registro.html", {"roles": roles, "error": error})
        
        passw = request.POST.get("password")
        
        # Validación de duplicados
        usuario_sin_verificar = Usuario.objects.filter(email=email, activo=False).first()
        if usuario_sin_verificar:
            # Reenviar correo si la cuenta existe pero no está verificada
            try:
                token = str(uuid.uuid4())
                usuario_sin_verificar.token_verificacion = token
                usuario_sin_verificar.save()
                
                # link = request.build_absolute_uri(reverse('verificar_correo', args=[token]))
                link = f"{settings.NGROK_URL}{reverse('verificar_correo', args=[token])}"
                
                send_mail(
                    'Verifica tu cuenta en el CRM (reenvío)',
                    f'Hola {usuario_sin_verificar.nombre_usuario},\n\nTe reenviamos el enlace de verificación:\n{link}\n\nSi no creaste esta cuenta, ignora este mensaje.',
                    None,
                    [email],
                    fail_silently=False,
                )
                return render(request, "registro.html", {"success": "Ya te habíamos enviado un correo. Te hemos reenviado el enlace de verificación. Revisa tu bandeja de entrada o spam.", "roles": Rol.objects.all()})
            except Exception as e:
                error = f"Error al reenviar correo: {e}"
        elif Usuario.objects.filter(nombre_usuario=nombre).exists():
            error = "Este nombre de usuario ya está ocupado."
        elif Usuario.objects.filter(email=email, activo=True).exists():
            error = "Este correo electrónico ya está registrado y verificado."
        else:
            try:
                token = str(uuid.uuid4())
                Usuario.objects.create(
                    nombre_usuario=nombre,
                    email=email,
                    rol_id=rol_id,
                    password_hash=passw,
                    activo=False,
                    token_verificacion=token
                )
                
                # link = request.build_absolute_uri(reverse('verificar_correo', args=[token]))
                link = f"{settings.NGROK_URL}{reverse('verificar_correo', args=[token])}"
                
                send_mail(
                    'Verifica tu cuenta en el CRM',
                    f'Hola {nombre},\n\nPor favor, verifica tu correo electrónico haciendo clic en el siguiente enlace:\n{link}\n\nSi no creaste esta cuenta, ignora este mensaje.',
                    None,
                    [email],
                    fail_silently=False,
                )
                return render(request, "registro.html", {"success": "Registro exitoso. Revisa tu bandeja de entrada o spam para verificar tu correo.", "roles": Rol.objects.all()})
            except Exception as e:
                error = f"Error al registrar: {e}"
                
    roles = Rol.objects.all()
    return render(request, "registro.html", {"roles": roles, "error": error})

def verificar_correo(request, token):
    if not token:
        return render(request, "login.html", {"error": "Token de verificación inválido.", "roles": Rol.objects.all()})
        
    u = Usuario.objects.filter(token_verificacion=token).first()
    if u:
        u.activo = True
        u.token_verificacion = ""
        u.save()
        return render(request, "login.html", {"success": "Cuenta verificada con éxito. Ya puedes iniciar sesión.", "roles": Rol.objects.all()})
    return render(request, "login.html", {"error": "El enlace de verificación es inválido o ya expiró.", "roles": Rol.objects.all()})

def login_view(request):
    error = ""
    # Asegurar roles base
    admin_rol, _ = Rol.objects.get_or_create(nombre_rol="Administrador")
    user_rol, _ = Rol.objects.get_or_create(nombre_rol="Usuario")
    
    # Usuario admin de prueba
    if not Usuario.objects.filter(nombre_usuario="admin").exists():
        Usuario.objects.create(nombre_usuario="admin", email="admin@crm.com", password_hash="admin123", rol=admin_rol, activo=True)
    
    if request.method == "POST":
        rol_id = request.POST.get("rol_id")
        if not rol_id:
            error = "Selecciona un rol."
            roles = Rol.objects.all()
            return render(request, "login.html", {"roles": roles, "error": error})
            
        user_input = request.POST.get("usuario", "").strip()
        pass_input = request.POST.get("password", "")
        
        u = Usuario.objects.filter(
            Q(nombre_usuario__iexact=user_input) | Q(email__iexact=user_input),
            rol_id=rol_id,
            password_hash=pass_input,
            activo=True
        ).first()
        if u:
            request.session['user_id'] = u.id
            request.session['user_name'] = u.nombre_usuario
            request.session['rol_name'] = u.rol.nombre_rol
            return redirect('/')
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
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        u = Usuario.objects.filter(email__iexact=email).first()
        if u:
            token = str(uuid.uuid4())
            u.token_password = token
            u.save()
            
            # link = request.build_absolute_uri(reverse('resetear_contrasena', args=[token]))
            link = f"{settings.NGROK_URL}{reverse('resetear_contrasena', args=[token])}"
            
            try:
                send_mail(
                    'Recuperar Contraseña - CRM Dyco',
                    f'Hola {u.nombre_usuario},\n\nHemos recibido una solicitud para restablecer tu contraseña. Haz clic en el siguiente enlace para continuar:\n\n{link}\n\nSi no solicitaste este cambio, puedes ignorar este mensaje de forma segura.',
                    None,
                    [email],
                    fail_silently=False,
                )
                success = "Te hemos enviado un correo con las instrucciones. Revisa tu bandeja de entrada o spam."
            except Exception as e:
                error = f"Error al enviar el correo: {e}"
        else:
            error = "No encontramos ningún usuario con ese correo electrónico."
            
    return render(request, "recuperar_contrasena.html", {"error": error, "success": success})

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
                    nombre_rep_legal=nombre_rep_legal, activo=True
                )
                return redirect('/')
            except Exception as e: error = f"Error: {e}"
            
    return render(request, "index.html", {
        "activos": Contacto.objects.filter(activo=True).order_by('-fecha_registro'),
        "inactivos": Contacto.objects.filter(activo=False),
        "tipos_contacto": TipoContacto.objects.all(),
        "tipos_doc": TipoIdentificacion.objects.all(),
        "error": error,
        "usuario_logueado": usuario_logueado
    })

def editar_contacto(request, id_contacto):
    if not request.session.get('user_id'): return redirect('/login/')
    p = get_object_or_404(Contacto, id=id_contacto)
    error = ""
    if request.method == "POST":
        p.documento_nit = request.POST.get("documento_nit")
        p.correo = request.POST.get("correo")
        p.celular = request.POST.get("celular")
        p.ciudad = request.POST.get("ciudad")
        p.direccion = request.POST.get("direccion")
        p.tipo_contacto_id = request.POST.get("tipo_contacto")
        p.tipo_doc_id = request.POST.get("tipo_doc")
        
        # Si es Jurídica, borramos campos de Natural y viceversa
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
            p.save()
            return redirect('/')
                
    return render(request, "editar_contacto.html", {
        "c": p, "error": error, 
        "tipos_contacto": TipoContacto.objects.all(),
        "tipos_doc": TipoIdentificacion.objects.all(),
        "usuario_logueado": Usuario.objects.get(id=request.session.get('user_id'))
    })

def cambiar_estado(request, id_contacto):
    if not request.session.get('user_id'): return redirect('/login/')
    c = get_object_or_404(Contacto, id=id_contacto)
    c.activo = not c.activo
    c.save()
    
    # Redirigir de vuelta a la página de origen para una mejor experiencia
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('/')

def sincronizar_correos_imap(request, contacto, usuario_logueado):
    """Sincroniza correos entrantes para un contacto específico."""
    try:
        # Conectar al servidor IMAP
        mail = imaplib.IMAP4_SSL(settings.IMAP_HOST, settings.IMAP_PORT)
        mail.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        mail.select("inbox")

        # Buscar correos del contacto
        status, messages_ids = mail.search(None, f'(FROM "{contacto.correo}")')
        if status != "OK":
            return False

        # Asegurar que el tipo 'Correo' exista
        tipo_correo, _ = TipoInteraccion.objects.get_or_create(nombre_tipo='Correo')

        count = 0
        for num in messages_ids[0].split():
            status, data = mail.fetch(num, "(RFC822)")
            if status != "OK": continue
            
            raw_email = data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Obtener ID del mensaje único
            mid = msg.get("Message-ID")
            if not mid: mid = f"{contacto.correo}-{num.decode()}"

            # Verificar si ya existe
            if Interaccion.objects.filter(mensaje_id=mid).exists():
                continue

            # Extraer Asunto y Cuerpo
            asunto, encoding = decode_header(msg.get("Subject", "Sin Asunto"))[0]
            if isinstance(asunto, bytes):
                asunto = asunto.decode(encoding if encoding else "utf-8")
            
            # Extraer cuerpo (mejorado)
            cuerpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if content_type == "text/plain" and "attachment" not in content_disposition:
                        charset = part.get_content_charset() or "utf-8"
                        try:
                            cuerpo = part.get_payload(decode=True).decode(charset, errors="replace")
                        except:
                            cuerpo = part.get_payload(decode=True).decode("utf-8", errors="replace")
                        break
            else:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    cuerpo = msg.get_payload(decode=True).decode(charset, errors="replace")
                except:
                    cuerpo = msg.get_payload(decode=True).decode("utf-8", errors="replace")

            # Limpiar posibles escapes literales si el texto los trae (como \u000A)
            import re
            def unescape_unicode(text):
                return re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
            
            clean_detalle = unescape_unicode(f"Asunto: {asunto}\n\n{cuerpo}") if asunto else unescape_unicode(cuerpo)

            # Crear Interacción
            Interaccion.objects.create(
                contacto=contacto,
                usuario_responsable=usuario_logueado,
                tipo_interaccion=tipo_correo,
                detalle_actividad=clean_detalle,
                tipo_comunicacion='Entrante',
                mensaje_id=mid
            )
            count += 1
        
        mail.logout()
        return count
    except Exception as e:
        print(f"Error IMAP: {str(e)}")
        return -1

def detalle_contacto(request, id_contacto):
    id_sesion = request.session.get('user_id')
    if not id_sesion: return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    
    contacto = get_object_or_404(Contacto, id=id_contacto)
    
    if request.method == "POST":
        # Opción Eliminar Interacción
        if request.POST.get('accion') == 'eliminar_interaccion':
            id_inter = request.POST.get('interaccion_id')
            inter_a_eliminar = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            tipo_n = inter_a_eliminar.tipo_interaccion.nombre_tipo
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
            if motivo:
                reunion.detalle_actividad = f"{reunion.detalle_actividad}\n\n[CANCELADA] Motivo: {motivo}"
            
            log = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Cancelada por {usuario_logueado.nombre_usuario}"
            reunion.historial_cambios = (reunion.historial_cambios + "\n" + log) if reunion.historial_cambios else log
            
            reunion.save()
            messages.success(request, "Reunión cancelada correctamente.")
            return redirect(f'/contacto/{id_contacto}/?tab=reuniones')

        # Finalizar reunión
        if request.POST.get('accion') == 'finalizar_reunion':
            id_inter = request.POST.get('interaccion_id')
            reunion = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            reunion.estado = 'Finalizada'
            
            log = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Finalizada por {usuario_logueado.nombre_usuario}"
            reunion.historial_cambios = (reunion.historial_cambios + "\n" + log) if reunion.historial_cambios else log
            
            reunion.save()
            messages.success(request, "Reunión marcada como finalizada.")
            return redirect(f'/contacto/{id_contacto}/?tab=reuniones')

        # Editar reunión
        if request.POST.get('accion') == 'editar_reunion':
            id_inter = request.POST.get('interaccion_id')
            reunion = get_object_or_404(Interaccion, id=id_inter, contacto=contacto)
            
            reunion.asunto = request.POST.get('asunto', reunion.asunto)
            reunion.fecha_reunion = request.POST.get('fecha_reunion') or None
            reunion.hora_reunion = request.POST.get('hora_reunion') or None
            reunion.modalidad = request.POST.get('modalidad', reunion.modalidad)
            reunion.direccion = request.POST.get('direccion', '') if reunion.modalidad == 'Presencial' else None
            reunion.detalle_actividad = request.POST.get('detalle', reunion.detalle_actividad)
            
            log = f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Editada por {usuario_logueado.nombre_usuario}"
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
        
        # Capturar asunto si es un correo o una reunión
        asunto = request.POST.get('asunto', '')
        detalle = request.POST.get('detalle', '')
        
        # Si hay asunto de correo, lo prefijamos al detalle
        m_detalle = f"Asunto: {asunto}\n\n{detalle}" if (asunto and tipo_nombre == 'Correo') else (detalle or asunto or '-')

        # Campos de reunión
        fecha_reunion = request.POST.get('fecha_reunion') or None
        hora_reunion = request.POST.get('hora_reunion') or None

        inter = Interaccion.objects.create(
            contacto=contacto,
            usuario_responsable=usuario_logueado,
            tipo_interaccion=tipo_obj,
            detalle_actividad=m_detalle,
            estado='Programada' if tipo_obj.nombre_tipo == 'Reunión' else 'Finalizada',
            modalidad=request.POST.get('modalidad', ''),
            asunto=asunto if asunto else None,
            fecha_reunion=fecha_reunion,
            hora_reunion=hora_reunion,
            direccion=request.POST.get('direccion', '') or None,
            historial_cambios=f"[{timezone.now().strftime('%d/%m/%Y %H:%M')}] Programada por {usuario_logueado.nombre_usuario}" if tipo_obj.nombre_tipo == 'Reunión' else None
        )

        # Lógica de envío real si es correo
        if tipo_obj.nombre_tipo == 'Correo' and contacto.correo:
            try:
                send_mail(
                    asunto if asunto else f"Correo de {usuario_logueado.nombre_usuario}",
                    detalle,
                    None, # Usa DEFAULT_FROM_EMAIL de settings
                    [contacto.correo],
                    fail_silently=False,
                )
                messages.success(request, f"¡Correo enviado con éxito a {contacto.correo}!")
            except Exception as e:
                messages.error(request, f"Error al enviar el correo: {str(e)}")
            return redirect(f'/contacto/{id_contacto}/?tab=correos')
        else:
            messages.success(request, f"{tipo_obj.nombre_tipo} registrada correctamente.")
            # Redirección inteligente por pestaña
            if tipo_obj.nombre_tipo == 'Nota': tabname = 'notas'
            elif tipo_obj.nombre_tipo == 'Reunión': tabname = 'reuniones'
            elif tipo_obj.nombre_tipo == 'Tarea': tabname = 'tareas'
            else: tabname = 'actividad'
            
            return redirect(f'/contacto/{id_contacto}/?tab={tabname}')
            
    interacciones = Interaccion.objects.filter(contacto=contacto).order_by('-fecha_interaccion')
    tipos_interaccion = TipoInteraccion.objects.all()
    
    return render(request, "detalle_contacto.html", {
        "c": contacto,
        "interacciones": interacciones,
        "tipos": tipos_interaccion,
        "usuario_logueado": usuario_logueado,
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
    id_sesion = request.session.get('user_id')
    if not id_sesion or request.session.get('rol_name') != "Administrador":
        return redirect('/')
    
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    usuarios = Usuario.objects.all().order_by('nombre_usuario')
    
    return render(request, "usuarios.html", {
        "usuarios": usuarios,
        "usuario_logueado": usuario_logueado,
        "tipos_contacto": TipoContacto.objects.all(),
        "tipos_doc": TipoIdentificacion.objects.all(),
    })
