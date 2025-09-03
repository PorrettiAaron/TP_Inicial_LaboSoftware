# 🧑‍💻 Proyecto de Reconocimiento Facial con Interfaz Gráfica

Este proyecto implementa una aplicación en **Python 3.11** para **reconocimiento facial** con interfaz gráfica (Tkinter).  
Permite:
- Agregar imágenes de usuarios a una base de datos.
- Capturar rostros en vivo desde la **webcam**.
- Comparar rostros desde imágenes contra la base existente.
- Administrar encodings (datos biométricos).

---

## 📋 Prerrequisitos

Antes de comenzar, asegurate de tener instalado:

- **Windows 10/11** (o Linux/Mac con Python 3.11).
- [Python 3.11](https://www.python.org/downloads/release/python-3110/) (específicamente esta versión, por compatibilidad con `dlib`).
- **Git** (opcional, para clonar el repositorio).

⚠️ No uses Python 3.12 o 3.13: los wheels de `dlib` disponibles para esas versiones no funcionan correctamente en este proyecto.

---

## ⚙️ Configuración del entorno

Vamos a crear un entorno virtual llamado `venv_proyecto` para aislar las dependencias.  
Esto evita conflictos con otros proyectos y es la forma recomendada de trabajar en Python.

### 1. Instalar Python 3.11 (Windows con winget)
```bash
winget install python.python.3.11
```

Verificá la instalación:
```bash
py -3.11 --version
```

### 2. Crear entorno virtual
```bash
py -3.11 -m venv venv_proyecto
```

Esto genera la carpeta `venv_proyecto/` en el proyecto (ya está en el `.gitignore`).

### 3. Activar entorno virtual
En **Windows (CMD o PowerShell)**:
```bash
venv_proyecto\Scripts\activate
```

En **Linux/Mac**:
```bash
source venv_proyecto/bin/activate
```

Cuando esté activo, verás el prefijo `(venv_proyecto)` en la consola.

### 4. Instalar dependencias
Con el entorno activado, instalá las dependencias necesarias:

```bash
pip install -r requirements.txt
```

Si no tenés un `requirements.txt`, podés instalar manualmente:

```bash
pip install opencv-python dlib face-recognition
```

*(Tkinter viene incluido con Python en la mayoría de instalaciones, no requiere instalación adicional).*

### 5. Desactivar entorno virtual
Cuando termines de usarlo:
```bash
deactivate
```

---

## ▶️ Ejecutar la aplicación

1. Activar el entorno virtual:
   ```bash
   venv_proyecto\Scripts\activate
   ```

2. Ejecutar la aplicación principal:
   ```bash
   python app_main.py
   ```

3. Funcionalidades disponibles en la interfaz:
   - **Agregar usuarios**: Selecciona imágenes de rostros y guárdalas en `tests/db_images/`.
   - **Captar rostro con webcam**: Abre la cámara y compara rostros detectados con la base.
   - **Captar rostro desde imagen**: Elegí una imagen para compararla contra la base.
   - **Regenerar encodings**: Recalcula los datos biométricos de todas las imágenes.
   - **Detectar imágenes problemáticas**: Lista archivos que no generaron un encoding válido.

Para cerrar la ventana de la webcam, presioná la tecla **q**.

---

## 🧪 Ejecutar tests

Podés correr los tests incluidos en la carpeta `tests/` con:

```bash
venv_proyecto\Scripts\activate
python -m unittest tests\file.py
deactivate
```

---

## 📂 Estructura del proyecto

```
.
├─ app_main.py          # Punto de entrada de la aplicación
├─ gui.py               # Interfaz gráfica (Tkinter)
├─ actions.py           # Lógica de las acciones de la GUI
├─ helpers.py           # Funciones auxiliares y configuraciones
├─ src/
│  └─ utils_recognition.py
└─ tests/
   ├─ db_images/        # Carpeta con imágenes de usuarios registrados
   └─ img_test.jpg      # Imagen de prueba (opcional)
```

---

## 🙌 Notas finales

- Si la aplicación marca errores al comparar, revisá que las imágenes en `tests/db_images/` contengan rostros claros y frontales.  
- El botón **“Detectar imágenes problemáticas”** ayuda a identificar archivos que no generaron encodings válidos.  
- Si querés cambiar la carpeta de base de datos, podés editar `DATABASE_PATH` en `helpers.py`.

---
