# sync_supabase.py
# Ejecutar:  python sync_supabase.py
# Sincroniza empleados, rostros y asistencia_empleado desde SQLite local a Supabase vía HTTP.
# Requisitos: pip install supabase python-dotenv

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from dotenv import load_dotenv
from supabase import create_client, Client

# --- asegurar import de src/ para reutilizar utils_db ---
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.utils_db import PYME_DB, get_connection  # usa tu DB local


# ------------------ utilidades ------------------
def rows_to_dicts(rows, cols) -> List[Dict[str, Any]]:
    return [dict(zip(cols, r)) for r in rows]


def fetch_all(sql: str, params=()):
    """Lee de SQLite usando tu helper get_connection."""
    from sqlite3 import Row
    results = []
    cols = []
    with get_connection(PYME_DB) as conn:
        conn.row_factory = Row
        cur = conn.cursor()
        cur.execute(sql, params)
        data = cur.fetchall()
        if data:
            cols = [d[0] for d in cur.description]
            results = [tuple(r) for r in data]
    return results, cols


def make_supabase() -> Client:
    load_dotenv()  # lee .env en raíz
    # Acepta variables con o sin prefijo REACT_APP_
    url = os.getenv("SUPABASE_URL") or os.getenv("REACT_APP_SUPABASE_URL")
    key = (
        os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_KEY")
        or os.getenv("REACT_APP_SUPABASE_ANON_KEY")
        or os.getenv("SUPABASE_ANON_KEY")
    )
    if not url or not key:
        raise RuntimeError(
            "Faltan credenciales. Definí SUPABASE_URL y SUPABASE_SERVICE_KEY (o ANON_KEY) en el .env"
        )
    print(f"Supabase URL: {url}")
    return create_client(url, key)


def chunked(iterable, size):
    """Genera bloques de tamaño 'size' para evitar rate limits."""
    for i in range(0, len(iterable)):
        if i % size == 0:
            yield iterable[i : i + size]


# ------------------ sincronizaciones ------------------
def sync_empleados(supabase: Client):
    rows, cols = fetch_all(
        "SELECT legajo, nombre, puesto, COALESCE(area,'') AS area FROM empleados ORDER BY legajo ASC"
    )
    if not rows:
        print("empleados: no hay filas para enviar.")
        return 0, 0

    data = rows_to_dicts(rows, cols)
    print(f"empleados: enviando {len(data)} filas…")
    inserted = 0
    for batch in chunked(data, 500):
        resp = supabase.table("empleados").upsert(
            batch, on_conflict="legajo"
        ).execute()
        # La API no devuelve counts exactos; asumimos éxito si no hay error
        inserted += len(batch)
    print("empleados: OK")
    return inserted, 0


def sync_rostros(supabase: Client):
    rows, cols = fetch_all("SELECT archivo, legajo FROM rostros ORDER BY archivo ASC")
    if not rows:
        print("rostros: no hay filas para enviar.")
        return 0, 0

    data = rows_to_dicts(rows, cols)
    print(f"rostros: enviando {len(data)} filas…")
    inserted = 0
    for batch in chunked(data, 500):
        supabase.table("rostros").upsert(batch, on_conflict="archivo").execute()
        inserted += len(batch)
    print("rostros: OK")
    return inserted, 0


def _normalize_ts(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        # epoch segundos
        try:
            return datetime.fromtimestamp(value).isoformat(sep=" ")
        except Exception:
            return None
    if isinstance(value, str):
        v = value.strip().replace("T", " ").replace("Z", "")
        # intentar varios formatos
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(v, fmt).isoformat(sep=" ")
            except ValueError:
                pass
        # último intento: fromisoformat
        try:
            return datetime.fromisoformat(v).isoformat(sep=" ")
        except ValueError:
            return v  # lo dejamos como está y que Postgres lo intente
    return str(value)


def sync_asistencias(supabase: Client):
    rows, cols = fetch_all(
        "SELECT legajo_empleado, entrada, salida FROM asistencia_empleado ORDER BY legajo_empleado, entrada ASC"
    )
    if not rows:
        print("asistencia_empleado: no hay filas para enviar.")
        return 0, 0

    dicts = []
    for r in rows:
        d = dict(zip(cols, r))
        d['entrada'] = _normalize_ts(d.get('entrada'))
        d['salida'] = _normalize_ts(d.get('salida'))
        dicts.append(d)

    print(f"asistencia_empleado: enviando {len(dicts)} filas…")
    inserted = 0
    for batch in chunked(dicts, 500):
        supabase.table("asistencia_empleado").upsert(
            batch, on_conflict="legajo_empleado,entrada"
        ).execute()
        inserted += len(batch)
    print("asistencia_empleado: OK")
    return inserted, 0


def main():
    print("Conectando a Supabase…")
    sb = make_supabase()

    # Respeta FKs: empleados -> rostros/asistencias
    e_ins, _ = sync_empleados(sb)
    r_ins, _ = sync_rostros(sb)
    a_ins, _ = sync_asistencias(sb)

    print("—" * 50)
    print(f"Totales enviados: empleados={e_ins}, rostros={r_ins}, asistencias={a_ins}")
    print("Sincronización finalizada ✅")


if __name__ == "__main__":
    main()
