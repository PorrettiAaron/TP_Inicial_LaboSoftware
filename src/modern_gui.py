# modern_gui.py
# GUI moderna con CustomTkinter + OpenCV embebido
# - Automatiza ENTRADA/SALIDA con PresenceManager
# - Mapea archivos de rostros a legajo en SQLite
# Requiere: customtkinter, pillow, opencv-python

import os
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
# - get_face_encoding_from(np.ndarray | path) -> vector | [vector] | None
# - comparison(encoding_a, encoding_b) -> (distance: float, same_person: bool)
<<<<<<< HEAD:src/modern_gui.py
import utils_recognition as u_rec  # en tu repo actual el módulo se llama utils_recognition.py
import utils_db
import utils_files
=======
from src import utils_recognition as u_rec  # en tu repo actual el módulo se llama utils_recognition.py
from src import utils_db
>>>>>>> 2712f4676a941bb50b89e902001af7a0e0030dbc:modern_gui.py
from presence import PresenceManager

DATABASE_PATH = utils_db.PYME_EMPLOYEES_IMAGES
os.makedirs(DATABASE_PATH, exist_ok=True)

# ---------------- Aplicación ----------------
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


        # Utils de optimización
        # scanear face encoding uno de cada (self.skip_count_fps) frames de webcam
        self.skip_fps = 5
        self.count_current_fps = 0

        # Evitar encoding cuando el frame anterior tenía cara (se asume que es la misma persona)
        self.last_processed_webcam_frame_had_known_face = False

        # Scanear la misma cara (self.max_retries_face_encoding) veces para intentar ver si se encuentra en la DB
        # Para evitar problemas conde tiempo de scaneo con (self.last_processed_webcam_frame_had_known_face)
        # Aún no está implementado TODO
        self.max_attempts_face_encoding = 3
        self.count_attempts_face_encoding = 0

        # Presence automation
        self.presence = PresenceManager(
            on_event=self._on_presence_event,
            disappear_seconds=10.0,
            cooldown_seconds=30.0,
        )

        # Layout: sidebar (izq) / main (centro) / right (log)
        self.grid_columnconfigure(0, weight=0)  # sidebar
        self.grid_columnconfigure(1, weight=1)  # main
        self.grid_columnconfigure(2, weight=0)  # right panel
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._build_right_panel()

        # Inicializar DB y encodings
        self.db_encs = None
        try:
            utils_db.ensure_db_seeded()
        except Exception as e:
            self._safe_log(f"[DB] No se pudo preparar la DB: {e}")

        self._safe_log("Generando/actualizando encodings de la base...")
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            self.db_encs = u_rec.get_saved_encodings(DATABASE_PATH)
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
        self.thr_scale = ctk.CTkSlider(self.sidebar, from_=0, to=1, number_of_steps=100, variable=self.threshold_var)
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

        self.video_label = ctk.CTkLabel(self.video_frame, text="Webcam detenida", text_color="#FFF", width=800, height=450, anchor="center",fg_color="#000")
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
        ctk.CTkButton(self.right, text="Limpiar log", command=lambda: self.log_txt.delete("1.0", "end"), fg_color="#444", hover_color="#666").grid(row=3, column=0, sticky="we", padx=12, pady=(0,12))

    # ---------- Helpers GUI ----------
    def _safe_log(self, text):
        try:
            self.log_txt.insert("end", text + ("\n" if not text.endswith("\n") else ""))
            self.log_txt.see("end")
        except Exception:
            pass

    def _on_theme_change(self, mode):
        ctk.set_appearance_mode(mode)

    # ---------- Resolución de legajo ----------
    def _extract_legajo_from_key(self, key: str):
        import os
        base = os.path.splitext(key)[0]
        return int(base) if str(base).isdigit() else None

    def _resolve_legajo_from_fname(self, fname: str):
        # 1) Si el nombre del archivo es un número → legajo directo
        leg = self._extract_legajo_from_key(fname)
        if leg is not None:
            return leg
        # 2) Intentar buscar mapeo en DB
        try:
            with utils_db.get_connection() as conn:
                cur = conn.cursor()
                mapped = utils_db.get_legajo_for_filename(cur, fname)
                if mapped is not None:
                    return mapped
        except Exception:
            pass
        return None

    # ---------- Presence callback ----------
    def _on_presence_event(self, evento: str, legajo: int, t: float):
        if legajo is None:
            self._safe_log("Por algun motivo legajo None llegó a este método")
            return
        try:
            with utils_db.get_connection() as conn:
                cur = conn.cursor()
                utils_db.empleado_detected(cur, legajo, t)
            self._safe_log(f"[DB] Legajo {legajo}: {evento.upper()} registrada a las {utils_db.get_timestamp_from_posix_version(t)}")
        except Exception as e:
            traceback.print_exc()

    # ---------- Actions ----------
    def on_add_users(self):
        paths = filedialog.askopenfilenames(title="Seleccioná imágenes de usuarios",
                                            filetypes=[("Imágenes", " ".join(f"*.{ext}" for ext in utils_files.ACCEPTABLE_IMAGE_EXTENSIONS))])
        if not paths:
            return

        # Pedir alias para renombrar
        dlg_name = ctk.CTkInputDialog(text="Ingresá nombre/alias para etiquetar estas imágenes:", title="Agregar usuarios")
        person_name = dlg_name.get_input()
        if not person_name:
            messagebox.showinfo("Info", "Operación cancelada: no se indicó alias.")
            return

        copied = 0
        os.makedirs(DATABASE_PATH, exist_ok=True)
        new_files = []
        for i, src in enumerate(paths, start=1):
            ext = utils_files.get_file_extension(src)
            if not utils_files.is_valid_image_extension(ext):
                continue
            dst_name = f"{person_name}_{i:03d}.{ext}"
            dst_path = os.path.join(DATABASE_PATH, dst_name)
            idx = i
            while os.path.exists(dst_path):
                idx += 1
                dst_name = f"{person_name}_{idx:03d}{ext}"
                dst_path = os.path.join(DATABASE_PATH, dst_name)
            try:
                with open(src, "rb") as fi, open(dst_path, "wb") as fo:
                    fo.write(fi.read())
                copied += 1
                new_files.append(dst_name)
            except Exception as e:
                self._safe_log(f"[ERROR] Copiando {src}: {e}")

        self._safe_log(f"Copiadas {copied} imágenes a {DATABASE_PATH}")

        if copied > 0:
            # Mapear a legajo
            try:
                dlg_leg = ctk.CTkInputDialog(text="Ingresá NÚMERO de legajo para asociar estas imágenes:", title="Mapear legajo")
                leg_str = dlg_leg.get_input()
                if leg_str and leg_str.isdigit():
                    legajo = int(leg_str)
                    with utils_db.get_connection() as conn:
                        cur = conn.cursor()
                        for fname in new_files:
                            utils_db.add_face_mapping(cur, fname, legajo)
                    self._safe_log(f"Asociadas {copied} imágenes al legajo {legajo}.")
                else:
                    self._safe_log("No se ingresó un legajo válido; no se guardó mapeo.")
            except Exception as e:
                self._safe_log(f"[DB][ERROR] Mapeando legajo: {e}")

            if messagebox.askyesno("Encodings", "¿Regenerar encodings ahora?"):
                self.on_rebuild_encodings()

    def on_compare_from_image(self):
        img_path = filedialog.askopenfilename(title="Seleccioná una imagen",
                                              filetypes=[("Imágenes", " ".join(f"*.{ext}" for ext in utils_files.ACCEPTABLE_IMAGE_EXTENSIONS))])
        if not img_path:
            return

        self._safe_log(f"Imagen seleccionada: {img_path}")
        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
