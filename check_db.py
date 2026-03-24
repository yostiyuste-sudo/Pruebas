import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

try:
    cursor.execute("PRAGMA table_info(core_usuario)")
    columns = cursor.fetchall()
    print("Columns in core_usuario:")
    for col in columns:
        print(col)
except Exception as e:
    print(f"Error: {e}")

conn.close()
