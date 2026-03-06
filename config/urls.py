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
    path('', views.contactos, name='contactos'),
    path('interacciones/', views.interacciones, name='interacciones'),
    path('edit/<int:id_contacto>/', views.editar_contacto, name='editar_contacto'),
    path('status/<int:id_contacto>/', views.cambiar_estado, name='cambiar_estado'),
    path('inter_del/<int:id_inter>/', views.eliminar_interaccion, name='eliminar_interaccion'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
]
