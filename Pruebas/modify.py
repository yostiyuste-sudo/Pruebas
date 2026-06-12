import sys
path = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas\detalle_contacto.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace tabs-header-top
old_tabs = '''            <div class="tabs-header-top">
                <button class="tab-top" id="btn-top-desc" onclick="cambiarTabPrincipal('descripcion')">Descripción</button>
                <button class="tab-top active" id="btn-top-activ"
                    onclick="cambiarTabPrincipal('actividades')">Actividades</button>
                <button class="tab-top" id="btn-top-chat" onclick="cambiarTabPrincipal('chat')">Chat cliente</button>
            </div>'''
new_tabs = '''            <div class="tabs-header-top" style="justify-content: space-between; padding-right: 20px;">
                <div style="display: flex; gap: 35px;">
                    <button class="tab-top" id="btn-top-desc" onclick="cambiarTabPrincipal('descripcion')">Descripción</button>
                    <button class="tab-top active" id="btn-top-activ"
                        onclick="cambiarTabPrincipal('actividades')">Actividades</button>
                    <button class="tab-top" id="btn-top-chat" onclick="cambiarTabPrincipal('chat')">Chat cliente</button>
                </div>
                <div style="display: flex; align-items: center;">
                    <button id="btn-toggle-datos" onclick="toggleDatosAdicionales()" style="background: var(--rojo-primario); color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; transition: 0.2s; box-shadow: 0 4px 10px rgba(183, 28, 28, 0.2);">Datos adicionales</button>
                </div>
            </div>'''

if old_tabs in content:
    content = content.replace(old_tabs, new_tabs)
    print('Replaced tabs-header-top')
else:
    print('Could not find tabs-header-top')

# Inject wrappers
old_desc = '<!-- CONTENIDO DESCRIPCIÓN -->'
new_desc = '''<div id="main-tabs-wrapper" style="display: flex; flex: 1; overflow: hidden; width: 100%;">
                <div id="tabs-content-area" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
            <!-- CONTENIDO DESCRIPCIÓN -->'''

if old_desc in content:
    content = content.replace(old_desc, new_desc, 1)
    print('Injected wrapper start')
else:
    print('Could not find CONTENIDO DESCRIPCIÓN')

old_end = '''                </div>
            </div>
        </section>
    </main>'''
new_end = '''                </div>
            </div>
            </div> <!-- End tabs-content-area -->

            <!-- PANEL DATOS ADICIONALES -->
            <div id="panel-datos-adicionales" style="width: 320px; background: #f8fafc; border-left: 1px solid var(--gris-borde); display: none; flex-direction: column; overflow-y: auto; transition: width 0.3s ease;">
                <div style="padding: 20px; border-bottom: 1px solid var(--gris-borde); display: flex; justify-content: space-between; align-items: center; background: white; position: sticky; top: 0; z-index: 10;">
                    <h3 style="font-size: 15px; font-weight: 800; color: var(--texto-principal); margin: 0;">Datos Adicionales</h3>
                    <button onclick="cerrarDatosAdicionalesManual()" id="btn-cerrar-datos" style="background: #f1f5f9; border: none; cursor: pointer; color: var(--texto-secundario); font-size: 16px; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: 0.2s;">&times;</button>
                </div>
                <div style="padding: 24px; display: flex; flex-direction: column; gap: 20px;">
                    <div class="dato-card" style="background: white; padding: 16px; border-radius: 12px; border: 1px solid var(--gris-borde); box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                        <div style="font-size: 11px; color: var(--texto-secundario); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Proyecto</div>
                        <div style="font-size: 14px; color: var(--texto-principal); font-weight: 600; word-break: break-word;">{{ c.proyecto|default:'Información no disponible' }}</div>
                    </div>
                    <div class="dato-card" style="background: white; padding: 16px; border-radius: 12px; border: 1px solid var(--gris-borde); box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                        <div style="font-size: 11px; color: var(--texto-secundario); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Trabajo</div>
                        <div style="font-size: 14px; color: var(--texto-principal); font-weight: 600; word-break: break-word;">{{ c.info_trabajo|default:'Información no disponible' }}</div>
                    </div>
                    <div class="dato-card" style="background: white; padding: 16px; border-radius: 12px; border: 1px solid var(--gris-borde); box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                        <div style="font-size: 11px; color: var(--texto-secundario); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Cargo</div>
                        <div style="font-size: 14px; color: var(--texto-principal); font-weight: 600; word-break: break-word;">{{ c.cargo|default:'Información no disponible' }}</div>
                    </div>
                    <div class="dato-card" style="background: white; padding: 16px; border-radius: 12px; border: 1px solid var(--gris-borde); box-shadow: 0 2px 4px rgba(0,0,0,0.01);">
                        <div style="font-size: 11px; color: var(--texto-secundario); font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px;">Empresa</div>
                        <div style="font-size: 14px; color: var(--texto-principal); font-weight: 600; word-break: break-word;">{{ c.empresa|default:'Información no disponible' }}</div>
                    </div>
                </div>
            </div>
            </div> <!-- End main-tabs-wrapper -->
        </section>
    </main>'''

