from django.db import models
from django.contrib.auth.models import User

class TipoIdentificacion(models.Model):
    nombre_tipo = models.CharField(max_length=50)
    def __str__(self): return self.nombre_tipo

class TipoContacto(models.Model):
    nombre_tipo = models.CharField(max_length=50)
    def __str__(self): return self.nombre_tipo

class TipoInteraccion(models.Model):
    nombre_tipo = models.CharField(max_length=50)
    def __str__(self): return self.nombre_tipo

class Contacto(models.Model):
    tipo_contacto = models.ForeignKey(TipoContacto, on_delete=models.CASCADE)
    tipo_doc = models.ForeignKey(TipoIdentificacion, on_delete=models.CASCADE)
    documento_nit = models.CharField(max_length=25)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    correo = models.EmailField(max_length=150, blank=True, null=True)
    usuario_asignado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    fecha_expedicion = models.DateField(blank=True, null=True)
    estado_civil = models.CharField(max_length=50, blank=True, null=True)
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    nombre_rep_legal = models.CharField(max_length=150, blank=True, null=True)
    id_rep_legal = models.CharField(max_length=25, blank=True, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre if self.nombre else self.razon_social

class Interaccion(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE)
    usuario_responsable = models.ForeignKey(User, on_delete=models.CASCADE)
    tipo_interaccion = models.ForeignKey(TipoInteraccion, on_delete=models.CASCADE)
    detalle_actividad = models.TextField()
    es_exitosa = models.BooleanField(default=False)
    procede_a_compromiso = models.BooleanField(default=False)
    fecha_interaccion = models.DateTimeField(auto_now_add=True)

class Compromiso(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    ]
    interaccion = models.ForeignKey(Interaccion, on_delete=models.CASCADE)
    descripcion_compromiso = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='Pendiente')
    fecha_limite = models.DateField()
