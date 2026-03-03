from django.contrib import admin
from .models import (
    Rol, Usuario, TipoIdentificacion, TipoContacto, 
    TipoInteraccion, Contacto, Interaccion, Compromiso
)

# Registro básico de tus modelos
admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(TipoIdentificacion)
admin.site.register(TipoContacto)
admin.site.register(TipoInteraccion)
admin.site.register(Contacto)
admin.site.register(Interaccion)
admin.site.register(Compromiso)
