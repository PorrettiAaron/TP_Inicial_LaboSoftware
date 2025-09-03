# modern_gui.py
# GUI moderna con CustomTkinter + OpenCV embebido
# Requiere: customtkinter, pillow, opencv-python
import os
import threading
import time

import cv2
import numpy as np

try:
    import customtkinter as ctk
except ImportError as e:
    raise SystemExit("Falta 'customtkinter'. Instalá con: pip install customtkinter") from e

try:
    from PIL import Image, ImageTk
except ImportError as e:
    raise SystemExit("Falta 'Pillow'. Instalá con: pip install pillow") from e

from tkinter import filedialog, messagebox

# Ajustá este import a tu proyecto
# Debe proveer:
# - _save_encodings_if_necessary(db_path)
# - get_saved_encodings(db_path) -> dict[str, np.ndarray | list | None]
# - get_face_encoding_from_opencv_frame(frame_bgr|rgb) -> vector | [vector] | None
# - get_face_encoding(np.ndarray | path) -> vector | [vector] | None
# - comparison(encoding_a, encoding_b) -> (distance: float, same_person: bool)
import src.utils_recognition as u_rec  # noqa: E402
from src.utils_recognition import ACCEPTABLE_IMAGE_EXTENSIONS

import helpers

DATABASE_PATH = "./tests/db_images/"
os.makedirs(DATABASE_PATH, exist_ok=True)

class ModernFaceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reconocimiento Facial - Interfaz Moderna")
        self.geometry("1100x700")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Estado
        self.webcam_running = False
        self.cap = None
        self.video_loop_job = None
        self.threshold_var = ctk.DoubleVar(value=u_rec.EUCLIDEAN_DISTANCE_TOLERANCE)

        # Layout: sidebar (izq) / main (centro) / right (log)
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # main
        self.grid_columnconfigure(2, weight=0)  # right panel
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_right_panel()

        # Inicial: generar encodings si hace falta
        self._safe_log("Generando/actualizando encodings de la base...")
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            self._safe_log("Encodings listos.\n")
        except Exception as e:
            self._safe_log(f"[ADVERTENCIA] No se pudieron generar encodings iniciales: {e}\n")

    # ---------- UI BUILDERS ----------
    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nswe")
        self.sidebar.grid_rowconfigure(8, weight=1)

        title = ctk.CTkLabel(self.sidebar, text="Panel de Control", font=("Segoe UI", 18, "bold"))
        title.pack(padx=16, pady=(18, 8))

        ctk.CTkButton(self.sidebar, text="Agregar usuarios", command=self.on_add_users).pack(padx=16, pady=6, fill="x")
        ctk.CTkButton(self.sidebar, text="Comparar desde imagen", command=self.on_compare_from_image).pack(padx=16, pady=6, fill="x")

        self.btn_start = ctk.CTkButton(self.sidebar, text="Iniciar webcam", command=self.on_start_webcam)
        self.btn_start.pack(padx=16, pady=(16,6), fill="x")
        self.btn_stop = ctk.CTkButton(self.sidebar, text="Detener webcam", command=self.on_stop_webcam, fg_color="#933", hover_color="#B44")
        self.btn_stop.pack(padx=16, pady=6, fill="x")

        ctk.CTkButton(self.sidebar, text="Regenerar encodings", command=self.on_rebuild_encodings).pack(padx=16, pady=(16,6), fill="x")
        ctk.CTkButton(self.sidebar, text="Detectar imágenes problemáticas", command=self.on_check_bad_images).pack(padx=16, pady=6, fill="x")

        # Threshold
        thr_label = ctk.CTkLabel(self.sidebar, text="Umbral (referencia)")
        thr_label.pack(padx=16, pady=(16,4))
        self.thr_scale = ctk.CTkSlider(self.sidebar, from_=0.0, to=1.0, number_of_steps=100, variable=self.threshold_var)
        self.thr_scale.pack(padx=16, pady=(0,10), fill="x")

        # Tema
        theme_label = ctk.CTkLabel(self.sidebar, text="Tema")
        theme_label.pack(padx=16, pady=(10,2))
        self.theme_opt = ctk.CTkOptionMenu(self.sidebar, values=["dark", "light", "system"], command=self._on_theme_change)
        self.theme_opt.set("dark")
        self.theme_opt.pack(padx=16, pady=(0,14), fill="x")

        # Salir
        ctk.CTkButton(self.sidebar, text="Salir", command=self.destroy).pack(padx=16, pady=(6,18), fill="x")

    def _build_main(self):
        self.main = ctk.CTkFrame(self, corner_radius=12)
        self.main.grid(row=0, column=1, sticky="nswe", padx=12, pady=12)
        self.main.grid_rowconfigure(1, weight=1)
        self.main.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(self.main, text="Vista de cámara / Resultados", font=("Segoe UI", 18, "bold"))
        header.grid(row=0, column=0, sticky="w", padx=16, pady=(16,6))

        # Video preview
        self.video_frame = ctk.CTkFrame(self.main, corner_radius=12)
        self.video_frame.grid(row=1, column=0, sticky="nswe", padx=16, pady=12)
        self.video_frame.grid_rowconfigure(0, weight=1)
        self.video_frame.grid_columnconfigure(0, weight=1)

        self.video_label = ctk.CTkLabel(self.video_frame, text="Webcam detenida", width=800, height=450, anchor="center")
        self.video_label.grid(row=0, column=0, sticky="nswe", padx=12, pady=12)

        # Footer helpers
        footer = ctk.CTkFrame(self.main, corner_radius=12)
        footer.grid(row=2, column=0, sticky="we", padx=16, pady=(0,16))
        tip = ctk.CTkLabel(footer, text="Consejo: mantené la cara centrada y con buena luz. Presioná 'Detener webcam' para liberar la cámara.", wraplength=800, justify="left")
        tip.pack(side="left", padx=12, pady=10)

    def _build_right_panel(self):
        self.right = ctk.CTkFrame(self, width=360, corner_radius=12)
        self.right.grid(row=0, column=2, sticky="nswe", padx=(0,12), pady=12)
        self.right.grid_rowconfigure(2, weight=1)
        self.right.grid_columnconfigure(0, weight=1)

        lbl = ctk.CTkLabel(self.right, text="Log / Matches", font=("Segoe UI", 18, "bold"))
        lbl.grid(row=0, column=0, sticky="w", padx=12, pady=(12,6))

        self.log_txt = ctk.CTkTextbox(self.right, height=400)
        self.log_txt.grid(row=2, column=0, sticky="nswe", padx=12, pady=(6,12))

        # Quick clear
        btn_clear = ctk.CTkButton(self.right, text="Limpiar log", command=lambda: self.log_txt.delete("1.0", "end"), fg_color="#444", hover_color="#666")
        btn_clear.grid(row=3, column=0, sticky="we", padx=12, pady=(0,12))

    # ---------- Helpers ----------
    def _safe_log(self, text):
        try:
            self.log_txt.insert("end", text + ("\n" if not text.endswith("\n") else ""))
            self.log_txt.see("end")
        except Exception:
            pass

    def _on_theme_change(self, mode):
        ctk.set_appearance_mode(mode)

    # ---------- Actions ----------
    def on_add_users(self):
        paths = filedialog.askopenfilenames(title="Seleccioná imágenes de usuarios",
            filetypes=[("Imágenes", " ".join("*.{}".format(ext) for ext in ACCEPTABLE_IMAGE_EXTENSIONS)), ("Todos", "*.*")])

        if not paths:
            return

        # Pedir nombre:
        dlg = ctk.CTkInputDialog(text="Ingresá nombre/alias para las imágenes:", title="Agregar usuarios")
        person_name = dlg.get_input()
        if not person_name:
            messagebox.showinfo("Info", "Operación cancelada: no se indicó nombre.")
            return

        copied = 0
        os.makedirs(DATABASE_PATH, exist_ok=True)
        for i, src in enumerate(paths, start=1):
            ext = os.path.splitext(src)[1][1:]
            if not u_rec.is_valid_image_extension(ext):
                continue
            dst_name = f"{person_name}_{i:03d}.{ext}"
            dst_path = os.path.join(DATABASE_PATH, dst_name)
            idx = i
            while os.path.exists(dst_path):
                idx += 1
                dst_name = f"{person_name}_{idx:03d}.{ext}"
                dst_path = os.path.join(DATABASE_PATH, dst_name)
            try:
                # copiar binario
                with open(src, "rb") as fi, open(dst_path, "wb") as fo:
                    fo.write(fi.read())
                copied += 1
            except Exception as e:
                self._safe_log(f"[ERROR] Copiando {src}: {e}")

        self._safe_log(f"Copiadas {copied} imágenes a {DATABASE_PATH}")
        if copied > 0:
            if messagebox.askyesno("Encodings", "¿Regenerar encodings ahora?"):
                self.on_rebuild_encodings()

    def on_compare_from_image(self):
        img_path = filedialog.askopenfilename(title="Seleccioná una imagen",
            filetypes=[("Imágenes", " ".join("*.{}".format(ext) for ext in ACCEPTABLE_IMAGE_EXTENSIONS))])

        if not img_path:
            return

        self._safe_log(f"Imagen seleccionada: {img_path}")
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            db_encs = helpers.filtered_db_encodings(u_rec.get_saved_encodings(DATABASE_PATH))

            main_enc = u_rec.get_face_encoding(img_path)
            if main_enc is None:
                self._safe_log("No se detectó un rostro válido en la imagen.")
                return

            self._safe_log("Comparando {img_path} con las imágenes de la base de datos...")

            matches = []
            for fname, person_enc in db_encs.items():
                if person_enc is None:
                    continue
                try:
                    d, same = u_rec.comparison(main_enc, person_enc, tolerance=self.threshold_var.get())
                except Exception as e:
                    self._safe_log(f"[ERROR] Comparando con {fname}: {e}")
                    continue
                if same:
                    matches.append((fname, d))

            if matches:
                self._safe_log("¡Coincidencias encontradas!")
                for f, dist in sorted(matches, key=lambda x: x[1]):
                    self._safe_log(f"  - {f} | distancia = {dist:.4f} (umbral ~ {self.threshold_var.get():.2f})")
            else:
                self._safe_log("No se encontraron coincidencias.")
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al comparar: {e}")

    def on_rebuild_encodings(self):
        self._safe_log("Regenerando encodings...")
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            self._safe_log("Encodings regenerados correctamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron regenerar encodings: {e}")

    def on_check_bad_images(self):
        try:
            bad_files = helpers.find_invalid_db_images()
            if not bad_files:
                self._safe_log("No hay imágenes problemáticas en la base.")
            else:
                self._safe_log("Imágenes sin encoding (reemplazar o borrar):")
                for b in bad_files:
                    self._safe_log(f"  - {b}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar la base: {e}")

    # ---------- Webcam ----------
    def on_start_webcam(self):
        if self.webcam_running:
            return
        # Abrimos la cámara
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Webcam", "No se pudo abrir la cámara.")
            return
        self.webcam_running = True
        # Pre-cargar encodings
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            self.db_encs = helpers.filtered_db_encodings(u_rec.get_saved_encodings(DATABASE_PATH))
        except Exception as e:
            self._safe_log(f"[ADVERTENCIA] No se pudo preparar la base: {e}")
            self.db_encs = {}
        # Iniciar loop de video
        self._update_video_frame()

    def on_stop_webcam(self):
        self.webcam_running = False
        if self.video_loop_job:
            self.after_cancel(self.video_loop_job)
            self.video_loop_job = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.video_label.configure(text="Webcam detenida", image=None)

    def _update_video_frame(self):
        if not self.webcam_running or self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.on_stop_webcam()
            return

        # Redimensionar para procesamiento, mantener original para display
        process_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)

        # Obtener encoding (tu función puede esperar BGR o RGB; si requiere RGB, descomentar siguiente línea)
        # process_small = cv2.cvtColor(process_small, cv2.COLOR_BGR2RGB)
        try:
            enc = u_rec.get_face_encoding_from_opencv_frame(process_small)

        except u_rec.MultipleFacesDetectedException:
             self._safe_log(f"[ERROR] Se detectó más de una cara en cámara, por favor, limite a una persona a la vez.")
             enc = None

        if enc is not None and self.db_encs:
            any_match = False
            for fname, other_enc in self.db_encs.items():
                if other_enc is None:
                    continue
                try:
                    d, same = u_rec.comparison(enc, other_enc)
                except Exception as e:
                    self._safe_log(f"[ERROR] Comparando con {fname}: {e}")
                    continue
                if same:
                    any_match = True
                    self._safe_log(f"Match con {fname} | d={d:.4f} (umbral ~ {self.threshold_var.get():.2f})")
            if not any_match:
                self._safe_log("Sin coincidencias en este frame.")

        # Mostrar en la UI (convertir a RGB)
        display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display)
        img = img.resize((900, 500), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        self.video_label.configure(image=imgtk, text="")
        self.video_label.imgtk_ref = imgtk  # evitar GC

        self.video_loop_job = self.after(30, self._update_video_frame)


if __name__ == "__main__":
    app = ModernFaceApp()
    app.mainloop()
