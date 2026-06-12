import os
import re

directory = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas'
files = [f for f in os.listdir(directory) if f.endswith('.html')]

# New palette
new_palette = "['#a82e2e', '#1a2232', '#64748b', '#e11d48', '#334155', '#7f1d1d']"
new_bg_color_5 = "backgroundColor: ['#a82e2e', '#1a2232', '#64748b', '#e11d48', '#334155']"
new_bg_color_3 = "backgroundColor: ['#a82e2e', '#1a2232', '#64748b']"
new_bg_color_2 = "backgroundColor: ['#a82e2e', '#1a2232']"

for f in files:
    path = os.path.join(directory, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content
    
    # 1. Replace the CONST COLORS array
    new_content = re.sub(
        r"const COLORS = \[.*?\];",
        f"const COLORS = {new_palette};",
        new_content
    )
    
    new_content = re.sub(
        r"const colors = \[.*?\];",
        f"const colors = {new_palette};",
        new_content
    )
    
    # 2. Replace backgroundColor arrays
    # Match any backgroundColor: [ ... ] and replace with appropriate size from palette
    def replacer(match):
        arr_str = match.group(1)
        # count how many elements
        elements = arr_str.split(',')
        n = len(elements)
        
        palette = ['#a82e2e', '#1a2232', '#64748b', '#e11d48', '#334155', '#7f1d1d', '#94a3b8', '#991b1b']
        
        # We don't want to replace backgroundColors in some specific non-chart places if they are single strings, 
        # but the regex specifically looks for arrays: backgroundColor: [ ... ]
        
        new_arr = ", ".join(f"'{palette[i % len(palette)]}'" for i in range(n))
        return f"backgroundColor: [{new_arr}]"
    
    new_content = re.sub(r"backgroundColor:\s*\[(.*?)\]", replacer, new_content)
    
    # 3. Handle backgroundColors = totalHours.map(...) where backgroundColors array is dynamically generated
    # If there are any backgroundColors arrays dynamically generated, we make sure they use red.
    # E.g. const backgroundColors = totalHours.map((val, idx) => { return ... });
    # The script uses the regex above for static arrays.
    
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')

print("Done.")
