import os
import tkinter as tk
from tkinter import messagebox, scrolledtext

from actions import Actions
from helpers import print_to_log, DATABASE_PATH, safe_regenerate_encodings

class FaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reconocimiento facial - Interfaz (Modular)")
        self.root.geometry("760x560")

        # ---- Controles superiores
        top = tk.Frame(root, padx=10, pady=10)
        top.pack(fill="x")

        self.btn_add_users = tk.Button(top, text="Agregar usuarios (seleccionar imágenes)", command=self.add_users)
        self.btn_add_users.grid(row=0, column=0, sticky="ew", padx=4, pady=4, columnspan=2)

        self.btn_webcam = tk.Button(top, text="Captar rostro con webcam", command=self.run_webcam_threaded)
        self.btn_webcam.grid(row=1, column=0, sticky="ew", padx=4, pady=4)

        self.btn_image = tk.Button(top, text="Captar rostro desde imagen", command=self.compare_from_image)
        self.btn_image.grid(row=1, column=1, sticky="ew", padx=4, pady=4)

        self.btn_rebuild = tk.Button(top, text="Regenerar encodings", command=self.rebuild_encodings)
        self.btn_rebuild.grid(row=2, column=0, sticky="ew", padx=4, pady=4)

        self.btn_check_bad = tk.Button(top, text="Detectar imágenes problemáticas", command=self.check_bad_images)
        self.btn_check_bad.grid(row=2, column=1, sticky="ew", padx=4, pady=4)

        # Umbral (informativo)
        thr_frame = tk.Frame(root, padx=10)
        thr_frame.pack(fill="x")
        tk.Label(thr_frame, text="Umbral (solo informativo):").pack(side="left")
        self.threshold_var = tk.DoubleVar(value=0.6)
        self.thr = tk.Scale(thr_frame, variable=self.threshold_var, from_=0.2, to=1.2, resolution=0.01,
                            orient="horizontal", length=300)
        self.thr.pack(side="left", padx=8)

        # ---- Log de resultados
        log_frame = tk.LabelFrame(root, text="Resultados / Log", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.txt_log = scrolledtext.ScrolledText(log_frame, height=18, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

        # Acciones (controlador)
        self.actions = Actions(self.txt_log, self.threshold_var)

        # Precarga de encodings
        try:
            safe_regenerate_encodings(DATABASE_PATH, text_sink=lambda m: print_to_log(self.txt_log, m))
        except Exception as e:
            messagebox.showwarning("Advertencia", f"No se pudieron generar encodings inicialmente.\n{e}")
        print_to_log(self.txt_log, "Sugerencia: añadí imágenes válidas en tests/db_images para armar la base.\n")

    # Eventos UI que delegan en Actions
    def add_users(self):
        self.actions.add_users()

    def run_webcam_threaded(self):
        self.actions.run_webcam_threaded()

    def compare_from_image(self):
        self.actions.compare_from_image()

    def rebuild_encodings(self):
        self.actions.rebuild_encodings()

    def check_bad_images(self):
        self.actions.check_bad_images()
