import re

path = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\core\views.py'
with open(path, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()

# Función para resolver conflictos: quedarse con la versión de JARY (la de abajo, >>>>>>>)
def resolver_conflicto(match):
    # match.group(1) = contenido HEAD (lo viejo/tuyo)
    # match.group(2) = contenido de Jary (nuevo)
    return match.group(2)

# Patrón para capturar bloques de conflicto
patron = re.compile(
    r'<<<<<<< HEAD\r?\n(.*?)=======\r?\n(.*?)>>>>>>> [^\r\n]+\r?\n',
    re.DOTALL
)

conflictos_encontrados = len(patron.findall(content))
print(f"Conflictos encontrados: {conflictos_encontrados}")

content_resuelto = patron.sub(resolver_conflicto, content)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content_resuelto)

print("Conflictos resueltos con el código de Jary.")
