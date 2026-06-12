import re

try:
    with open('mi_dashboard_stash.html', 'r', encoding='utf-16') as f:
        stash_html = f.read()
except Exception as e:
    print("Error reading stash:", e)
    exit(1)

with open('Pruebas/dashboard.html', 'r', encoding='utf-8') as f:
    curr_html = f.read()

# Extract CSS from stash
style_match = re.search(r'<style>(.*?)</style>', stash_html, re.DOTALL)
if style_match:
    stash_style = style_match.group(0)
    print("Extracted style from stash")
else:
    print("No style found in stash")

# Extract sidebar from stash
sidebar_match = re.search(r'<aside.*?</aside>', stash_html, re.DOTALL)
if sidebar_match:
    stash_sidebar = sidebar_match.group(0)
    print("Extracted sidebar from stash")
else:
    print("No sidebar found in stash")

# Extract the banner / carousel from stash
# We look for something before the main grid
main_match = re.search(r'(<div class="main-content".*?)(<div class="metrics-grid"|<div class="kpi-grid"|<div class="grid")', stash_html, re.DOTALL)
if main_match:
    banner_area = main_match.group(1)
    print("Extracted banner area")
else:
    # Just grab whatever is after <div class="main-content"> up to the first metrics or grid
    banner_match = re.search(r'(<div class="banner.*?</style>.*?</div>)', stash_html, re.DOTALL)
    if banner_match:
        banner_area = banner_match.group(1)
    else:
        print("Could not extract banner area")
        banner_area = ""

# Now replace in curr_html
# Replace <style>
curr_html = re.sub(r'<style>.*?</style>', stash_style, curr_html, flags=re.DOTALL)

# Replace sidebar
curr_html = re.sub(r'<aside.*?</aside>', stash_sidebar, curr_html, flags=re.DOTALL)

# Replace the header banner in curr_html
# The current one has a div with background: #fff; border-radius: 16px;
# Let's replace the whole <!-- Header --> block
curr_html = re.sub(r'<!-- Header -->.*?</div>\s*</div>', banner_area, curr_html, flags=re.DOTALL)

# We need to ensure the Javascript colors are updated:
# const C = { green : '#01B574', amber : '#F59E0B', red : '#EF4444', pri : '#D32F2F', blue : '#4318FF', cyan : '#00C6E0', gray : '#CBD5E1', bg : '#F4F7FE' };
# The user wants their old colors. The old colors are:
# pri: '#a82e2e', blue: '#335d80', bg: '#f8fafc', red: '#e63946'
curr_html = re.sub(r'pri\s*:\s*\'[^\']+\'', "pri   : '#a82e2e'", curr_html)
curr_html = re.sub(r'blue\s*:\s*\'[^\']+\'', "blue  : '#335d80'", curr_html)
curr_html = re.sub(r'bg\s*:\s*\'[^\']+\'', "bg    : '#f8fafc'", curr_html)

with open('Pruebas/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(curr_html)

print("Successfully merged!")
