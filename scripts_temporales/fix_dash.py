import re

# Read current dashboard.html
with open('Pruebas/dashboard.html', 'r', encoding='utf-8') as f:
    curr_html = f.read()

# Read the stash file (which contains the user's beautiful design)
with open('mi_dashboard_stash.html', 'r', encoding='utf-16') as f:
    stash_html = f.read()

# 1. FIX THE CHART COLORS
curr_html = curr_html.replace("pri   : '#D32F2F'", "pri   : '#a82e2e'")
curr_html = curr_html.replace("blue  : '#4318FF'", "blue  : '#335d80'")
curr_html = curr_html.replace("bg    : '#F4F7FE'", "bg    : '#f8fafc'")
curr_html = curr_html.replace("red   : '#EF4444'", "red   : '#a82e2e'")

# 2. REPLACE SIDEBAR HTML
# Extract sidebar from stash
stash_sidebar_match = re.search(r'<aside class="barra-lateral">.*?</aside>', stash_html, re.DOTALL)
if stash_sidebar_match:
    stash_sidebar = stash_sidebar_match.group(0)
    # Jary's sidebar is <aside class="sidebar">...</aside>
    curr_html = re.sub(r'<aside class="sidebar">.*?</aside>', stash_sidebar, curr_html, flags=re.DOTALL)

# 3. REPLACE HEADER HTML
# Jary's header starts after <!-- ════════════ MAIN ════════════ -->
# <div class="wrapper">
# <!-- Header -->
# <div style="..."> ... </div>
# And ends before <!-- ── Dashboard Grid ── -->
stash_banner_match = re.search(r'(<div class="banner-inicio".*?)<div class="kpi-grid"', stash_html, re.DOTALL)
if stash_banner_match:
    stash_banner = stash_banner_match.group(1)
    # We replace from <!-- Header --> to just before <!-- ── Dashboard Grid ── -->
    curr_html = re.sub(r'<!-- Header -->.*?<!-- ── Dashboard Grid ── -->', stash_banner + '\n    <!-- ── Dashboard Grid ── -->', curr_html, flags=re.DOTALL)

# 4. ADD SIDEBAR AND BANNER CSS TO JARY'S STYLE
# Extract relevant CSS from stash
stash_style_match = re.search(r'<style>(.*?)</style>', stash_html, re.DOTALL)
if stash_style_match:
    stash_css = stash_style_match.group(1)
    # We just need to add the classes that Jary doesn't have, OR we can just inject the whole stash CSS at the END of Jary's style 
    # to override/add the barra-lateral and banner-inicio classes.
    # But wait, if we inject all stash CSS, it might break Jary's .card. 
    # Let's extract ONLY .barra-lateral, .banner-inicio, .nav-menu, etc.
    # Actually, it's safer to just inject the whole stash CSS EXCEPT the general body/root tags.
    css_to_add = re.sub(r':root\s*\{.*?\}', '', stash_css, flags=re.DOTALL)
    css_to_add = re.sub(r'\* \{.*?\}', '', css_to_add, flags=re.DOTALL)
    css_to_add = re.sub(r'body\s*\{.*?\}', '', css_to_add, flags=re.DOTALL)
    
    # Inject before </style>
    curr_html = curr_html.replace('</style>', css_to_add + '\n    </style>')

# Also fix the margin in .wrapper so it matches the new sidebar
curr_html = curr_html.replace('.wrapper{margin-left:90px', '.wrapper{margin-left:260px')
curr_html = curr_html.replace('width:calc(100% - 90px)', 'width:calc(100% - 260px)')

# Write back
with open('Pruebas/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(curr_html)

print("Done fixing dashboard.html!")
