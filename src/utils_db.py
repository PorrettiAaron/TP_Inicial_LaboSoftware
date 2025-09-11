import sqlite3
import logging
from contextlib import contextmanager
from datetime import datetime

PYME_DB = "./pyme_san_ignacio.db"
PYME_EMPLOYEES_IMAGES = "./db_images/"

#Coniguración de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

empleados = [
    (100, "Matías Stricker", "Ingeniero en sistemas", "Sistemas"),
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

productos_finales = [
    ("P-001", "Dulce de leche Clásico", "Pote 400gr", 2800, 1900, 750000, 500000),
    ("P-002", "Dulce de leche Clásico", "Pote 250gr", 2000, 1200, 300000, 200000),
    ("P-003", "Dulce de leche Clásico", "Pote 1kg", 4000, 2500, 250000, 170000),
    ("P-004", "Dulce de leche Repostero", "Pote 1kg", 6500, 4200, 300000, 220000),
    ("P-005", "Dulce de leche Repostero", "Pote 400gr", 3200, 2300, 400000, 300000),
    ("P-006", "Dulce de leche Repostero", "Pote 250gr", 2700, 1700, 250000, 197000),
    ("P-007", "Dulce de leche Light", "Pote 400gr", 3500, 2200, 150000, 95000),
    ("P-008", "Dulce de Leche vegano", "Pote 250gr", 2900, 1900, 200000, 145000),
]

insumos = [
    ("M-001", "Leche entera", "Cooperativa Tamberos", 1000, "Litro"),
    ("M-002", "Azúcar", "Azucarera Norte", 800, "Kg"),
    ("M-003", "Esencia de vainilla", "Sabores SRL", 600, "Litro"),
    ("M-004", "Bicarbonato", "Insumos Alimenticios SA", 700, "Kg"),
    ("M-005", "Glucosa (jarabe)", "Insumos Dulceros SRL", 600, "Kg"),
    ("M-006", "Leche de almendras", "Cooperativa Tamberos", 1500, "Litro"),
]

productos_por_kg = [
    ("Leche", "8.5 litros", "Dulce de leche tradicional"),
    ("Azucar", "2 kg", "Dulce de leche tradicional"),
    ("Vainilla", "5 ml", "Dulce de leche tradicional"),
    ("Bicarbonato de Sodio", "1.5 gr", "Dulce de leche tradicional"),
    ("Glucosa", "100 gr", "Dulce de leche tradicional"),
    ("Leche de almendras", "0 gr", "Dulce de leche tradicional"),
    ("Leche", "10 litros", "Dulce de leche repostero"),
    ("Azucar", "3 kg", "Dulce de leche repostero"),
    ("Vainilla", "7 ml", "Dulce de leche repostero"),
    ("Bicarbonato de Sodio", "2 gr", "Dulce de leche repostero"),
    ("Glucosa", "150 gr", "Dulce de leche repostero"),
    ("Leche de almendras", "0 gr", "Dulce de leche repostero"),
    ("Leche", "0 litros", "Dulce de leche vegano"),
    ("Azucar", "1.5 kg", "Dulce de leche vegano"),
    ("Vainilla", "2 ml", "Dulce de leche vegano"),
    ("Bicarbonato de Sodio", "0.5 gr", "Dulce de leche vegano"),
    ("Glucosa", "70 gr", "Dulce de leche vegano"),
    ("Leche de almendras", "7 litros", "Dulce de leche vegano"),
]

tiempos_de_produccion = [
    ("Recepción de leche", 0.5, 1000, "Dulce de leche clásico"),
    ("Recepción de leche", 0.6, 1000, "Dulce de leche repostero"),
    ("Recepción de leche", 0.7, 1000, "Dulce de leche light"),
    ("Recepción de leche", 0.8, 1000, "Dulce de leche vegano"),
    ("Estandarización y pasteurización", 1.5, 1000, "Dulce de leche clásico"),
    ("Estandarización y pasteurización", 2.5, 1000, "Dulce de leche repostero"),
    ("Estandarización y pasteurización", 3.5, 1000, "Dulce de leche light"),
    ("Estandarización y pasteurización", 4.5, 1000, "Dulce de leche vegano"),
    ("Concentración (evaporación)", 8, 1000, "Dulce de leche clásico"),
    ("Adición de azúcar y bicarbonato", 0.5, 1000, "Dulce de leche clásico"),
    ("Cocción y desarrollo del color/sabor", 4, 1000, "Dulce de leche clásico"),
    ("Enfriamiento", 2, 1000, "Dulce de leche clásico"),
    ("Envasado", 3, 1000, "Dulce de leche clásico"),
    ("Envasado", 3, 1000, "Dulce de leche repostero"),
    ("Envasado", 3, 1000, "Dulce de leche light"),
    ("Envasado", 3, 1000, "Dulce de leche vegano"),
    ("Almacenamiento", 2, 1000, "Dulce de leche clásico"),
    ("Almacenamiento", 2, 1000, "Dulce de leche repostero"),
    ("Almacenamiento", 2, 1000, "Dulce de leche light"),
    ("Almacenamiento", 2, 1000, "Dulce de leche vegano"),
    ("Concentración (evaporación)", 10, 1000, "Dulce de leche repostero"),
    ("Adición de azúcar y bicarbonato", 1, 1000, "Dulce de leche repostero"),
    ("Cocción y desarrollo del color/sabor", 6, 1000, "Dulce de leche repostero"),
    ("Enfriamiento", 2.5, 1000, "Dulce de leche repostero"),
    ("Concentración (evaporación)", 6.5, 1000, "Dulce de leche light"),
    ("Adición de azúcar y bicarbonato", 0.25, 1000, "Dulce de leche light"),
    ("Cocción y desarrollo del color/sabor", 3.5, 1000, "Dulce de leche light"),
    ("Enfriamiento", 2, 1000, "Dulce de leche light"),
    ("Concentración (evaporación)", 6, 1000, "Dulce de leche vegano"),
    ("Adición de azúcar y bicarbonato", 0.15, 1000, "Dulce de leche vegano"),
    ("Cocción y desarrollo del color/sabor", 3, 1000, "Dulce de leche vegano"),
    ("Enfriamiento", 3, 1000, "Dulce de leche vegano"),
]

tiempos_de_produccion = [
    ("Recepción de leche", 0.5, 1000, "Dulce de leche clásico"),
    ("Recepción de leche", 0.6, 1000, "Dulce de leche repostero"),
    ("Recepción de leche", 0.7, 1000, "Dulce de leche light"),
    ("Recepción de leche", 0.8, 1000, "Dulce de leche vegano"),
    ("Estandarización y pasteurización", 1.5, 1000, "Dulce de leche clásico"),
    ("Estandarización y pasteurización", 2.5, 1000, "Dulce de leche repostero"),
    ("Estandarización y pasteurización", 3.5, 1000, "Dulce de leche light"),
    ("Estandarización y pasteurización", 4.5, 1000, "Dulce de leche vegano"),
    ("Concentración (evaporación)", 8, 1000, "Dulce de leche clásico"),
    ("Adición de azúcar y bicarbonato", 0.5, 1000, "Dulce de leche clásico"),
    ("Cocción y desarrollo del color/sabor", 4, 1000, "Dulce de leche clásico"),
    ("Enfriamiento", 2, 1000, "Dulce de leche clásico"),
    ("Envasado", 3, 1000, "Dulce de leche clásico"),
    ("Envasado", 3, 1000, "Dulce de leche repostero"),
    ("Envasado", 3, 1000, "Dulce de leche light"),
    ("Envasado", 3, 1000, "Dulce de leche vegano"),
    ("Almacenamiento", 2, 1000, "Dulce de leche clásico"),
    ("Almacenamiento", 2, 1000, "Dulce de leche repostero"),
    ("Almacenamiento", 2, 1000, "Dulce de leche light"),
    ("Almacenamiento", 2, 1000, "Dulce de leche vegano"),
    ("Concentración (evaporación)", 10, 1000, "Dulce de leche repostero"),
    ("Adición de azúcar y bicarbonato", 1, 1000, "Dulce de leche repostero"),
    ("Cocción y desarrollo del color/sabor", 6, 1000, "Dulce de leche repostero"),
    ("Enfriamiento", 2.5, 1000, "Dulce de leche repostero"),
    ("Concentración (evaporación)", 6.5, 1000, "Dulce de leche light"),
    ("Adición de azúcar y bicarbonato", 0.25, 1000, "Dulce de leche light"),
    ("Cocción y desarrollo del color/sabor", 3.5, 1000, "Dulce de leche light"),
    ("Enfriamiento", 2, 1000, "Dulce de leche light"),
    ("Concentración (evaporación)", 6, 1000, "Dulce de leche vegano"),
    ("Adición de azúcar y bicarbonato", 0.15, 1000, "Dulce de leche vegano"),
    ("Cocción y desarrollo del color/sabor", 3, 1000, "Dulce de leche vegano"),
    ("Enfriamiento", 3, 1000, "Dulce de leche vegano"),
]

desperdicio_por_producto = [
    (344.2, 100, 244.2, 70.80, 95, 5, "Dulce de leche clásico"),
    (360, 120, 240, 66.70, 93, 7, "Dulce de leche repostero"),
    (320, 80, 240, 75.00, 90, 10, "Dulce de leche light"),
    (300, 90, 210, 70.00, 85, 15, "Dulce de leche vegano"),
]

stock_materia_prima = [
    ("M-001", "Leche", 567863),
    ("M-002", "Azucar", 453215),
    ("M-003", "Vainilla", 205698),
    ("M-004", "Bicarbonato de Sodio", 165169),
    ("M-005", "Glucosa", 156598),
    ("M-006", "Leche de almendras", 100000),
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
        ' id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' legajo_empleado INTEGER NOT NULL,'
        ' entrada TIMESTAMP NOT NULL,'
        ' salida TIMESTAMP,'
        ' FOREIGN KEY (legajo_empleado) REFERENCES empleados(legajo),'
        ' UNIQUE (legajo_empleado, entrada))'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS rostros ('
        ' archivo TEXT PRIMARY KEY,'
        ' legajo INTEGER NOT NULL,'
        ' FOREIGN KEY (legajo) REFERENCES empleados(legajo))'
    )
    # 🔹 Nuevo: índice para mejorar consultas por legajo
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_asistencia_legajo ON asistencia_empleado(legajo_empleado)')
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS productos_finales ('
        ' codigo TEXT PRIMARY KEY,'
        ' producto TEXT NOT NULL,'
        ' presentacion TEXT NOT NULL,'
        ' precio_venta REAL NOT NULL,'
        ' costo_unitario REAL NOT NULL,'
        ' stock INTEGER NOT NULL,'
        ' estimado_ventas_mensuales INTEGER NOT NULL)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS insumos ('
        ' codigo TEXT PRIMARY KEY,'
        ' insumo TEXT NOT NULL,'
        ' proveedor TEXT NOT NULL,'
        ' costo_unitario REAL NOT NULL,'
        ' unidad TEXT NOT NULL)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS productos_por_kg ('
        ' id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' insumo TEXT NOT NULL,'
        ' cantidad TEXT NOT NULL,'
        ' producto_final TEXT NOT NULL)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS tiempos_de_produccion ('
        ' id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' procedimiento TEXT NOT NULL,'
        ' tiempo_estimado REAL NOT NULL,'
        ' cantidad_gr REAL NOT NULL,'
        ' producto TEXT NOT NULL)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS desperdicio_por_producto ('
        ' id INTEGER PRIMARY KEY AUTOINCREMENT,'
        ' total_inicial_kg REAL NOT NULL,'
        ' producto_final_obtenido_kg REAL NOT NULL,'
        ' desperdicio_kg REAL NOT NULL,'
        ' desperdicio_pct REAL NOT NULL,'
        ' desperdicio_reutilizable_pct REAL NOT NULL,'
        ' desperdicio_real_pct REAL NOT NULL,'
        ' producto TEXT NOT NULL)'
    )
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS stock_materia_prima ('
        ' codigo TEXT PRIMARY KEY,'
        ' nombre TEXT NOT NULL,'
        ' stock INTEGER NOT NULL)'
    )

def manual_load_empleados(cursor, empleados_list):
    cursor.executemany(
        'INSERT OR IGNORE INTO empleados (legajo, nombre, puesto, area) VALUES (?, ?, ?, ?)',
        empleados_list,
    )

def manual_load_horarios_empleados(cursor, horarios_list):
    cursor.executemany(
        'INSERT OR IGNORE INTO horarios_empleados (legajo_empleado, hora_entrada, hora_salida) VALUES (?, ?, ?)',
        horarios_list,
    )

def manual_load_productos_finales(cursor, productos_list):
    cursor.executemany(
        'INSERT OR IGNORE INTO productos_finales (codigo, producto, presentacion, precio_venta, costo_unitario, stock, estimado_ventas_mensuales) VALUES (?, ?, ?, ?, ?, ?, ?)',
        productos_list,
    )

def manual_load_insumos(cursor, insumos_list):
    cursor.executemany(
        'INSERT OR IGNORE INTO insumos (codigo, insumo, proveedor, costo_unitario, unidad) VALUES (?, ?, ?, ?, ?)',
        insumos_list,
    )

def manual_load_productos_por_kg(cursor, productos_kg_list):
    cursor.executemany(
        'INSERT INTO productos_por_kg (insumo, cantidad, producto_final) VALUES (?, ?, ?)',
        productos_kg_list,
    )

def manual_load_tiempos_produccion(cursor, tiempos_list):
    cursor.executemany(
        'INSERT INTO tiempos_de_produccion (procedimiento, tiempo_estimado, cantidad_gr, producto) VALUES (?, ?, ?, ?)',
        tiempos_list,
    )

def manual_load_desperdicio(cursor, desperdicio_list):
    cursor.executemany(
        'INSERT INTO desperdicio_por_producto (total_inicial_kg, producto_final_obtenido_kg, desperdicio_kg, desperdicio_pct, desperdicio_reutilizable_pct, desperdicio_real_pct, producto) VALUES (?, ?, ?, ?, ?, ?, ?)',
        desperdicio_list,
    )

def manual_load_stock_materia_prima(cursor, stock_list):
    cursor.executemany(
        'INSERT OR REPLACE INTO stock_materia_prima (codigo, nombre, stock) VALUES (?, ?, ?)',
        stock_list,
    )

def ensure_db_seeded(db_path: str = PYME_DB):
    with get_connection(db_path) as conn:
        cur = conn.cursor()
        create_database_pyme(cur)
        manual_load_empleados(cur, empleados)
        manual_load_horarios_empleados(cur, horarios)
        manual_load_productos_finales(cur, productos_finales)
        manual_load_insumos(cur, insumos)
        manual_load_productos_por_kg(cur, productos_por_kg)
        manual_load_tiempos_produccion(cur, tiempos_de_produccion)
        manual_load_desperdicio(cur, desperdicio_por_producto)
        manual_load_stock_materia_prima(cur, stock_materia_prima)

def get_timestamp_from_posix_version(posix_timestamp, _format="%Y-%m-%d %H:%M:%S"):
    return datetime.fromtimestamp(posix_timestamp).strftime(_format)

def report_empleado_entrada(cursor, legajo: int, timestamp):
    cursor.execute("INSERT INTO asistencia_empleado (legajo_empleado, entrada, salida) VALUES (?,?,NULL)", (legajo, timestamp))

def report_empleado_salida(cursor, legajo: int, timestamp, entrada=None):
    if entrada is None:
        cursor.execute("SELECT entrada FROM asistencia_empleado WHERE legajo_empleado = ? ORDER BY entrada DESC LIMIT 1")
        entrada = cursor.fetchone()
        if not row:
            logging.warning(f"No se encontró entrada previa para el empleado con legajo {legajo_empleado}")
            return
        entrada = row[0]
    cursor.execute("UPDATE asistencia_empleado SET salida = ? WHERE legajo_empleado = ? AND entrada = ?",(timestamp, legajo, entrada))

def get_last_assistance_empleado(cursor, legajo):
    cursor.execute("SELECT entrada, salida FROM asistencia_empleado WHERE legajo_empleado = ? ORDER BY entrada DESC LIMIT 1", (legajo,))
    row = cursor.fetchone()
    if row is None:
        return  None, None
    return row

def empleado_detected(cursor, legajo: int, timestamp: float):
    timestamp = get_timestamp_from_posix_version(timestamp)
    entrada, salida = get_last_assistance_empleado(cursor, legajo)
    if entrada is None or salida is not None: # Registar nueva entrada
        report_empleado_entrada(cursor, legajo, timestamp)
        logging.info("Registrada entrada de empleado")
    else: # Registar nueva salida
        report_empleado_salida(cursor, legajo, timestamp, entrada)
        logging.info("Registrada salida de empleado")

def add_face_mapping(cursor, archivo: str, legajo: int):
    cursor.execute('INSERT OR REPLACE INTO rostros (archivo, legajo) VALUES (?, ?)', (archivo, legajo))

def set_face_mapping_bulk(cursor, pairs):
    cursor.executemany('INSERT OR REPLACE INTO rostros (archivo, legajo) VALUES (?, ?)', pairs)

def get_legajo_for_filename(cursor, archivo: str):
    cursor.execute('SELECT legajo FROM rostros WHERE archivo = ?', (archivo,))
    row = cursor.fetchone()
    return row[0] if row else None

def get_asistencia_por_dia(cursor, fecha: str):
    cursor.execute(
        "SELECT legajo_empleado, entrada, salida FROM asistencia_empleado "
        "WHERE DATE(entrada) = ? ORDER BY entrada", (fecha,)
    )
    return cursor.fetchall()

def get_empleados_por_area(cursor, area: str):
    cursor.execute("SELECT legajo, nombre, puesto FROM empleados WHERE area = ?", (area,))
    return cursor.fetchall()

def get_productos_finales(cursor):
    cursor.execute("SELECT codigo, producto, presentacion, precio_venta, costo_unitario, stock, estimado_ventas_mensuales FROM productos_finales")
    return cursor.fetchall()

def get_insumos(cursor):
    cursor.execute("SELECT codigo, insumo, proveedor, costo_unitario, unidad FROM insumos")
    return cursor.fetchall()

def get_productos_por_kg(cursor):
    cursor.execute("SELECT insumo, cantidad, producto_final FROM productos_por_kg")
    return cursor.fetchall()

def get_tiempos_produccion(cursor):
    cursor.execute("SELECT procedimiento, tiempo_estimado, cantidad_gr, producto FROM tiempos_de_produccion")
    return cursor.fetchall()

def get_desperdicio(cursor):
    cursor.execute(
        "SELECT total_inicial_kg, producto_final_obtenido_kg, desperdicio_kg, desperdicio_pct, desperdicio_reutilizable_pct, desperdicio_real_pct, producto FROM desperdicio_por_producto"
    )
    return cursor.fetchall()

def get_stock_materia_prima(cursor):
    cursor.execute("SELECT codigo, nombre, stock FROM stock_materia_prima")
    return cursor.fetchall()

def get_stock_por_codigo(cursor, codigo):
    cursor.execute("SELECT codigo, nombre, stock FROM stock_materia_prima WHERE codigo = ?", (codigo,))
    return cursor.fetchone()

def main():
    ensure_db_seeded()
    logging.info('Base de datos lista ✅')

if __name__ == '__main__':
    main()
