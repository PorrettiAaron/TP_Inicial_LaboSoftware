import sys
import os
import tkinter as tk
from tkinter import messagebox

# Asegurar que el path de src esté incluido
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modern_gui import ModernFaceApp
from report_app import ReportApp
from dashboards_windows import DashboardsApp

#  Color y el estilo
COLOR_FONDO = "#2E2E2E"          # Gris oscuro
COLOR_BOTON = "#4CAF50"          # Verde moderno
COLOR_TEXTO = "#FFFFFF"          # Blanco
FUENTE_TITULO = ("Segoe UI", 16, "bold")
FUENTE_BOTON = ("Segoe UI", 12)

#  Visualizar ventana principal
ventana = tk.Tk()
ventana.title("Menú Principal")
ventana.geometry("400x300")
ventana.configure(bg=COLOR_FONDO)

# Frame centralizado
frame = tk.Frame(ventana, bg=COLOR_FONDO)
frame.pack(expand=True)

# Comentario de bienvenida
etiqueta = tk.Label(frame,
                    text="Selecciona una aplicación",
                    font=FUENTE_TITULO,
                    fg=COLOR_TEXTO,
                    bg=COLOR_FONDO)
etiqueta.pack(pady=(10, 20))

# Funcion de los botones
def abrir_reconocimiento_facial():
    ModernFaceApp(master=ventana)

def abrir_tablas():
    app = ReportApp()
    app.mainloop()

def abrir_reportes():
    try:
        import sqlite3
        conn = sqlite3.connect("./pyme_san_ignacio.db")
        cursor = conn.cursor()
        DashboardsApp(cursor)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la ventana de reportes:\n{e}")

# Crear botones
def crear_boton(texto, comando):
    return tk.Button(frame,
                     text=texto,
                     command=comando,
                     font=FUENTE_BOTON,
                     fg=COLOR_TEXTO,
                     bg=COLOR_BOTON,
                     activebackground="#45a049",
                     width=25,
                     height=2,
                     relief="flat",
                     cursor="hand2")

boton_reconocimiento = crear_boton("Reconocimiento Facial", abrir_reconocimiento_facial)
boton_reconocimiento.pack(pady=5)

boton_tablas = crear_boton("Tablas Referenciales", abrir_tablas)
boton_tablas.pack(pady=5)

boton_reportes = crear_boton("Reportes y Dashboards", abrir_reportes)
boton_reportes.pack(pady=5)

if __name__ == "__main__":
    ventana.mainloop()
