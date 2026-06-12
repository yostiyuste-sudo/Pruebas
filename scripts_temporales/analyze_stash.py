import sys
import re

stash_html = open('mi_dashboard_stash.html', 'r', encoding='utf-16').read()

match = re.search(r'</aside>\s*(<div.*)', stash_html, re.DOTALL)
if match:
    print(match.group(1)[:2000])
else:
    print('Could not find content after aside')
