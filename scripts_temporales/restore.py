import json
import os

log_path = r"C:\Users\Jary\.gemini\antigravity\brain\c0ea56e9-ad9f-41f4-94d4-b6dd86c78972\.system_generated\logs\transcript.jsonl"
out_path = r"c:\Users\Jary\OneDrive\Documentos\Pruebas\Pruebas\detalle_contacto_recovered.html"

print("Searching for the premium version of detalle_contacto.html in transcript.jsonl...")
best_content = None
max_len = 0

with open(log_path, 'r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        try:
            data = json.loads(line)
            tool_calls = data.get('tool_calls', [])
            for tc in tool_calls:
                func = tc.get('function', {})
                args = func.get('arguments', {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except:
                        pass
                if not isinstance(args, dict):
                    continue
                
                target = args.get('TargetFile', '')
                if 'detalle_contacto.html' in target:
                    content = args.get('CodeContent', '') or args.get('ReplacementContent', '')
                    if content and len(content) > max_len:
                        max_len = len(content)
                        best_content = content
                        print(f"Line {line_num}: found content with length {len(content)}")
        except Exception as e:
            pass

if best_content:
    with open(out_path, 'w', encoding='utf-8') as f_out:
        f_out.write(best_content)
    print(f"Successfully wrote recovered content ({len(best_content)} chars) to {out_path}")
else:
    print("Could not find any content in transcript.jsonl.")
