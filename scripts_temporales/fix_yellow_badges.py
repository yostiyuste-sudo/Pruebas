import os

directory = r'c:\Users\paudi\OneDrive\Desktop\Pruebas\Pruebas'
files = [f for f in os.listdir(directory) if f.endswith('.html')]

# We want to replace any yellow/orange colors with red
replacements = {
    '#fef3c7': '#ffe4e6',
    '#FEF3C7': '#ffe4e6',
    '#92400e': '#be123c',
    '#B45309': '#be123c',
    '#fef08a': '#ffe4e6',
    '#fef9c3': '#ffe4e6',
    '#ca8a04': '#be123c',
    '#d97706': '#be123c',
    '#b45309': '#be123c',
    # Replace orange background for specific badges if there are classes doing it:
    'bg-yellow-100': 'bg-rose-100',
    'bg-yellow-200': 'bg-rose-100',
    'text-yellow-600': 'text-rose-600',
    'text-yellow-700': 'text-rose-700',
    'text-yellow-800': 'text-rose-800',
    'border-yellow-200': 'border-rose-200',
    'border-yellow-300': 'border-rose-300',
}

for f in files:
    path = os.path.join(directory, f)
    with open(path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    new_content = content
    for old, new in replacements.items():
        new_content = new_content.replace(old, new)
        
    if new_content != content:
        with open(path, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print(f'Updated {f}')

print("Additional yellow removal done.")
