from django.db import models

class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre_rol

class Usuario(models.Model):

    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    nombre_usuario = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)

    
    token_verificacion = models.CharField(max_length=100, null=True, blank=True)
    token_password = models.CharField(max_length=100, blank=True, null=True)

    # Campos para actualización de correo electrónico
    nuevo_email_pendiente = models.EmailField(null=True, blank=True)
    token_cambio_email = models.CharField(max_length=6, null=True, blank=True)
    token_cambio_email_expiracion = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre_usuario

class TipoIdentificacion(models.Model):
    nombre_tipo = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre_tipo

class TipoContacto(models.Model):
    nombre_tipo = models.CharField(max_length=50) # Ej: 'Persona Natural', 'Persona Juridica'

    def __str__(self):
        return self.nombre_tipo

class TipoInteraccion(models.Model):
    nombre_tipo = models.CharField(max_length=50) # Ejemplo: 'Llamada', 'Correo', 'Nota'

    def __str__(self):
        return self.nombre_tipo

class Contacto(models.Model):
    tipo_contacto = models.ForeignKey(TipoContacto, on_delete=models.CASCADE)
    tipo_doc = models.ForeignKey(TipoIdentificacion, on_delete=models.CASCADE)
    documento_nit = models.CharField(max_length=25)
    
    # Atributos Compartidos
    telefono = models.CharField(max_length=20, blank=True, null=True)
    celular = models.CharField(max_length=20, blank=True, null=True)
    direccion = models.CharField(max_length=255, blank=True, null=True)
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    correo = models.EmailField(max_length=150, blank=True, null=True)
    usuario_asignado = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    
    # Atributos de Persona Natural
    nombre = models.CharField(max_length=100, blank=True, null=True)
    apellido = models.CharField(max_length=100, blank=True, null=True)
    fecha_expedicion = models.DateField(blank=True, null=True)
    estado_civil = models.CharField(max_length=50, blank=True, null=True)
    
    # Atributos de Persona Jurídica
    razon_social = models.CharField(max_length=200, blank=True, null=True)
    nombre_rep_legal = models.CharField(max_length=150, blank=True, null=True)
    id_rep_legal = models.CharField(max_length=25, blank=True, null=True)
    
    # Nuevos atributos de Proyecto
    tipo_proyecto = models.CharField(max_length=150, blank=True, null=True)
    proyecto_nombre = models.CharField(max_length=150, blank=True, null=True)
    torre = models.CharField(max_length=50, blank=True, null=True)
    apartamento = models.CharField(max_length=50, blank=True, null=True)
    tipo_contrato = models.CharField(max_length=50, blank=True, null=True)
    
    # Nuevos atributos Personales/Laborales
    ocupacion = models.CharField(max_length=150, blank=True, null=True)
    otra_ocupacion = models.CharField(max_length=150, blank=True, null=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    edad = models.IntegerField(blank=True, null=True)
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    historial_cambios = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.razon_social if self.razon_social else f"{self.nombre} {self.apellido}"

    @property
    def bell_count(self):
        from .models import Interaccion
        calls = Interaccion.objects.filter(contacto=self, tipo_interaccion__nombre_tipo='Llamada', estado='Programada').count()
        emails = Interaccion.objects.filter(contacto=self, tipo_interaccion__nombre_tipo='Correo', tipo_comunicacion='Entrante').count()
        meetings = Interaccion.objects.filter(contacto=self, tipo_interaccion__nombre_tipo='Reunión', estado='Programada').count()
        return calls + emails + meetings

    @property
    def clock_count(self):
        from .models import Interaccion
        from datetime import datetime, time
        from django.utils import timezone
        
        scheduled = Interaccion.objects.filter(
            contacto=self, 
            tipo_interaccion__nombre_tipo__in=['Llamada', 'Reunión'], 
            estado='Programada',
            fecha_reunion__isnull=False
        )
        
        now = timezone.localtime(timezone.now())
        count = 0
        
        for inter in scheduled:
            f = inter.fecha_reunion
            h = inter.hora_reunion or time(0, 0)
            
            try:
                event_dt = timezone.make_aware(datetime.combine(f, h), timezone.get_current_timezone())
                diff = event_dt - now
                diff_hours = diff.total_seconds() / 3600.0
                
                if diff_hours <= 24:
                    count += 1
            except Exception:
                pass
                
        return count

class Interaccion(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE)
    usuario_responsable = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True)
    tipo_interaccion = models.ForeignKey(TipoInteraccion, on_delete=models.CASCADE)
    detalle_actividad = models.TextField()
    es_exitosa = models.BooleanField(default=False)
    procede_a_compromiso = models.BooleanField(default=False)
    fecha_interaccion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    # Campos adicionales basados en la vista y DB
    tipo_comunicacion = models.CharField(max_length=10, default='Saliente') # 'Entrante' / 'Saliente'
    mensaje_id = models.CharField(max_length=255, blank=True, null=True)
    destacado = models.BooleanField(default=False)
    estado = models.CharField(max_length=20, default='Finalizada') # 'Programada', 'Finalizada', 'Cancelada'
    modalidad = models.CharField(max_length=50, blank=True, null=True)
    asunto = models.CharField(max_length=255, blank=True, null=True)
    fecha_reunion = models.DateField(null=True, blank=True)
    hora_reunion = models.TimeField(null=True, blank=True)
    direccion = models.CharField(max_length=300, blank=True, null=True)
    enlace_reunion = models.URLField(max_length=500, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='sub_interacciones')
    historial_cambios = models.TextField(blank=True, null=True)

    # Nuevos campos obligatorios para estadísticas analíticas
    canal_comunicacion = models.ForeignKey(TipoInteraccion, on_delete=models.SET_NULL, null=True, blank=True, related_name='interacciones_canal')
    duracion_minutos = models.PositiveIntegerField(null=True, blank=True)
    temperatura_emocional = models.PositiveIntegerField(null=True, blank=True, choices=[(i, str(i)) for i in range(1, 6)])

class Compromiso(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    ]
    
    interaccion = models.ForeignKey(Interaccion, on_delete=models.CASCADE)
    descripcion_compromiso = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='Pendiente')
    fecha_limite = models.DateField()

class FirmaDigital(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='firma_digital')
    html_content = models.TextField(blank=True, null=True)
    pdf_attachment = models.FileField(upload_to='firmas_pdf/', blank=True, null=True)

    def __str__(self):
        return f"Firma de {self.usuario.nombre_usuario}"

class MensajeWhatsApp(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE, related_name='mensajes_whatsapp')
    remitente_usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    texto = models.TextField()
    fecha_envio = models.DateTimeField(auto_now_add=True)
    direccion = models.CharField(max_length=10, choices=[('Entrante', 'Entrante'), ('Saliente', 'Saliente')])
    whatsapp_id = models.CharField(max_length=255, blank=True, null=True)
    estado = models.CharField(max_length=20, default='enviado')

    def __str__(self):
        return f"Mensaje to/from {self.contacto}: {self.texto[:30]}"


