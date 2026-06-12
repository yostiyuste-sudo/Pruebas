import io
with io.open(r"c:\Users\usuario\Documents\Pruebas\temp_old_index.html", "r", encoding="utf-16le") as f:
    text = f.read()
with io.open(r"c:\Users\usuario\Documents\Pruebas\temp_old_index_utf8.html", "w", encoding="utf-8") as f:
    f.write(text)
