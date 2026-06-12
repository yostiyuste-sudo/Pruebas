import re

with open('Pruebas/dashboard.html', 'r', encoding='utf-8') as f:
    jary = f.read()

with open('mi_dashboard_stash.html', 'r', encoding='utf-16') as f:
    stash = f.read()

# 1. EXTRACT SIDEBAR HTML FROM STASH
sidebar_html = ""
m_side = re.search(r'<aside class="barra-lateral">.*?</aside>', stash, re.DOTALL)
if m_side:
    sidebar_html = m_side.group(0)

# 2. EXTRACT HEADER/CAROUSEL HTML FROM STASH
header_html = ""
m_head = re.search(r'<header.*?</header>', stash, re.DOTALL)
if m_head:
    header_html = m_head.group(0)

# 3. EXTRACT ALL CSS FROM STASH
stash_css = ""
m_css = re.search(r'<style>(.*?)</style>', stash, re.DOTALL)
if m_css:
    stash_css = m_css.group(1)
    
# Clean stash CSS to not break Jary's body
stash_css_clean = re.sub(r':root\s*\{.*?\}', '', stash_css, flags=re.DOTALL)
stash_css_clean = re.sub(r'\*\s*\{.*?\}', '', stash_css_clean, flags=re.DOTALL)
stash_css_clean = re.sub(r'body\s*\{.*?\}', '', stash_css_clean, flags=re.DOTALL)

# 4. MODIFY JARY'S HTML
# Replace the sidebar
jary = re.sub(r'<!-- ════════════ SIDEBAR ════════════ -->.*?</aside>', '<!-- SIDEBAR -->\n' + sidebar_html, jary, flags=re.DOTALL)

# Replace the Header banner
jary = re.sub(r'<!-- Header -->.*?</div>\s*</div>\s*(?=<!-- ── Dashboard Grid ── -->)', header_html + '\n', jary, flags=re.DOTALL)

# Inject stash CSS into Jary's style block at the end (so it overrides if necessary, or just adds the classes)
jary = jary.replace('</style>', stash_css_clean + '\n</style>')

# Fix Jary's .wrapper margin
jary = re.sub(r'\.wrapper\{margin-left:90px;flex:1;padding:40px;transition:var\(--ease\);width:calc\(100% - 90px\)\}',
              '.wrapper{margin-left:90px;flex:1;padding:40px;transition:var(--ease);width:calc(100% - 90px)} /* Stash sidebar overrides this later if hovered */', jary)

# Fix JS Chart Colors!
# Change generic Chart.js background arrays to only use the user's 2 colors + some dark theme fallbacks
jary = re.sub(r'backgroundColor:\s*\[C\.pri,\s*C\.amber,\s*C\.blue,\s*C\.cyan,\s*C\.green\]',
              "backgroundColor: ['#a82e2e', '#335d80', '#1a2232', '#64748b', '#01B574']", jary)

jary = re.sub(r'backgroundColor:\s*\[C\.blue,\s*C\.cyan\]',
              "backgroundColor: ['#a82e2e', '#335d80']", jary)

jary = re.sub(r'backgroundColor:\s*\[C\.green,\s*C\.gray\]',
              "backgroundColor: ['#335d80', '#1a2232']", jary)

jary = re.sub(r'backgroundColor:\s*\[C\.pri,\s*C\.blue\]',
              "backgroundColor: ['#a82e2e', '#335d80']", jary)

# Change bar chart color
jary = re.sub(r"const bars = data\.map\(\(\) => 'rgba\(67,24,255,\.72\)'\);",
              "const bars = data.map(() => '#335d80');", jary)
jary = re.sub(r"const bHov = data\.map\(\(\) => 'rgba\(67,24,255,\.9\)'\);",
              "const bHov = data.map(() => '#a82e2e');", jary)

# Write back
with open('Pruebas/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(jary)
print('Merged successfully')
