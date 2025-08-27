from enum import Enum
import tkinter as tk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd

PYME_EXCEL = "pyme.xlsx"

class PlotType(str, Enum):
    LINEA = "Gráfico de líneas"
    BARRA = "Gráfico de barras"

class PymeData(str, Enum):
    #TODO poner los adecuados cuando esté hecho el excel
    PRODUCCION      = "Producción"
    PERDIDAS        = "Pérdidas"
    GANANCIAS       = "Ganancias"
    VENTAS          = "Ventas"
    PRECIOS_INSUMOS = "Precios Insumos"
    STOCK           = "Stock"

class PymeDataVisualizer:

    # El programa se rompe si se cierra el programa con Ctrl+C desde terminal en vez de cerrando la ventana
    # No sé cómo arreglar eso
    def on_close(self):
        try:
            plt.close(self.fig)
        finally:
            self.root.destroy()

    def __init__(self, root):
        self.root = root
        self.root.title = "Visualización de datos de la PYME"
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.plot_type_var = tk.StringVar(value=PlotType.LINEA)
        self.pymedata_var = tk.StringVar(value=PymeData.PRODUCCION)

        menu_plot_type = tk.OptionMenu(self.root, self.plot_type_var, *(ptype for ptype in PlotType), command=self.show_graph_with_new_plot_type)
        menu_plot_type.pack(padx=10, pady=10)

        menu_choose_data = tk.OptionMenu(self.root, self.pymedata_var, *(pdata for pdata in PymeData), command=self.update_graph_with_new_data)
        menu_choose_data.pack(padx=10, pady=10)

        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.widget = self.canvas.get_tk_widget()
        self.widget.pack(padx=10, pady=10)

        self.excel_file = pd.ExcelFile(PYME_EXCEL)
        self.df = None

        self.current_x = None
        self.current_y = None
        self.current_label = None

    def show_graph_with_new_plot_type(self, ptype):
        #if self.df is None:
        #    return

        # Nomas para cuando no hay data definida yet
        if self.df is None or self.current_x is None or self.current_y is None: 
            self.ax.clear()
            self.ax.set_xlabel("Unknown")
            self.ax.set_ylabel("Unknown")
            self.canvas.draw()
            print("NO DATA")
            return 

        self.ax.clear()
        x_values = self.df[self.current_x]
        y_values = self.df[self.current_y]

        match ptype:
            case PlotType.LINEA.value:

                self.ax.plot(x_values,y_values, label=self.current_label)
                for x,y in zip(x_values, y_values):
                    self.ax.text(x,y,str(y))
            case PlotType.BARRA.value:
                bars = self.ax.bar(x_values, y_values, label=self.current_label)
                self.ax.bar_label(bars, label_type="center")
        self.ax.set_xlabel(self.current_x)
        self.ax.set_ylabel(self.current_y)
#       self.ax.legend()
#        self.fig.tight_layout()
        self.canvas.draw()

    def update_graph_with_new_data(self, pymedata):
        match pymedata:
            case PymeData.PRODUCCION:
                self.set_graph_produccion()
            case PymeData.GANANCIAS:
                self.set_graph_ganancias()
            case PymeData.PERDIDAS:
                self.set_graph_perdidas()
            case PymeData.VENTAS:
                self.set_graph_ventas()
            case PymeData.PRECIOS_INSUMOS:
                self.set_graph_precios_insumos()
            case PymeData.STOCK:
                self.set_graph_stock()

        self.show_graph_with_new_plot_type(self.plot_type_var.get())

    def _test_reset_graph(self):
        self.current_x = None
        self.current_y = None

    def set_graph_produccion(self):
        self._test_reset_graph()

    def set_graph_ganancias(self):
        self._test_reset_graph()

    def set_graph_perdidas(self):
        self._test_reset_graph()

    def set_graph_ventas(self):
        self._test_reset_graph()

    def set_graph_stock(self):
        self.df = pd.read_excel(self.excel_file, sheet_name="Empleados", header=10, usecols="A:C",nrows=6)
        self.current_x = self.df.columns[1]
        self.current_y = self.df.columns[2]
        self.current_label = "Stock"

    def set_graph_precios_insumos(self):
        self.df = pd.read_excel(self.excel_file, sheet_name="Insumos")
        self.current_x = self.df.columns[1]
        self.current_y = self.df.columns[3]
        self.current_label = "Insumos"

def main():
    root = tk.Tk()
    visualizer = PymeDataVisualizer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
