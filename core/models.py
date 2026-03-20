from django.db import models

class Rol(models.Model):
    nombre_rol = models.CharField(max_length=50)

    def __str__(self):
        return self.nombre_rol

class Usuario(models.Model):
<<<<<<< HEAD
    # Relación con el modelo Rol
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE) 
=======
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
>>>>>>> 2007be47f625f7ff45b41f1ffd84e0aec86bcd8a
    nombre_usuario = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    activo = models.BooleanField(default=True)
<<<<<<< HEAD
    
    # --- CAMPO AGREGADO AQUÍ ---
    token_verificacion = models.CharField(max_length=100, null=True, blank=True)
=======
    token_verificacion = models.CharField(max_length=100, blank=True, null=True)
    token_password = models.CharField(max_length=100, blank=True, null=True)
>>>>>>> 2007be47f625f7ff45b41f1ffd84e0aec86bcd8a

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
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.razon_social if self.razon_social else f"{self.nombre} {self.apellido}"

class Interaccion(models.Model):
    contacto = models.ForeignKey(Contacto, on_delete=models.CASCADE)
    usuario_responsable = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True)
    tipo_interaccion = models.ForeignKey(TipoInteraccion, on_delete=models.CASCADE)
    detalle_actividad = models.TextField()
    es_exitosa = models.BooleanField(default=False)
    procede_a_compromiso = models.BooleanField(default=False)
    fecha_interaccion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(null=True, blank=True)
    
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
    historial_cambios = models.TextField(blank=True, null=True)

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

