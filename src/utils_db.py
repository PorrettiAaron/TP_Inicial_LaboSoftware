import sqlite3
from contextlib import contextmanager
from datetime import datetime

PYME_DB = "pyme_san_ignacio.db"

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

@contextmanager
def get_connection(db_path: str = PYME_DB):
    conn = sqlite3.connect(db_path)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def create_database_pyme(cursor):
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS empleados ('
        ' legajo INTEGER PRIMARY KEY,'
        ' nombre TEXT NOT NULL,'
        ' puesto TEXT NOT NULL,'
        ' area TEXT)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS horarios_empleados ('
        ' id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' legajo_empleado INTEGER NOT NULL,'
        ' hora_entrada TIME NOT NULL,'
        ' hora_salida TIME NOT NULL,'
        ' FOREIGN KEY (legajo_empleado) REFERENCES empleados(legajo))'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS asistencia_empleado ('
        ' legajo_empleado INTEGER NOT NULL,'
        ' entrada TIMESTAMP NOT NULL,'
        ' salida TIMESTAMP,'
        ' FOREIGN KEY (legajo_empleado) REFERENCES empleados(legajo),'
        ' PRIMARY KEY (legajo_empleado, entrada))'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS rostros ('
        ' archivo TEXT PRIMARY KEY,'
        ' legajo INTEGER NOT NULL,'
        ' FOREIGN KEY (legajo) REFERENCES empleados(legajo))'
    )

def manual_load_empleados(cursor, empleados_list):
    cursor.executemany(
        'INSERT OR IGNORE INTO empleados (legajo, nombre, puesto, area) VALUES (?, ?, ?, ?)',
        empleados_list,
    )

def manual_load_horarios_empleados(cursor, horarios_list):
    cursor.executemany(
        'INSERT INTO horarios_empleados (legajo_empleado, hora_entrada, hora_salida) VALUES (?, ?, ?)',
        horarios_list,
    )

def ensure_db_seeded(db_path: str = PYME_DB):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        create_database_pyme(cur)
        manual_load_empleados(cur, empleados)
        manual_load_horarios_empleados(cur, horarios)

def empleado_detected(cursor, legajo: int):
    cursor.execute(
        'SELECT entrada, salida FROM asistencia_empleado WHERE legajo_empleado = ? ORDER BY entrada DESC LIMIT 1',
        (legajo,),
    )
    row = cursor.fetchone()
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if row is None or row[1] is not None:
        cursor.execute(
            'INSERT INTO asistencia_empleado (legajo_empleado, entrada, salida) VALUES (?, ?, NULL)',
            (legajo, now),
        )
        return {'status': 'entrada', 'legajo': legajo, 'timestamp': now}
    else:
        last_entrada = row[0]
        cursor.execute(
            'UPDATE asistencia_empleado SET salida = ? WHERE legajo_empleado = ? AND entrada = ?',
            (now, legajo, last_entrada),
        )
        return {'status': 'salida', 'legajo': legajo, 'timestamp': now, 'entrada': last_entrada}

def add_face_mapping(cursor, archivo: str, legajo: int):
    cursor.execute('INSERT OR REPLACE INTO rostros (archivo, legajo) VALUES (?, ?)', (archivo, legajo))

def set_face_mapping_bulk(cursor, pairs):
    cursor.executemany('INSERT OR REPLACE INTO rostros (archivo, legajo) VALUES (?, ?)', pairs)

def get_legajo_for_filename(cursor, archivo: str):
    cursor.execute('SELECT legajo FROM rostros WHERE archivo = ?', (archivo,))
    row = cursor.fetchone()
    return row[0] if row else None

def main():
    ensure_db_seeded()
    print('Base de datos lista ✅')

if __name__ == '__main__':
    main()
