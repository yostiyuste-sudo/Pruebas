from django.shortcuts import render, redirect
from .models import Contacto, TipoContacto, TipoIdentificacion
from django.db.models import Q

def contactos(request):
    error = ""
    
    # 1. Creamos tipos por defecto si la base de datos está vacía para que no falle la web
    if not TipoContacto.objects.exists():
        TipoContacto.objects.create(nombre_tipo="Cliente")
        TipoContacto.objects.create(nombre_tipo="Proveedor")
    if not TipoIdentificacion.objects.exists():
        TipoIdentificacion.objects.create(nombre_tipo="CC")
        TipoIdentificacion.objects.create(nombre_tipo="NIT")
    
    # 2. Si enviamos el formulario HTML al servidor
    if request.method == "POST":
        tipo_contacto_id = request.POST.get("tipo_contacto")
        tipo_doc_id = request.POST.get("tipo_doc")
        documento_nit = request.POST.get("documento_nit")
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        telefono = request.POST.get("telefono")
        
        # Validar medio de contacto (Regla 1)
        if not correo and not telefono:
            error = "Debes ingresar al menos un correo o un teléfono."
        elif not nombre:
            error = "Debes ingresar el nombre del contacto."
        elif not documento_nit:
            error = "Debes ingresar el Documento / NIT."
        else:
            # Validar si el correo está duplicado (Regla 2)
            if correo and Contacto.objects.filter(correo=correo).exists():
                error = "Ya existe un contacto registrado con ese correo en el sistema."
            else:
                try:
                    tipo_contacto = TipoContacto.objects.get(id=tipo_contacto_id)
                    tipo_doc = TipoIdentificacion.objects.get(id=tipo_doc_id)
                    
                    # Guardamos el contacto con los nuevos campos
                    Contacto.objects.create(
                        tipo_contacto=tipo_contacto,
                        tipo_doc=tipo_doc,
                        documento_nit=documento_nit,
                        nombre=nombre,
                        correo=correo,
                        telefono=telefono,
                    )
                    return redirect('/') # Recargar la página limpia
                except Exception as e:
                    error = f"Ocurrió un error al guardar: {e}"
            
    # Mostrar la página web con las listas para armar el formulario
    lista_contactos = Contacto.objects.all().order_by('-fecha_registro')
    tipos_contacto = TipoContacto.objects.all()
    tipos_doc = TipoIdentificacion.objects.all()
    
    return render(request, "index.html", {
        "contactos": lista_contactos,
        "tipos_contacto": tipos_contacto,
        "tipos_doc": tipos_doc,
        "error": error
    })
