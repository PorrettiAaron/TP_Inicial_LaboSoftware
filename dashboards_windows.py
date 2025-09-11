import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Importar funciones de tu utils_db que está en src
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
        # Estilo más compacto para Treeview
        style = ttk.Style()
        style.configure("Treeview", rowheight=20, font=("Arial", 9))  # filas más cortas y letra más pequeña

        tree = ttk.Treeview(tab, columns=list(df.columns), show='headings')
        for col in df.columns:
            tree.heading(col, text=col)
            tree.column(col, width=70, anchor='center')  # menos ancho
        for _, row in df.iterrows():
            tree.insert("", "end", values=list(row))
        tree.pack(expand=False, fill='x', pady=5)  # menos alto
        return tree


    def _crear_grafico(self, tab, df, x, y, color='blue', titulo=''):
        if df.empty:
            messagebox.showinfo("Sin datos", f"No hay datos disponibles para el gráfico: {titulo}")
            return

        df[y] = pd.to_numeric(df[y], errors='coerce')
        fig, ax = plt.subplots(figsize=(4, 2.5))  # ancho y alto reducidos
        df.plot(kind='bar', x=x, y=y, ax=ax, color=color)

        ax.set_title(titulo, fontsize=10)  # título más pequeño
        ax.set_ylabel(y, fontsize=8)
        ax.set_xlabel(x, fontsize=8)
        plt.xticks(rotation=30, ha='right', fontsize=8)
        plt.yticks(fontsize=8)
        plt.tight_layout(pad=1)

        canvas = FigureCanvasTkAgg(fig, master=tab)
        canvas.draw()
        canvas.get_tk_widget().pack(side='bottom', fill='x', expand=False, pady=5)


    def mostrar_productos_finales(self):
        try:
            data = get_productos_finales(self.cursor)
            df = pd.DataFrame(data, columns=[
                'codigo', 'producto', 'presentacion', 'precio_venta',
                'costo_unitario', 'stock', 'estimado_ventas_mensuales'
            ])
            df.columns = ['Código', 'Producto', 'Presentación', 'Precio Venta', 'Costo', 'Stock', 'Estimado Ventas']
            self._crear_tabla(self.tab_productos_finales, df)
            self._crear_grafico(self.tab_productos_finales, df, x='Producto', y='Estimado Ventas', color='green', titulo='Estimado Ventas Mensuales')
        except Exception as e:
            print("Error en mostrar_productos_finales:", e)
            messagebox.showerror("Error", f"No se pudieron cargar productos finales: {e}")

    def mostrar_insumos(self):
        try:
            data = get_insumos(self.cursor)
            df = pd.DataFrame(data, columns=[
            'codigo', 'insumo', 'proveedor', 'costo_unitario', 'unidad'
            ])
            df.columns = ['Código', 'Insumo', 'Proveedor', 'Costo', 'Unidad']
        
            # Crear tabla
            self._crear_tabla(self.tab_insumos, df)
        
            # --- CREAR GRÁFICO ---
            fig, ax = plt.subplots(figsize=(6, 4))
            df.plot(kind='bar', x='Insumo', y='Costo', ax=ax, color='skyblue')
            ax.set_title("Costo por Insumo")
            ax.set_ylabel("Costo Unitario")
            ax.set_xlabel("Insumo")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            # Insertar gráfico en Tkinter
            canvas = FigureCanvasTkAgg(fig, master=self.tab_insumos)
            canvas.draw()
            canvas.get_tk_widget().pack(side='bottom', fill='both', expand=True)
        
        except Exception as e:
            print("Error en mostrar_insumos:", e)
            messagebox.showerror("Error", f"No se pudieron cargar insumos: {e}")


    def mostrar_desperdicio(self):
        try:
            data = get_desperdicio(self.cursor)
            df = pd.DataFrame(data, columns=[
                'total_inicial_kg', 'producto_final_obtenido_kg', 'desperdicio_kg',
                'desperdicio_pct', 'desperdicio_reutilizable_pct', 'desperdicio_real_pct', 'producto'
            ])
            df.columns = ['Total Inicial', 'Obtenido', 'Desperdicio kg', 'Desperdicio %', 'Reutilizable %', 'Real %', 'Producto']
            self._crear_tabla(self.tab_desperdicio, df)
            self._crear_grafico(self.tab_desperdicio, df, x='Producto', y='Desperdicio %', color='red', titulo='Porcentaje de Desperdicio')
        except Exception as e:
            print("Error en mostrar_desperdicio:", e)
            messagebox.showerror("Error", f"No se pudieron cargar datos de desperdicio: {e}")

    def mostrar_stock(self):
        try:
            data = get_stock_materia_prima(self.cursor)
            df = pd.DataFrame(data, columns=['codigo', 'nombre', 'stock'])
            df.columns = ['Código', 'Nombre', 'Stock']
            self._crear_tabla(self.tab_stock, df)
            self._crear_grafico(self.tab_stock, df, x='Nombre', y='Stock', color='orange', titulo='Stock de Materia Prima')
        except Exception as e:
            print("Error en mostrar_stock:", e)
            messagebox.showerror("Error", f"No se pudieron cargar datos de stock: {e}")