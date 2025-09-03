import os
from tkinter import scrolledtext

import src.utils_recognition as u_rec

# ---------------- Config ----------------
DATABASE_PATH = "./tests/db_images/"
TEST_IMAGE_PATH_DEFAULT = "./tests/img_test.jpg"
os.makedirs(DATABASE_PATH, exist_ok=True)


# ---------------- Utilidades generales ----------------
def print_to_log(widget: scrolledtext.ScrolledText, msg: str):
    widget.configure(state="normal")
    widget.insert("end", msg)
    widget.see("end")
    widget.configure(state="disabled")


def safe_regenerate_encodings(database_path: str, text_sink=None):
    if text_sink:
        text_sink("Generando/actualizando encodings de la base...\n")
    u_rec._save_encodings_if_necessary(database_path)
    if text_sink:
        text_sink("Encodings listos.\n")


def filtered_db_encodings(db_dict):
    """
    Quita entradas None o vacías, y normaliza listas/tuplas a vector.
    """
    cleaned = {}
    for k, v in db_dict.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)) and len(v) == 0:
            continue
        cleaned[k] = v
    return cleaned

def find_invalid_db_images():
    """
    Devuelve lista de nombres de archivo en la base que no tienen encoding válido.
    """
    u_rec._save_encodings_if_necessary(DATABASE_PATH)
    encs = u_rec.get_saved_encodings(DATABASE_PATH)
    bad = []
    for name, enc in encs.items():
        if enc is None:
            bad.append(name)
    return bad
