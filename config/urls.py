"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('contactos/', views.contactos, name='contactos'),
    path('contacto/<int:id_contacto>/', views.detalle_contacto, name='detalle_contacto'),
    path('interacciones/', views.interacciones, name='interacciones'),
    path('edit/<int:id_contacto>/', views.editar_contacto, name='editar_contacto'),
    path('status/<int:id_contacto>/', views.cambiar_estado, name='cambiar_estado'),
    path('inter_del/<int:id_inter>/', views.eliminar_interaccion, name='eliminar_interaccion'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('incidencias/', views.incidencias_view, name='incidencias'),
    path('contacto/<int:id_contacto>/destacar/<int:id_interaccion>/', views.destacar_interaccion, name='destacar_interaccion'),
    path('contacto/<int:id_contacto>/ajax-sync-correos/', views.ajax_sincronizar_correos, name='ajax_sincronizar_correos'),
    path('verificar/', views.verificar_correo, name='verificar_correo'),
    path('reenviar-pin/', views.reenviar_pin, name='reenviar_pin'),
    path('cambiar-correo-registro/', views.cambiar_correo_registro, name='cambiar_correo_registro'),
    path('recuperar-contrasena/', views.recuperar_contrasena_view, name='recuperar_contrasena'),
    path('resetear-contrasena/<str:token>/', views.resetear_contrasena_view, name='resetear_contrasena'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('configurar-firma/', views.configurar_firma, name='configurar_firma'),
    path('subir-adjunto/', views.subir_adjunto, name='subir_adjunto'),
    path('contacto/<int:id_contacto>/whatsapp/enviar/', views.enviar_mensaje_whatsapp, name='enviar_mensaje_whatsapp'),
    path('contacto/<int:id_contacto>/whatsapp/mensajes/', views.obtener_mensajes_whatsapp, name='obtener_mensajes_whatsapp'),
    path('contacto/<int:id_contacto>/alertas/', views.obtener_notificaciones_contacto, name='obtener_notificaciones_contacto'),
    path('whatsapp/webhook/', views.whatsapp_webhook, name='whatsapp_webhook'),
]

from django.conf import settings
from django.conf.urls.static import static

# Auto-migration of firmas_pdf directory to media/firmas_pdf if needed
import os
import shutil
src_firmas = os.path.join(settings.BASE_DIR, 'firmas_pdf')
dst_firmas = os.path.join(settings.BASE_DIR, 'media', 'firmas_pdf')
if os.path.exists(src_firmas) and not os.path.exists(dst_firmas):
    try:
        os.makedirs(os.path.join(settings.BASE_DIR, 'media'), exist_ok=True)
        shutil.move(src_firmas, dst_firmas)
        print("[AUTO-MIGRATION] Moved firmas_pdf to media/firmas_pdf successfully!")
    except Exception as e:
        print("[AUTO-MIGRATION] Error moving firmas_pdf:", e)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

