import os
import shutil
import threading
from tkinter import filedialog, simpledialog, messagebox

import cv2

from helpers import (
    print_to_log, DATABASE_PATH, safe_regenerate_encodings,
    normalize_encoding, filtered_db_encodings, find_invalid_db_images
)
import src.utils_recognition as u_rec


class Actions:
    def __init__(self, txt_log_widget, threshold_var):
        self.txt_log = txt_log_widget
        self.threshold_var = threshold_var
        self.webcam_running = False
        self.webcam_thread = None

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

        os.makedirs(DATABASE_PATH, exist_ok=True)
        copied = 0
        for i, src in enumerate(files, start=1):
            ext = os.path.splitext(src)[1].lower()
            if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]:
                continue
            dst_name = f"{person_name}_{i:03d}{ext}"
            dst_path = os.path.join(DATABASE_PATH, dst_name)
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
        self.webcam_running = True
        try:
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
                    matches.append((file_name, d))

            if matches:
                print_to_log(self.txt_log, "¡Coincidencias encontradas!\n")
                for f, dist in sorted(matches, key=lambda x: x[1]):
                    print_to_log(self.txt_log, f"  {f} | distancia = {dist:.4f} (umbral ~ {self.threshold_var.get():.2f})\n")
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
