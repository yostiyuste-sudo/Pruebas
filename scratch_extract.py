import json

log_path = r"c:\Users\usuario\.gemini\antigravity-ide\brain\b13de9cb-4e0a-47a6-9bbe-b399216e678f\.system_generated\logs\transcript.jsonl"
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            if data.get("type") == "TOOL_RESPONSE" and "dashboard.html" in line:
                content = data.get("content", "")
                if "The following code has been modified" in content and "dashboard.html" in content:
                    print("Found dashboard.html view_file response")
                    with open(r"c:\Users\usuario\Documents\Pruebas\Pruebas\dashboard_history.txt", "w", encoding="utf-8") as out:
                        out.write(content)
                    break
        except Exception as e:
            pass
print("Done")