#            self.db_encs = u_rec.get_saved_encodings(DATABASE_PATH)

            main_enc = u_rec.get_face_encoding(img_path)
            if main_enc is None:
                self._safe_log("No se detectó un rostro válido en la imagen.")
                return

            matches = []
            for fname, person_enc in self.db_encs.items():
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
            #    for f, dist in sorted(matches, key=lambda x: x[1]):
#                    self._safe_log(f"  - {f} | distancia = {dist:.4f} (umbral ~ {self.threshold_var.get():.2f})")
            else:
                self._safe_log("No se encontraron coincidencias.")

        except u_rec.MultipleFacesDetectedException:
            self._safe_log("[ERROR] Se detectaron más de una cara en la imagen. Por favor, asegúrese de que haya únicamente una cara.")
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
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            all_encs = self.db_encs
            bad = []
            for name, enc in all_encs.items():
                if enc is None:
                    bad.append(name)
            if bad:
                self._safe_log("Imágenes sin encoding (reemplazar o borrar):")
                for b in bad:
                    self._safe_log(f"  - {b}")
            else:
                self._safe_log("No hay imágenes problemáticas en la base.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar la base: {e}")

    # ---------- Webcam ----------
    def on_start_webcam(self):
        if self.webcam_running:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Webcam", "No se pudo abrir la cámara.")
            return
        self.webcam_running = True
        self._update_video_frame()

    def on_stop_webcam(self):
        self.webcam_running = False
        if self.video_loop_job:
            self.after_cancel(self.video_loop_job)
            self.video_loop_job = None
        if self.cap is not None:
            self.cap.release()
            self.cap = None

        # Poner imagen vacía para que no muestre el último frame de la webcam
        blank = Image.new("RGB", (900, 500), (0,0,0))
        imgtk = ImageTk.PhotoImage(blank)
        self.video_label.configure(text="Webcam detenida", image=imgtk)
        self.video_label.imgtk_ref = imgtk

    def _update_video_frame(self):

        if not self.webcam_running or self.cap is None:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.on_stop_webcam()
            return


        if  self.count_current_fps < self.skip_fps:
            print("[SKIP] Frame")
            self.count_current_fps += 1

        else:

            self.count_current_fps = 0

            process_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            # Si tu encoder requiere RGB, descomentar:
            # process_small = cv2.cvtColor(process_small, cv2.COLOR_BGR2RGB)

            try:
                face_loc = u_rec.get_face_location(process_small)
                if face_loc is not None:
                    if self.last_processed_webcam_frame_had_face:
                        enc = None
                        print("[SKIP] Misma persona detectada.")
                    else:
                        enc = u_rec.get_face_encoding(process_small,known_location=face_loc)
                        print("Nueva cara detectada")
                else:
                    self.last_processed_webcam_frame_had_face = False
                    self.count_attempts_face_encoding = 0
                    enc = None


            except u_rec.MultipleFacesDetectedException as e:
                self._safe_log("[ERROR] Se detectaron más de una cara en la webcam. Por favor, limite a una sola persona por reconocimiento.")
                self.last_processed_webcam_frame_had_face = False
                enc = None

            if enc is not None and self.db_encs is not None:
                self.last_processed_webcam_frame_had_face = True
                print("Buscando coincidencias...")
                any_match = False
                for fname, other_enc in self.db_encs.items():
                    if other_enc is None:
                        continue
                    try:
                        d, same = u_rec.comparison(enc, other_enc, tolerance=self.threshold_var.get())
                    except Exception as e:
                        self._safe_log(f"[ERROR] Comparando con {fname}: {e}")
                        continue
                    if same:
                        any_match = True
                        self._safe_log(f"Match con {fname} | d={d:.4f} (umbral ~ {self.threshold_var.get():.2f})")
                        leg = self._resolve_legajo_from_fname(fname)
                        self.presence.detection(leg)
                if not any_match:
                    self._safe_log("Sin coincidencias en este frame.")

        # Mostrar en la UI (convertir a RGB para Pillow)
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
