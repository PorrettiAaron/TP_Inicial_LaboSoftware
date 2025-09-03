import os
import shutil
import threading
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox, scrolledtext

# --- Dependencias externas ---
# pip install opencv-python
# (Opcional Pillow si querés thumbnails en la GUI)

import cv2

# Ajustá este import a tu proyecto. Debe proveer:
# - _save_encodings_if_necessary(db_path)
# - get_saved_encodings(db_path) -> dict[str, np.ndarray | list | None]
# - get_face_encoding_from_opencv_frame(frame) -> vector | [vector] | None
# - get_face_encoding_from_image_path(path) -> vector | [vector] | None
# - comparison(encoding_a, encoding_b) -> (distance: float, same_person: bool)
import src.utils_recognition as u_rec  # noqa: E402

# ---------------- Config ----------------
DATABASE_PATH = "./tests/db_images/"
TEST_IMAGE_PATH_DEFAULT = "./tests/img_test.jpg"  # Solo como sugerencia inicial de ruta

# Asegurar carpeta de base
os.makedirs(DATABASE_PATH, exist_ok=True)


# ---------------- Utilidades ----------------
def print_to_log(widget: scrolledtext.ScrolledText, msg: str):
    widget.configure(state="normal")
    widget.insert(tk.END, msg)
    widget.see(tk.END)
    widget.configure(state="disabled")


def safe_regenerate_encodings(database_path: str, text_sink=None):
    """
    Regenera encodings si hace falta (o fuerza la creación).
    """
    if text_sink:
        text_sink("Generando/actualizando encodings de la base...\n")
    u_rec._save_encodings_if_necessary(database_path)
    if text_sink:
        text_sink("Encodings listos.\n")


def normalize_encoding(enc):
    """
    Acepta vector, lista/tupla de vectores o None.
    Devuelve: vector o None.
    """
    if enc is None:
        return None
    if isinstance(enc, (list, tuple)):
        return enc[0] if len(enc) > 0 else None
    return enc


def filtered_db_encodings(db_dict):
    """
    Quita entradas None o vacías.
    """
    cleaned = {}
    for k, v in db_dict.items():
        if v is None:
            continue
        if isinstance(v, (list, tuple)) and len(v) == 0:
            continue
        cleaned[k] = normalize_encoding(v)
    return cleaned


def find_invalid_db_images():
    """
    Devuelve lista de nombres de archivo en la base que no tienen encoding válido.
    """
    u_rec._save_encodings_if_necessary(DATABASE_PATH)
    encs = u_rec.get_saved_encodings(DATABASE_PATH)
    bad = []
    for name, enc in encs.items():
        enc = normalize_encoding(enc)
        if enc is None:
            bad.append(name)
    return bad


