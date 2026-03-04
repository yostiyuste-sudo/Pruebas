from django.shortcuts import render, redirect, get_object_or_404
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
        passw = request.POST.get("password")
        
        # Validación de duplicados
        if Usuario.objects.filter(nombre_usuario=nombre).exists():
            error = "Este nombre de usuario ya está ocupado."
        elif Usuario.objects.filter(email=email).exists():
            error = "Este correo electrónico ya está registrado."
        else:
            try:
                Usuario.objects.create(
                    nombre_usuario=nombre,
                    email=email,
                    rol_id=rol_id,
                    password_hash=passw,
                    activo=True
                )
                return redirect('/login/')
            except Exception as e:
                error = f"Error al registrar: {e}"
                
    roles = Rol.objects.all()
    return render(request, "registro.html", {"roles": roles, "error": error})

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
        user_input = request.POST.get("usuario")
        pass_input = request.POST.get("password")
        
        u = Usuario.objects.filter(nombre_usuario=user_input, rol_id=rol_id, password_hash=pass_input, activo=True).first()
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

def contactos(request):
    # Verificación de sesión
    id_sesion = request.session.get('user_id')
    if not id_sesion:
        return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    
    error = ""
    if not TipoContacto.objects.exists():
        TipoContacto.objects.create(nombre_tipo="Persona Natural")
        TipoContacto.objects.create(nombre_tipo="Persona Jurídica")
    if not TipoIdentificacion.objects.exists():
        TipoIdentificacion.objects.create(nombre_tipo="CC")
        TipoIdentificacion.objects.create(nombre_tipo="NIT")
    
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
        
        identificador = nombre if nombre else razon_social
        
        if not identificador or not documento_nit:
            error = "Nombre y Documento son obligatorios."
        elif not correo and not celular:
            error = "Ingrese Correo o Celular."
        else:
            if correo and Contacto.objects.filter(correo=correo).exists():
                error = "Correo ya registrado."
            else:
                try:
                    Contacto.objects.create(
                        tipo_contacto_id=tipo_contacto_id, tipo_doc_id=tipo_doc_id,
                        documento_nit=documento_nit, celular=celular,
                        direccion=direccion, ciudad=ciudad, correo=correo,
                        usuario_asignado=usuario_logueado, nombre=nombre,
                        apellido=apellido, razon_social=razon_social, activo=True
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
        p.nombre = request.POST.get("nombre")
        p.apellido = request.POST.get("apellido")
        p.razon_social = request.POST.get("razon_social")
        p.correo = request.POST.get("correo")
        p.celular = request.POST.get("celular")
        p.ciudad = request.POST.get("ciudad")
        p.direccion = request.POST.get("direccion")
        
        if not (p.nombre if p.nombre else p.razon_social): error = "Nombre obligatorio."
        elif not p.correo and not p.celular: error = "Contacto obligatorio."
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
    return redirect('/')

def interacciones(request):
    id_sesion = request.session.get('user_id')
    if not id_sesion: return redirect('/login/')
    usuario_logueado = Usuario.objects.get(id=id_sesion)
    error = ""
    
    if not TipoInteraccion.objects.exists():
        TipoInteraccion.objects.create(nombre_tipo="Llamada")
        TipoInteraccion.objects.create(nombre_tipo="WhatsApp")

    if request.method == "POST":
        contacto_id = request.POST.get("contacto")
        tipo_id = request.POST.get("tipo_interaccion")
        detalle = request.POST.get("detalle")
        if not detalle or not contacto_id: error = "Datos obligatorios."
        else:
            Interaccion.objects.create(
                contacto_id=contacto_id, usuario_responsable=usuario_logueado,
                tipo_interaccion_id=tipo_id, detalle_actividad=detalle,
                es_exitosa=request.POST.get("es_exitosa")=="on"
            )
            return redirect('/interacciones/')

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
