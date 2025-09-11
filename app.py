import sys
import os
import tkinter as tk
from tkinter import messagebox

# Asegurar que el path de src esté incluido
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.modern_gui import ModernFaceApp
from report_app import ReportApp
from dashboards_windows import DashboardsApp

# Crear la ventana principal
ventana = tk.Tk()
ventana.title("Menú Principal")
ventana.geometry("300x200")

# Etiqueta de bienvenida
etiqueta = tk.Label(ventana, text="Selecciona una aplicación", font=("Arial", 14))
etiqueta.pack(pady=20)

# Función para abrir la ventana secundaria
def abrir_reconocimiento_facial():
    nueva_ventana = ModernFaceApp(master=ventana)

def abrir_tablas():
    app = ReportApp()
    app.mainloop() 

# Función para abrir la ventana de reportes
def abrir_reportes():
    try:
        import sqlite3
        conn = sqlite3.connect("./pyme_san_ignacio.db")
        cursor = conn.cursor()
        DashboardsApp(cursor)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir la ventana de reportes: {e}")


# Botón para abrir el reconocimiento facial
boton_reconocimiento = tk.Button(ventana, text="Reconocimiento Facial", command=abrir_reconocimiento_facial, width=25, height=2)
boton_reconocimiento.pack(pady=5)

boton_tablas = tk.Button(ventana, text="Tablas Referenciales", command=abrir_tablas, width=25, height=2)
boton_tablas.pack(pady=5)

# Botón para abrir la ventana de dashboards
boton_reportes = tk.Button(ventana, text="Reportes y Dashboards", command=abrir_reportes, width=25, height=2)
boton_reportes.pack(pady=5)

if __name__ == "__main__":
    ventana.mainloop()
