import sqlite3

#Conectar a SQLite (creael archivo si no existe)
conn = sqlite3.conect("pyme_san_ignacio.db")
cursor = conn.cursor()

# Crear tabla empleados
cursor.execute("""
CREATE TABLE IF NOT EXISTS empleados (
    legajo INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    puesto TEXT NOT NULL,
    area TEXT
)
""")

# Crear tabla horarios_empleados
cursor.execute("""
CREATE TABLE IF NOT EXISTS horarios_empleados (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    legajo_empleado INTEGER NOT NULL,
    hora_entrada TIME NOT NULL,
    hora_salida TIME NOT NULL,
    FOREIGN KEY (legajo_empleado) REFERENCES empleados(legajo)
)
""")

# Datos de empleados (legajo, nombre, puesto, area)
empleados = [
    (1, "Juan Pérez", "Ingeniero de alimentos", "Producción"),
    (2, "María López", "Técnico químico", "Calidad"),
    (3, "Lucas Fernandez", "Técnico químico", "Calidad"),
    (4, "Pedro Gómez", "Ingeniero de sistemas", "Sistemas"),
    (5, "Laura Torres", "Técnico en alimentos", "Producción"),
    (6, "Luis Martínez", "Limpieza", "Servicios Generales"),
    (7, "Sofía Fernández", "Operario de depósito", "Depósito"),
    (8, "Manuel Iglesias", "Técnico en alimentos", "Producción"),
    (9, "Maria Maio", "Operario de depósito", "Depósito"),
    (10, "Agustin Baez", "Encargado de inventario", "Depósito"),
    (11, "Lourdes Gonzalez", "Limpieza", "Servicios Generales"),
]

cursor.executemany("""
INSERT OR IGNORE INTO empleados (legajo, nombre, puesto, area)
VALUES (?, ?, ?, ?)
""", empleados)

# Horarios de empleados (legajo_empleado, hora_entrada, hora_salida)
horarios = [
    (1, "09:00", "18:00"),
    (2, "14:00", "22:00"),
    (3, "20:00", "04:00"),
    (4, "20:00", "04:00"),
    (5, "09:00", "18:00"),
    (6, "14:00", "22:00"),
    (7, "09:00", "18:00"),
    (8, "14:00", "22:00"),
    (9, "14:00", "22:00"),
    (10, "09:00", "18:00"),
    (11, "09:00", "18:00"),
]

cursor.executemany("""
INSERT INTO horarios_empleados (legajo_empleado, hora_entrada, hora_salida)
VALUES (?, ?, ?)
""", horarios)

# Guardar cambios y cerrar conexión
conn.commit()
conn.close()

print("Base de datos creada con empleados y horarios cargados ✅")