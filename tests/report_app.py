# report_app.py
# Pantalla de reportes (testing): visualiza tablas de la base y permite filtrar/exportar asistencias.
# Requiere: customtkinter (UI). Usa sqlite3 estándar (no necesita pandas).
# Ejecutar: python report_app.py

import csv
import sqlite3
from tkinter import ttk, messagebox, filedialog

try:
    import customtkinter as ctk
except ImportError as e:
    raise SystemExit("Falta 'customtkinter'. Instalá con: pip install customtkinter") from e

import utils_db  # Usa PYME_DB y ensure_db_seeded()


DB_PATH = utils_db.PYME_DB


def safe_query(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall(), [d[0] for d in cur.description]


class TableView(ctk.CTkFrame):
    """Wrapper para Treeview + barra de desplazamiento."""
    def __init__(self, master, height=320, **kwargs):
        super().__init__(master, **kwargs)
        self.tree = ttk.Treeview(self, show="headings", height=height)
        self.scroll_y = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.scroll_x = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        self.scroll_y.grid(row=0, column=1, sticky="ns")
        self.scroll_x.grid(row=1, column=0, sticky="we")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def set_data(self, columns, rows):
        self.tree.delete(*self.tree.get_children())
        self.tree["columns"] = columns
        for c in columns:
            self.tree.heading(c, text=c)
            self.tree.column(c, width=140, anchor="center")
        for r in rows:
            self.tree.insert("", "end", values=r)

    def export_csv(self, path):
        cols = self.tree["columns"]
        rows = [self.tree.item(i, "values") for i in self.tree.get_children()]
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow(r)


class ReportApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Reportes - Asistencias (Testing)")
        self.geometry("1000x680")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Asegurar DB lista
        try:
            utils_db.ensure_db_seeded()
        except Exception as e:
            messagebox.showwarning("DB", f"No se pudo inicializar la base: {e}")

        # Layout principal
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        tabs = ctk.CTkTabview(self)
        tabs.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)
        self.tab_asist = tabs.add("Asistencias")
        self.tab_emps = tabs.add("Empleados")
        self.tab_rost = tabs.add("Rostros")
        self.tab_hora = tabs.add("Horarios")

        # --- Tab Asistencias ---
        self._build_asistencias_tab(self.tab_asist)

        # --- Tab Empleados ---
        self.table_emps = TableView(self.tab_emps, height=20)
        self.table_emps.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab Rostros ---
        self.table_rost = TableView(self.tab_rost, height=20)
        self.table_rost.pack(fill="both", expand=True, padx=10, pady=10)

        # --- Tab Horarios ---
        self.table_hora = TableView(self.tab_hora, height=20)
        self.table_hora.pack(fill="both", expand=True, padx=10, pady=10)

        # Cargar datos iniciales
        self.refresh_all_tables()

    # ---------------- Asistencias ----------------
    def _build_asistencias_tab(self, parent):
        # Filtros
        filt = ctk.CTkFrame(parent)
        filt.pack(fill="x", padx=10, pady=(10, 0))

        ctk.CTkLabel(filt, text="Legajo").grid(row=0, column=0, padx=6, pady=6, sticky="w")
        self.entry_leg = ctk.CTkEntry(filt, width=100, placeholder_text="(opcional)")
        self.entry_leg.grid(row=0, column=1, padx=6, pady=6)

        ctk.CTkLabel(filt, text="Desde (YYYY-MM-DD)").grid(row=0, column=2, padx=6, pady=6)
        self.entry_from = ctk.CTkEntry(filt, width=140, placeholder_text="2025-01-01")
        self.entry_from.grid(row=0, column=3, padx=6, pady=6)

        ctk.CTkLabel(filt, text="Hasta (YYYY-MM-DD)").grid(row=0, column=4, padx=6, pady=6)
        self.entry_to = ctk.CTkEntry(filt, width=140, placeholder_text="2025-12-31")
        self.entry_to.grid(row=0, column=5, padx=6, pady=6)

        ctk.CTkButton(filt, text="Buscar", command=self.run_asist_query).grid(row=0, column=6, padx=8, pady=6)
        ctk.CTkButton(filt, text="Exportar CSV", command=self.export_asist).grid(row=0, column=7, padx=8, pady=6)
        ctk.CTkButton(filt, text="Limpiar", command=self.clear_filters).grid(row=0, column=8, padx=8, pady=6)

        # Tabla
        self.table_asist = TableView(parent, height=22)
        self.table_asist.pack(fill="both", expand=True, padx=10, pady=10)

        # Tip
        tip = ctk.CTkLabel(parent, text="Tip: dejá filtros vacíos para ver todo. La columna 'salida' puede ser NULL si el empleado sigue trabajando.", wraplength=900, justify="left")
        tip.pack(fill="x", padx=10, pady=(0, 10))

    def clear_filters(self):
        self.entry_leg.delete(0, "end")
        self.entry_from.delete(0, "end")
        self.entry_to.delete(0, "end")
        self.run_asist_query()

    def export_asist(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], title="Guardar como...")
        if not path:
            return
        try:
            self.table_asist.export_csv(path)
            messagebox.showinfo("Exportar", f"Archivo guardado en: {path}")
        except Exception as e:
            messagebox.showerror("Exportar", f"No se pudo exportar: {e}")

    def run_asist_query(self):
        # Construir WHERE dinámico
        wh = []
        params = []

        leg = self.entry_leg.get().strip()
        if leg:
            if leg.isdigit():
                wh.append("a.legajo_empleado = ?")
                params.append(int(leg))
            else:
                messagebox.showwarning("Filtro", "El legajo debe ser numérico.")
                return

        date_from = self.entry_from.get().strip()
        if date_from:
            wh.append("date(a.entrada) >= date(?)")
            params.append(date_from)

        date_to = self.entry_to.get().strip()
        if date_to:
            wh.append("date(a.entrada) <= date(?)")
            params.append(date_to)

        where_sql = ("WHERE " + " AND ".join(wh)) if wh else ""
        sql = f"""\
        SELECT a.legajo_empleado AS legajo,
               e.nombre,
               e.puesto,
               e.area,
               a.entrada,
               a.salida
        FROM asistencia_empleado a
        LEFT JOIN empleados e ON e.legajo = a.legajo_empleado
        {where_sql}
        ORDER BY a.entrada DESC
        """
        rows, cols = safe_query(sql, tuple(params))
        self.table_asist.set_data(cols, rows)

    # ---------------- Otras tablas ----------------
    def refresh_all_tables(self):
        # Asistencias inicial (sin filtros)
        self.run_asist_query()

        # Empleados
        rows, cols = safe_query("SELECT legajo, nombre, puesto, area FROM empleados ORDER BY legajo ASC")
        self.table_emps.set_data(cols, rows)

        # Rostros
        rows, cols = safe_query("SELECT archivo, legajo FROM rostros ORDER BY archivo ASC")
        self.table_rost.set_data(cols, rows)

        # Horarios
        rows, cols = safe_query("SELECT legajo_empleado, hora_entrada, hora_salida FROM horarios_empleados ORDER BY legajo_empleado ASC")
        self.table_hora.set_data(cols, rows)


if __name__ == '__main__':
    app = ReportApp()
    app.mainloop()
