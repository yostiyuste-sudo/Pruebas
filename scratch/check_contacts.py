import os
import sqlite3

db_path = 'db.sqlite3'
if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get all contacts and their phones
cursor.execute("SELECT id, nombre, apellido, celular, telefono FROM core_contacto;")
contacts = cursor.fetchall()

print("CONTACTS IN DATABASE:")
for c in contacts:
    print(f"ID: {c[0]} | Name: {c[1]} {c[2]} | Celular: '{c[3]}' | Telefono: '{c[4]}'")

conn.close()