# ---------------- Lógica de GUI ----------------
class FaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Reconocimiento facial - Interfaz")
        self.root.geometry("720x520")

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

        # Umbral (opcional, si tu comparison usa uno interno, podés ignorar esto.
        # Aquí solo lo usamos para log y potencial uso propio)
        thr_frame = tk.Frame(root, padx=10)
        thr_frame.pack(fill="x")
        tk.Label(thr_frame, text="Umbral (solo informativo):").pack(side="left")
        self.threshold_var = tk.DoubleVar(value=0.6)
        self.thr = tk.Scale(thr_frame, variable=self.threshold_var, from_=0.2, to=1.2, resolution=0.01,
                            orient="horizontal", length=280)
        self.thr.pack(side="left", padx=8)

        # ---- Log de resultados
        log_frame = tk.LabelFrame(root, text="Resultados / Log", padx=8, pady=8)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.txt_log = scrolledtext.ScrolledText(log_frame, height=16, state="disabled")
        self.txt_log.pack(fill="both", expand=True)

        # Estado de webcam
        self.webcam_running = False
        self.webcam_thread = None

        # Precarga de encodings (si aplica)
        try:
            safe_regenerate_encodings(DATABASE_PATH, text_sink=lambda m: print_to_log(self.txt_log, m))
        except Exception as e:
            messagebox.showwarning("Advertencia", f"No se pudieron generar encodings inicialmente.\n{e}")

        # Tip inicial
        print_to_log(self.txt_log, "Sugerencia: añadí imágenes válidas en tests/db_images para armar la base.\n")

    # -------- Agregar usuarios --------
    def add_users(self):
        files = filedialog.askopenfilenames(
            title="Seleccioná una o varias imágenes para agregar a la base",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Todos", "*.*")]
        )
        if not files:
            return

        person_name = simpledialog.askstring(
            "Nombre de persona",
            "Ingresá un nombre/alias para etiquetar estas imágenes (se usará como prefijo de archivo):"
        )
        if not person_name:
            messagebox.showinfo("Acción cancelada", "No se especificó un nombre. Operación cancelada.")
            return

        # Copiar con nombres únicos
        copied = 0
        for i, src in enumerate(files, start=1):
            ext = os.path.splitext(src)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                continue
            # Nombre destino
            dst_name = f"{person_name}_{i:03d}{ext}"
            dst_path = os.path.join(DATABASE_PATH, dst_name)
            # Evitar overwrite
            idx = i
            while os.path.exists(dst_path):
                idx += 1
                dst_name = f"{person_name}_{idx:03d}{ext}"
                dst_path = os.path.join(DATABASE_PATH, dst_name)

            try:
                shutil.copy2(src, dst_path)
                copied += 1
            except Exception as e:
                print_to_log(self.txt_log, f"Error copiando {src}: {e}\n")

        print_to_log(self.txt_log, f"Copiadas {copied} imágenes a {DATABASE_PATH}\n")

        # Preguntar si desea regenerar encodings ahora
        if copied > 0:
            if messagebox.askyesno("Encodings", "¿Regenerar encodings ahora? (recomendado)"):
                try:
                    safe_regenerate_encodings(DATABASE_PATH, text_sink=lambda m: print_to_log(self.txt_log, m))
                except Exception as e:
                    messagebox.showerror("Error", f"Fallo al regenerar encodings: {e}")

    # -------- Webcam (captura y comparación) --------
    def run_webcam_threaded(self):
        if self.webcam_running:
            messagebox.showinfo("Webcam", "La captura por webcam ya se está ejecutando.\nCerrá la ventana de video (tecla 'q') para detenerla.")
            return
        self.webcam_thread = threading.Thread(target=self._webcam_loop, daemon=True)
        self.webcam_thread.start()

    def _webcam_loop(self):
        """
        Obtiene frames, extrae encoding (normalizado) y compara contra la base.
        Cerrar con la tecla 'q' en la ventana de OpenCV.
        """
        self.webcam_running = True
        try:
            # Preparar encodings guardados
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            saved_encodings = filtered_db_encodings(u_rec.get_saved_encodings(DATABASE_PATH))

            if not saved_encodings:
                print_to_log(self.txt_log, "Aviso: la base está vacía o sin encodings válidos.\n")

            video_capture = cv2.VideoCapture(0)
            if not video_capture.isOpened():
                messagebox.showerror("Webcam", "No se pudo abrir la cámara.")
                self.webcam_running = False
                return

            while True:
                ret, frame = video_capture.read()
                if not ret:
                    break

                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                encoding = normalize_encoding(u_rec.get_face_encoding_from_opencv_frame(small_frame))

                if encoding is not None:
                    any_match = False
                    for file_name, other_encoding in saved_encodings.items():
                        if other_encoding is None:
                            print_to_log(self.txt_log, f"[AVISO] {file_name} no tiene encoding válido.\n")
                            continue
                        try:
                            d, are_the_same = u_rec.comparison(encoding, other_encoding)
                        except Exception as e:
                            print_to_log(self.txt_log, f"[ERROR] Comparando con {file_name}: {e}\n")
                            continue
                        if are_the_same:
                            any_match = True
                            print_to_log(self.txt_log, f"Match con {file_name}. Distancia = {d:.4f} (umbral ~ {self.threshold_var.get():.2f})\n")
                    if not any_match:
                        print_to_log(self.txt_log, "Sin coincidencias en este frame.\n")

                cv2.imshow("Presioná 'q' para salir", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

            video_capture.release()
            cv2.destroyAllWindows()
        except Exception as e:
            messagebox.showerror("Error en webcam", str(e))
        finally:
            self.webcam_running = False

    # -------- Comparar desde una imagen --------
    def compare_from_image(self):
        img_path = filedialog.askopenfilename(
            title="Seleccioná una imagen para comparar",
            initialdir=os.path.dirname(TEST_IMAGE_PATH_DEFAULT) if os.path.exists(TEST_IMAGE_PATH_DEFAULT) else ".",
            filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp *.webp"), ("Todos", "*.*")]
        )
        if not img_path:
            return
        print_to_log(self.txt_log, f"Imagen seleccionada: {img_path}\n")

        try:
            u_rec._save_encodings_if_necessary(DATABASE_PATH)
            database_encodings = filtered_db_encodings(u_rec.get_saved_encodings(DATABASE_PATH))

            main_img_encoding = normalize_encoding(u_rec.get_face_encoding_from_image_path(img_path))
            if main_img_encoding is None:
                print_to_log(self.txt_log, "No se detectó un rostro válido en la imagen.\n")
                return

            matches = []
            for file_name, person_encoding in database_encodings.items():
                if person_encoding is None:
                    print_to_log(self.txt_log, f"[AVISO] {file_name} no tiene encoding válido.\n")
                    continue
                try:
                    d, same_person = u_rec.comparison(main_img_encoding, person_encoding)
                except Exception as e:
                    print_to_log(self.txt_log, f"[ERROR] Comparando con {file_name}: {e}\n")
                    continue
                if same_person:
                    matches.append((os.path.join(DATABASE_PATH, file_name), d))

            if matches:
                print_to_log(self.txt_log, f"¡Coincidencias encontradas con {os.path.basename(img_path)}!\n")
                for f, dist in sorted(matches, key=lambda x: x[1]):
                    print_to_log(self.txt_log, f"  {os.path.basename(f)} | distancia = {dist:.4f} (umbral ~ {self.threshold_var.get():.2f})\n")
            else:
                print_to_log(self.txt_log, "No se encontraron coincidencias.\n")

        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un problema al comparar: {e}")

    # -------- Regenerar encodings manualmente --------
    def rebuild_encodings(self):
        try:
            safe_regenerate_encodings(DATABASE_PATH, text_sink=lambda m: print_to_log(self.txt_log, m))
            messagebox.showinfo("Listo", "Encodings regenerados.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron regenerar encodings: {e}")

    # -------- Detectar imágenes sin encoding --------
    def check_bad_images(self):
        try:
            bad = find_invalid_db_images()
            if bad:
                print_to_log(self.txt_log, "Imágenes sin encoding (reemplazar o borrar):\n")
                for b in bad:
                    print_to_log(self.txt_log, f"  - {b}\n")
            else:
                print_to_log(self.txt_log, "No hay imágenes problemáticas en la base.\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo verificar la base: {e}")


# ---------------- Main ----------------
if __name__ == "__main__":
    root = tk.Tk()
    app = FaceApp(root)
    root.mainloop()
