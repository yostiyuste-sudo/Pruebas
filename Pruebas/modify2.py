import sys
import re

path = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas\detalle_contacto.html'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Replace the button
btn_old_pattern = r'<button id="btn-toggle-datos" onclick="toggleDatosAdicionales\(\)" style="background: var\(--rojo-primario\); color: white; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; transition: 0\.2s; box-shadow: 0 4px 10px rgba\(183, 28, 28, 0\.2\);">Datos adicionales</button>'
btn_new = '''<button id="btn-toggle-datos" title="Información del cliente" onclick="toggleDatosAdicionales()" style="background: white; border: 1.5px solid #e2e8f0; color: #64748b; padding: 0; border-radius: 50%; width: 38px; height: 38px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: 0.2s; box-shadow: 0 2px 5px rgba(0,0,0,0.02);" onmouseover="this.style.borderColor='#a82e2e'; this.style.color='#a82e2e';" onmouseout="this.style.borderColor='#e2e8f0'; this.style.color='#64748b';">
                        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1 0-5H20"></path>
                        </svg>
                    </button>'''

content = re.sub(btn_old_pattern, btn_new, content)

# 2. Replace the panel
panel_old_start = '<!-- PANEL DATOS ADICIONALES -->'
panel_old_end = '</div> <!-- End main-tabs-wrapper -->'

start_idx = content.find(panel_old_start)
if start_idx != -1:
    end_idx = content.find(panel_old_end, start_idx)
    if end_idx != -1:
        # Construct new panel
        new_panel = '''<!-- PANEL DATOS ADICIONALES -->
            <div id="panel-datos-adicionales" style="width: 380px; background: white; border-left: 1px solid var(--gris-borde); display: none; flex-direction: column; overflow-y: auto; transition: width 0.3s ease; box-shadow: -4px 0 15px rgba(0,0,0,0.02);">
                <div style="padding: 24px 24px 16px; display: flex; justify-content: space-between; align-items: center; background: white; position: sticky; top: 0; z-index: 10;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="16" x2="12" y2="12"></line>
                            <line x1="12" y1="8" x2="12.01" y2="8"></line>
                        </svg>
                        <h3 style="font-size: 16px; font-weight: 800; color: #0f172a; margin: 0;">Información del Cliente</h3>
                    </div>
                    <button onclick="cerrarDatosAdicionalesManual()" id="btn-cerrar-datos" style="background: none; border: none; cursor: pointer; color: #94a3b8; font-size: 22px; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: 0.2s;" onmouseover="this.style.background='#f1f5f9'; this.style.color='#ef4444';" onmouseout="this.style.background='none'; this.style.color='#94a3b8';">&times;</button>
                </div>
                
                <div style="padding: 0 24px 20px;">
                    <h2 style="font-size: 18px; font-weight: 800; color: #0f172a; margin: 0;">{% if c.nombre %}{{ c.nombre }} {{ c.apellido }}{% else %}{{ c.razon_social }}{% endif %}</h2>
                </div>

                <div style="padding: 0 24px 24px; display: flex; flex-direction: column; gap: 16px;">
                    <!-- Card Proyecto -->
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.01);">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#a82e2e" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
                                <polyline points="9 22 9 12 15 12 15 22"></polyline>
                            </svg>
                            <div style="font-size: 11px; color: #a82e2e; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Información del Proyecto</div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                            <div>
                                <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Tipo</div>
                                <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.tipo_proyecto|default:'-' }}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Conjunto</div>
                                <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.conjunto|default:'-' }}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Torre</div>
                                <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.torre|default:'-' }}</div>
                            </div>
                            <div>
                                <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Apto / Motivo</div>
                                <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.apto|default:'-' }} / {{ c.motivo|default:'-' }}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Card Personal y Laboral -->
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.01);">
                        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                                <circle cx="12" cy="7" r="4"></circle>
                            </svg>
                            <div style="font-size: 11px; color: #3b82f6; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;">Personal y Laboral</div>
                        </div>
                        <div>
                            <div style="margin-bottom: 16px;">
                                <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Ocupación / Cargo</div>
                                <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.ocupacion|default:c.cargo|default:'-' }}</div>
                            </div>
                            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                                <div>
                                    <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Fecha de Nacimiento</div>
                                    <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.fecha_nacimiento|default:'-' }}</div>
                                </div>
                                <div>
                                    <div style="font-size: 12px; color: #64748b; font-weight: 600; margin-bottom: 4px;">Edad</div>
                                    <div style="font-size: 14px; color: #0f172a; font-weight: 700; word-break: break-word;">{{ c.edad|default:'-' }}</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            '''
        
        content = content[:start_idx] + new_panel + content[end_idx:]

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Modification complete.")
