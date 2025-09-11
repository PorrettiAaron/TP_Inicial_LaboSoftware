import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar funciones de tu utils_db
from src.utils_db import (
    get_productos_finales,
    get_insumos,
    get_productos_por_kg,
    get_tiempos_produccion,
    get_desperdicio,
    get_stock_materia_prima
)

class DashboardsApp(tk.Toplevel):
    def __init__(self, cursor):
        super().__init__()
        self.title("Reportes y Dashboards")
        self.geometry("900x600")
        self.cursor = cursor

        self.tab_control = ttk.Notebook(self)
        self.tab_control.pack(expand=1, fill="both")

        self.tab_productos_finales = ttk.Frame(self.tab_control)
        self.tab_insumos = ttk.Frame(self.tab_control)
        self.tab_desperdicio = ttk.Frame(self.tab_control)
        self.tab_stock = ttk.Frame(self.tab_control)

        self.tab_control.add(self.tab_productos_finales, text='Productos Finales')
        self.tab_control.add(self.tab_insumos, text='Insumos')
        self.tab_control.add(self.tab_desperdicio, text='Desperdicio')
        self.tab_control.add(self.tab_stock, text='Stock Materia Prima')

        self.mostrar_productos_finales()
        self.mostrar_insumos()
        self.mostrar_desperdicio()
        self.mostrar_stock()

    def _crear_tabla(self, tab, df):
        tree = ttk.Treeview(tab, columns=list(df.columns), show='headings')
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        tree.pack(expand=True, fill='both')
        return tree

    def _crear_grafico(self, tab, df, x, y, color='blue', titulo=''):
        if df.empty:
            print(f"⚠️ No hay datos para graficar: {titulo}")
            messagebox.showinfo("Sin datos", f"No hay datos disponibles para el gráfico: {titulo}")
            return
        try:
            df[y] = pd.to_numeric(df[y], errors='coerce')
            fig, ax = plt.subplots(figsize=(6, 3))
            df.plot(kind='bar', x=x, y=y, ax=ax, color=color)
            ax.set_title(titulo)
            canvas = FigureCanvasTkAgg(fig, master=tab)
            canvas.draw()
            canvas.get_tk_widget().pack(pady=10)
        except Exception as e:
            print(f"❌ Error al crear gráfico '{titulo}':", repr(e))
            messagebox.showerror("Error", f"No se pudo generar el gráfico: {titulo}")

    def mostrar_productos_finales(self):
        try:
            print("🔍 Cargando productos finales...")
            data = get_productos_finales(self.cursor)
            print("📦 Datos obtenidos:", data)
            df = pd.DataFrame(data, columns=[
                'codigo', 'producto', 'presentacion', 'precio_venta',
                'costo_unitario', 'stock', 'estimado_ventas_mensuales'
            ])
            df.columns = ['Código', 'Producto', 'Presentación', 'Precio Venta', 'Costo', 'Stock', 'Estimado Ventas']
            print("📊 DataFrame creado:", df.head())
            self._crear_tabla(self.tab_productos_finales, df)
            self._crear_grafico(self.tab_productos_finales, df, x='Producto', y='Estimado Ventas', color='green', titulo='Estimado Ventas Mensuales')
        except Exception as e:
            print("❌ Error en mostrar_productos_finales:", repr(e))
            messagebox.showerror("Error", f"No se pudieron cargar productos finales: {e}")

    def mostrar_insumos(self):
        try:
            print("🔍 Cargando insumos...")
            data = get_insumos(self.cursor)
            print("📦 Datos obtenidos:", data)
            df = pd.DataFrame(data, columns=[
                'codigo', 'insumo', 'proveedor', 'costo_unitario', 'unidad'
            ])
            df.columns = ['Código', 'Insumo', 'Proveedor', 'Costo', 'Unidad']
            print("📊 DataFrame creado:", df.head())
            self._crear_tabla(self.tab_insumos, df)
        except Exception as e:
            print("❌ Error en mostrar_insumos:", repr(e))
            messagebox.showerror("Error", f"No se pudieron cargar insumos: {e}")

    def mostrar_desperdicio(self):
        try:
            print("🔍 Cargando desperdicio...")
            data = get_desperdicio(self.cursor)
            print("📦 Datos obtenidos:", data)
            df = pd.DataFrame(data, columns=[
                'total_inicial_kg', 'producto_final_obtenido_kg', 'desperdicio_kg',
                'desperdicio_pct', 'desperdicio_reutilizable_pct', 'desperdicio_real_pct', 'producto'
            ])
            df.columns = ['Total Inicial', 'Obtenido', 'Desperdicio kg', 'Desperdicio %', 'Reutilizable %', 'Real %', 'Producto']
            print("📊 DataFrame creado:", df.head())
            self._crear_tabla(self.tab_desperdicio, df)
            self._crear_grafico(self.tab_desperdicio, df, x='Producto', y='Desperdicio %', color='red', titulo='Porcentaje de Desperdicio')
        except Exception as e:
            print("❌ Error en mostrar_desperdicio:", repr(e))
            messagebox.showerror("Error", f"No se pudieron cargar datos de desperdicio: {e}")

    def mostrar_stock(self):
        try:
            print("🔍 Cargando stock de materia prima...")
            data = get_stock_materia_prima(self.cursor)
            print("📦 Datos obtenidos:", data)
            df = pd.DataFrame(data, columns=['codigo', 'nombre', 'stock'])
            df.columns = ['Código', 'Nombre', 'Stock']
            print("📊 DataFrame creado:", df.head())
            self._crear_tabla(self.tab_stock, df)
            self._crear_grafico(self.tab_stock, df, x='Nombre', y='Stock', color='orange', titulo='Stock de Materia Prima')
        except Exception as e:
            print("❌ Error en mostrar_stock:", repr(e))
            messagebox.showerror("Error", f"No se pudieron cargar datos de stock: {e}")
