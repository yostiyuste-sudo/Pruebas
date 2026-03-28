import re

fpath = r'c:\Users\paudi\OneDrive\Documentos\Pruebas\Pruebas\detalle_contacto.html'
with open(fpath, 'r', encoding='utf-8') as f:
    content = f.read()

EMAIL_UI_CSS = '''
        /* --- ESTILOS CORREO --- */
        .correos-container { padding: 40px; background: #fcfcfc; }
        .email-card { background: white; border: 1.5px solid #f1f5f9; border-radius: 16px; margin-bottom: 12px; transition: 0.2s; overflow: hidden; }
        .email-card:hover { border-color: #e2e8f0; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
        .email-card-header { padding: 15px 25px; display: flex; align-items: center; justify-content: space-between; cursor: pointer; background: #fff; }
        .email-subject-row { display: flex; align-items: center; gap: 12px; font-weight: 700; color: #334155; font-size: 14.5px; }
        .email-card-body { display: none; padding: 25px; background: #fafafa; border-top: 1.5px solid #f1f5f9; }
        .email-sender-info { display: flex; align-items: center; gap: 15px; margin-bottom: 20px; position: relative; }
        .email-avatar-v2 { width: 40px; height: 40px; border-radius: 50%; background: var(--rojo-primario); color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 15px; }
        .email-names { flex: 1; }
        .email-sender-name { font-weight: 800; color: #1e293b; font-size: 14px; }
        .email-to-list { font-size: 12px; color: #64748b; margin-top: 2px; }
        .email-status-badge { font-size: 11px; font-weight: 800; color: #10b981; display: flex; align-items: center; gap: 4px; margin-top: 4px; text-transform: uppercase; }
        .email-text-content { font-size: 14.5px; color: #334155; line-height: 1.7; white-space: pre-wrap; padding: 10px 5px; }
        .btn-star { background: none; border: none; font-size: 18px; color: #cbd5e0; cursor: pointer; transition: 0.2s; }
        .btn-star.active { color: #f59e0b; }
        .email-actions-inline { position: absolute; right: 0; top: 0; display: flex; gap: 8px; }
        .email-actions-inline button { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; padding: 5px; }
        .email-actions-inline button:hover { color: #ef4444; }
'''

# 1. Add Email CSS
if '.email-card' not in content:
    content = re.sub(r'</style>', f'{EMAIL_UI_CSS}\n    </style>', content)

# 2. Fix Logo to "D DYCO"
content = content.replace('<div class="logo-texto">CONSTRUCTORA</div>', '<div class="logo-texto">DYCO</div>')

with open(fpath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Email UI restored and logo updated to DYCO.")