if old_end in content:
    content = content.replace(old_end, new_end, 1)
    print('Injected wrapper end')
else:
    print('Could not find wrapper end')

# Inject JS
old_js = '''        function cambiarTabPrincipal(tab) {'''
new_js = '''        let userClosedDatosAdicionales = false;

        function toggleDatosAdicionales() {
            const panel = document.getElementById('panel-datos-adicionales');
            const isVisible = panel.style.display !== 'none';
            if (isVisible) {
                panel.style.display = 'none';
                userClosedDatosAdicionales = true;
            } else {
                panel.style.display = 'flex';
                userClosedDatosAdicionales = false;
            }
        }

        function cerrarDatosAdicionalesManual() {
            document.getElementById('panel-datos-adicionales').style.display = 'none';
            userClosedDatosAdicionales = true;
        }

        function cambiarTabPrincipal(tab) {'''

if old_js in content:
    content = content.replace(old_js, new_js, 1)
    print('Injected JS')
else:
    print('Could not find cambiarTabPrincipal')

# Update cambiarTabPrincipal to auto-open in chat
old_tab_chat = '''            } else if (tab === 'chat') {
                if (btnChat) btnChat.classList.add('active');
                if (cntChat) cntChat.classList.add('active');
                // Re-inicializar scroll'''
new_tab_chat = '''            } else if (tab === 'chat') {
                if (btnChat) btnChat.classList.add('active');
                if (cntChat) cntChat.classList.add('active');
                
                // Forzar panel de datos abierto en chat
                const panelDatos = document.getElementById('panel-datos-adicionales');
                const btnCerrarDatos = document.getElementById('btn-cerrar-datos');
                if(panelDatos) {
                    panelDatos.style.display = 'flex';
                    if(btnCerrarDatos) btnCerrarDatos.style.display = 'none';
                }
                
                // Re-inicializar scroll'''

if old_tab_chat in content:
    content = content.replace(old_tab_chat, new_tab_chat, 1)
    print('Injected chat tab behavior')
else:
    print('Could not find chat tab behavior')

# Ensure hiding logic for other tabs
old_tab_desc = '''            if (tab === 'descripcion') {
                if (btnDesc) btnDesc.classList.add('active');
                if (cntDesc) cntDesc.classList.add('active');
            } else if (tab === 'actividades') {'''
new_tab_desc = '''            const panelDatosGlobal = document.getElementById('panel-datos-adicionales');
            const btnCerrarDatosGlobal = document.getElementById('btn-cerrar-datos');
            if (panelDatosGlobal && tab !== 'chat') {
                if(userClosedDatosAdicionales) {
                    panelDatosGlobal.style.display = 'none';
                }
                if(btnCerrarDatosGlobal) btnCerrarDatosGlobal.style.display = 'flex';
            }

            if (tab === 'descripcion') {
                if (btnDesc) btnDesc.classList.add('active');
                if (cntDesc) cntDesc.classList.add('active');
            } else if (tab === 'actividades') {'''

if old_tab_desc in content:
    content = content.replace(old_tab_desc, new_tab_desc, 1)
    print('Injected desc tab behavior')
else:
    print('Could not find desc tab behavior')

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)
