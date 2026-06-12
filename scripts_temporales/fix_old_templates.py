import os
import re

directory = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas'
files = ['incidencias.html', 'usuarios.html']

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

new_css = """
        /* --- SIDEBAR NUEVA --- */
        .barra-lateral {
            position: fixed; top: 0; left: 0; height: 100vh;
            width: 90px; background-color: #1a2232; border-right: 1px solid #111827;
            display: flex; flex-direction: column; z-index: 1000;
            transition: var(--ease); padding-bottom: 30px; overflow: hidden;
            align-items: center;
        }
        .barra-lateral:hover { width: 290px; align-items: stretch; }
        
        .barra-cabecera { padding: 40px 0; display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%; transition: 0.3s; }
        .barra-lateral:hover .barra-cabecera { padding: 40px 25px; justify-content: flex-start; }
        
        .logo-d { 
            min-width: 48px; height: 48px; 
            background: #a82e2e; color: white; display: flex; align-items: center; justify-content: center;
            border-radius: 14px; font-weight: 800; font-size: 24px;
        }
        .logo-texto { font-weight: 800; font-size: 22px; color: #ffffff; letter-spacing: -0.5px; opacity: 0; transition: 0.3s; white-space: nowrap; display: none; margin-left: 5px; }
        .barra-lateral:hover .logo-texto { opacity: 1; display: block; }

        .navegacion { flex: 1; width: 100%; padding: 0 15px; display: flex; flex-direction: column; align-items: center; gap: 8px; }
        .barra-lateral:hover .navegacion { align-items: stretch; padding: 0 20px; }
        
        .nav-enlace { 
            display: flex; align-items: center; justify-content: center; width: 56px; min-height: 56px; 
            text-decoration: none; color: #94a3b8; border-radius: 16px; 
            transition: 0.3s; font-weight: 700; font-size: 16px; white-space: nowrap;
        }
        .barra-lateral:hover .nav-enlace { width: 100%; justify-content: flex-start; padding: 16px 22px; border-radius: 20px; gap: 18px; }
        
        .nav-enlace:hover { background: rgba(255, 255, 255, 0.05); color: #ffffff; }
        .nav-enlace.activo { 
            background: rgba(168, 46, 46, 0.15); color: #ffffff !important; 
            border-left: 4px solid #a82e2e;
            border-radius: 20px 0 0 20px;
        }
        .nav-enlace.activo svg { stroke: #a82e2e; }
        .nav-text { opacity: 0; transition: 0.3s; display: none; }
        .barra-lateral:hover .nav-text { opacity: 1; display: block; }
        
        /* Mobile styles override */
        @media (max-width: 768px) {
            .barra-lateral {
                width: 280px !important;
                position: fixed !important;
                left: -280px !important;
                height: 100dvh !important;
                padding-bottom: 50px !important;
                overflow-y: auto !important;
                transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), left 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
                z-index: 10000 !important;
            }
            .barra-lateral.activo {
                left: 0 !important;
                box-shadow: 15px 0 50px rgba(0,0,0,0.15) !important;
            }
            .barra-lateral:hover { width: 280px !important; }
            .barra-lateral:hover .logo-texto, .barra-lateral:hover .nav-text { display: block !important; opacity: 1 !important; }
            .nav-enlace {
                width: 100% !important;
                justify-content: flex-start !important;
                padding: 16px 22px !important;
                border-radius: 20px !important;
                gap: 18px !important;
            }
            .barra-lateral:hover ~ .wrapper { margin-left: 0 !important; width: 100% !important; }
        }
"""

for f in files:
    path = os.path.join(directory, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
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
    
    # Remove old sidebar HTML
    new_content = re.sub(r'<aside class="sidebar">.*?</aside>', new_sidebar, content, flags=re.DOTALL)
    
    # Adjust CSS
    # Add new CSS before </style>
    if '/* --- SIDEBAR NUEVA --- */' not in new_content:
        new_content = new_content.replace('</style>', new_css + '\n    </style>')
    
    # Update wrapper padding/margin logic
    new_content = re.sub(r'\.wrapper\{padding:25px 25px 25px 115px;transition:var\(--ease\);width:100%\}', r'.wrapper{margin-left: 90px; padding:25px; transition:var(--ease); width:calc(100% - 90px)}', new_content)
    new_content = re.sub(r'\.sidebar:hover~\.wrapper\{padding-left:315px\}', r'.barra-lateral:hover~.wrapper{margin-left:290px; width:calc(100% - 290px)}', new_content)
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')
    else:
        print(f'No changes for {f}')
print("Done.")
