from django.shortcuts import render, redirect
from .models import Contacto, TipoContacto, TipoIdentificacion, Interaccion, TipoInteraccion, Usuario, Rol

def contactos(request):
    error = ""
    
    # === INICIALIZACIÓN DE DATOS BASE (Para que no falle si la BD está limpia) ===
    if not TipoContacto.objects.exists():
        TipoContacto.objects.create(nombre_tipo="Persona Natural")
        TipoContacto.objects.create(nombre_tipo="Persona Jurídica")
    if not TipoIdentificacion.objects.exists():
        TipoIdentificacion.objects.create(nombre_tipo="CC")
        TipoIdentificacion.objects.create(nombre_tipo="NIT")
    
    # Crear un usuario y rol por defecto si no existen
    if not Rol.objects.exists():
        rol_admin = Rol.objects.create(nombre_rol="Administrador")
    else:
        rol_admin = Rol.objects.first()
        
    if not Usuario.objects.exists():
        usuario_def = Usuario.objects.create(
            rol=rol_admin,
            nombre_usuario="Usuario por Defecto",
            email="admin@constructora.com",
            password_hash="123456"
        )
    else:
        usuario_def = Usuario.objects.first()

    # === LÓGICA DE GUARDADO (POST) ===
    if request.method == "POST":
        # Atributos Compartidos
        tipo_contacto_id = request.POST.get("tipo_contacto")
        tipo_doc_id = request.POST.get("tipo_doc")
        documento_nit = request.POST.get("documento_nit")
        telefono = request.POST.get("telefono")
        celular = request.POST.get("celular")
        direccion = request.POST.get("direccion")
        ciudad = request.POST.get("ciudad")
        correo = request.POST.get("correo")
        
        # Atributos Persona Natural
        nombre = request.POST.get("nombre")
        apellido = request.POST.get("apellido")
        # Atributos Persona Jurídica
        razon_social = request.POST.get("razon_social")
        
        # === REGLA: Nombre y al menos un medio de contacto son obligatorios ===
        identificador = nombre if nombre else razon_social
        
        if not identificador:
            error = "El Nombre o Razón Social es obligatorio."
        elif not correo and not telefono and not celular:
            error = "Debes ingresar al menos un medio de contacto (Correo, Teléfono o Celular)."
        elif not documento_nit:
            error = "El Documento o NIT es obligatorio."
        else:
            # === REGLA: No se permiten duplicados con el mismo correo ===
            if correo and Contacto.objects.filter(correo=correo).exists():
                error = "Ya existe un contacto registrado con ese correo."
            else:
                try:
                    tipo_contacto = TipoContacto.objects.get(id=tipo_contacto_id)
                    tipo_doc = TipoIdentificacion.objects.get(id=tipo_doc_id)
                    
                    # Guardamos el contacto con TODO el nuevo esquema SQL
                    Contacto.objects.create(
                        tipo_contacto=tipo_contacto,
                        tipo_doc=tipo_doc,
                        documento_nit=documento_nit,
                        telefono=telefono,
                        celular=celular,
                        direccion=direccion,
                        ciudad=ciudad,
                        correo=correo,
                        usuario_asignado=usuario_def, # Asignamos el usuario por defecto
                        nombre=nombre,
                        apellido=apellido,
                        razon_social=razon_social,
                        activo=True
                    )
                    return redirect('/') 
                except Exception as e:
                    error = f"Error al guardar: {e}"
            
    # === DATOS PARA LA VISTA ===
    # Solo mostrar contactos activos (Cumpliendo Requerimiento Jira)
    lista_contactos = Contacto.objects.filter(activo=True).order_by('-fecha_registro')
    tipos_contacto = TipoContacto.objects.all()
    tipos_doc = TipoIdentificacion.objects.all()
    
    return render(request, "index.html", {
        "activos": Contacto.objects.filter(activo=True),
        "inactivos": Contacto.objects.filter(activo=False),
        "tipos_contacto": tipos_contacto,
        "tipos_doc": tipos_doc,
        "error": error
    })

# === FUNCIONES DE SCRUM-2 (Editar e Inactivar) ===
def editar_contacto(request, id_contacto):
    p = Contacto.objects.get(id=id_contacto)
    error = ""
    
    if request.method == "POST":
        # Traer datos del formulario de edición
        p.documento_nit = request.POST.get("documento_nit")
        p.nombre = request.POST.get("nombre")
        p.apellido = request.POST.get("apellido")
        p.razon_social = request.POST.get("razon_social")
        p.correo = request.POST.get("correo")
        p.celular = request.POST.get("celular")
        p.ciudad = request.POST.get("ciudad")
        p.direccion = request.POST.get("direccion")
        
        # Validaciones de SCRUM-2
        if not (p.nombre if p.nombre else p.razon_social):
            error = "El nombre/razón social es obligatorio."
        elif not p.correo and not p.celular:
            error = "Al menos un contacto es obligatorio."
        else:
            # Control de duplicados por correo (Si cambió el correo)
            if p.correo and Contacto.objects.filter(correo=p.correo).exclude(id=p.id).exists():
                error = "Este correo ya está registrado en otro contacto."
            else:
                p.save()
                return redirect('/')
                
    tipos_contacto = TipoContacto.objects.all()
    tipos_doc = TipoIdentificacion.objects.all()
    return render(request, "editar_contacto.html", {
        "c": p, 
        "error": error,
        "tipos_contacto": tipos_contacto,
        "tipos_doc": tipos_doc
    })

def cambiar_estado(request, id_contacto):
    # Criterio: El sistema debe permitir activar o desactivar contactos
    try:
        c = Contacto.objects.get(id=id_contacto)
        c.activo = not c.activo # Si es True cambia a False, y viceversa
        c.save()
    except:
        pass
    return redirect('/')

# === LÓGICA DE INTERACCIONES (Modificada para SCRUM-2) ===
def interacciones(request):
    error = ""
    if not TipoInteraccion.objects.exists():
        TipoInteraccion.objects.create(nombre_tipo="Llamada")
        TipoInteraccion.objects.create(nombre_tipo="WhatsApp")

    usuario_def = Usuario.objects.get_or_create(nombre_usuario="Admin", email="a@a.com")[0]

    if request.method == "POST":
        contacto_id = request.POST.get("contacto")
        tipo_id = request.POST.get("tipo_interaccion")
        detalle = request.POST.get("detalle")
        
        if not detalle or not contacto_id:
            error = "El contacto y el detalle son obligatorios."
        else:
            Interaccion.objects.create(
                contacto_id=contacto_id,
                usuario_responsable=usuario_def,
                tipo_interaccion_id=tipo_id,
                detalle_actividad=detalle,
                es_exitosa=request.POST.get("es_exitosa")=="on"
            )
            return redirect('/interacciones/')

    # Criterio SCRUM-2: Seleccionar solo contactos activos para interacciones
    contactos_activos = Contacto.objects.filter(activo=True)
    historial = Interaccion.objects.all().order_by('-fecha_interaccion')
    tipos = TipoInteraccion.objects.all()
    
    return render(request, "interacciones.html", {
        "interacciones": historial,
        "contactos": contactos_activos, # Solo pasamos los activos
        "tipos": tipos,
        "error": error
    })

def eliminar_interaccion(request, id_inter):
    try:
        Interaccion.objects.get(id=id_inter).delete()
    except:
        pass
    return redirect('/interacciones/')
