import os
import re

directory = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas'
files = [f for f in os.listdir(directory) if f.endswith('.html')]

sidebar_template = """    <!-- BARRA LATERAL -->
    <aside class="barra-lateral">
        <div class="barra-cabecera">
            <img src="{% static 'img/logo_dyco.png' %}" alt="Logo DYCO" style="width: 48px; height: 48px; object-fit: contain; border-radius: 12px; background: white; padding: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
            <div class="logo-texto">CONSTRUCTORA</div>
        </div>

        <nav class="navegacion">
            <a href="{% url 'dashboard' %}" class="nav-enlace{DASHBOARD_ACTIVO}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
                <span class="nav-text">Inicio</span>
            </a>
            <a href="{% url 'contactos' %}" class="nav-enlace{CONTACTOS_ACTIVO}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path></svg>
                <span class="nav-text">Registro de Contacto</span>
            </a>
            <a href="{% url 'interacciones' %}" class="nav-enlace{INTERACCIONES_ACTIVO}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span class="nav-text">Interacciones</span>
            </a>
            {% if usuario_logueado.rol.nombre_rol == "Administrador" %}
            <a href="{% url 'usuarios' %}" class="nav-enlace{USUARIOS_ACTIVO}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <span class="nav-text">Gestión de Usuarios</span>
            </a>
            {% endif %}
            <a href="{% url 'incidencias' %}" class="nav-enlace{INCIDENCIAS_ACTIVO}">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
                <span class="nav-text">Incidencias</span>
            </a>
        </nav>

        <!-- ── PERFIL BOTTOM (Configuraciones) ── -->
        {% include 'configuraciones.html' %}
    </aside>"""

for f in files:
    if f == 'configuraciones.html':
        continue
    path = os.path.join(directory, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '<aside class="barra-lateral">' in content:
        d_activo = " activo" if f == 'dashboard.html' else ""
        c_activo = " activo" if f in ['index.html', 'detalle_contacto.html', 'editar_contacto.html', 'detalle_contacto.html.tmp', 'nuevo_contacto.html', 'registro_contactos.html'] else ""
        i_activo = " activo" if f == 'interacciones.html' else ""
        u_activo = " activo" if f == 'usuarios.html' else ""
        inc_activo = " activo" if f == 'incidencias.html' else ""
        
        new_sidebar = sidebar_template.replace('{DASHBOARD_ACTIVO}', d_activo)
        new_sidebar = new_sidebar.replace('{CONTACTOS_ACTIVO}', c_activo)
        new_sidebar = new_sidebar.replace('{INTERACCIONES_ACTIVO}', i_activo)
        new_sidebar = new_sidebar.replace('{USUARIOS_ACTIVO}', u_activo)
        new_sidebar = new_sidebar.replace('{INCIDENCIAS_ACTIVO}', inc_activo)
        
        new_content = re.sub(r'<aside class="barra-lateral">.*?</aside>', new_sidebar, content, flags=re.DOTALL)
        
        if new_content != content:
            with open(path, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f'Updated {f}')
        else:
            print(f'No changes for {f}')
print("Done.")
