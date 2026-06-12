import os

directory = r"c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas"
files = [
    "usuarios.html", "interacciones.html", "editar_contacto.html", 
    "index.html", "detalle_contacto.html", "dashboard.html", "calendario.html"
]

for file in files:
    path = os.path.join(directory, file)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        
        new_content = content.replace(
            '<div class="logo-d">D</div>', 
            '<img src="{% static \'img/logo_dyco.png\' %}" alt="Logo" style="width: 48px; height: 48px; object-fit: contain; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">'
        )
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)
print("Reemplazo exitoso en todos los archivos.")
