import os
import re
import glob

def resolver_conflictos(directorio):
    patron = re.compile(
        r'<<<<<<< Updated upstream\r?\n(.*?)=======\r?\n(.*?)>>>>>>> Stashed changes\r?\n',
        re.DOTALL
    )

    for ruta_archivo in glob.glob(os.path.join(directorio, '*.html')):
        with open(ruta_archivo, 'r', encoding='utf-8', errors='replace') as f:
            contenido = f.read()

        if '<<<<<<< Updated upstream' in contenido:
            print(f"Resolviendo conflictos en {ruta_archivo}...")
            # Reemplazamos quedándonos con lo que está abajo de los ======= (Stashed changes)
            nuevo_contenido = patron.sub(lambda m: m.group(2), contenido)
            
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(nuevo_contenido)
            print("  -> ¡Resuelto!")

if __name__ == "__main__":
    resolver_conflictos(r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas')
