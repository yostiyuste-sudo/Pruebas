import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

def check_table(table):
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"\nColumns in {table}:")
        for col in columns:
            print(col)
    except Exception as e:
        print(f"Error checking {table}: {e}")

check_table('core_contacto')
check_table('core_interaccion')
check_table('core_compromiso')

conn.close()
