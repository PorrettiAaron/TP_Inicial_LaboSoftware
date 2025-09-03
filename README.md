# 🧑‍💻 Proyecto de Reconocimiento Facial con Interfaz Gráfica

Aplicación en **Python 3.11** con **Tkinter** para reconocimiento facial:  
- 📸 Captura rostros desde webcam.  
- 🖼️ Compara imágenes contra una base de datos.  
- 👤 Permite agregar usuarios (rostros) a la base.  
- 🛠️ Administra encodings (datos biométricos).

El proyecto está configurado con **`pyproject.toml`** (PEP 621), el estándar moderno para empaquetado en Python.  
Esto permite instalarlo fácilmente con `pip install .`.

---

## 📋 Requisitos

- **Python 3.11** (⚠️ obligatorio: por compatibilidad con `dlib`).
- Sistema operativo: Windows 10/11 (probado) o Linux/Mac con build de `dlib` compatible.
- [Git](https://git-scm.com/) (opcional, para clonar el repositorio).

---

## ⚙️ Configuración del entorno

### 1. Instalar Python 3.11
En Windows:
```bash
winget install python.python.3.11
```

Verificar:
```bash
py -3.11 --version
```

### 2. Crear entorno virtual
```bash
py -3.11 -m venv venv_proyecto
```

### 3. Activar entorno virtual
- Windows (CMD o PowerShell):
  ```bash
  venv_proyecto\Scripts\activate
  ```
- Linux/Mac:
  ```bash
  source venv_proyecto/bin/activate
  ```

### 4. Instalar dependencias del proyecto
Como este proyecto usa `pyproject.toml`, basta con:
```bash
pip install -e .
```

Esto instalará:
- `opencv-python`
- `numpy`
- `face_recognition`
- `dlib` (desde wheel precompilado para Python 3.11 en Windows)
- y cualquier otra dependencia listada en el `pyproject.toml`.

### 5. Desactivar entorno virtual
```bash
deactivate
```

---

## ▶️ Uso de la aplicación

1. Activar el entorno virtual:
   ```bash
   venv_proyecto\Scripts\activate
   ```

2. Ejecutar la app gráfica:
   ```bash
   python app.py
   ```

3. Funcionalidades en la interfaz:
   - **Agregar usuarios** → selecciona imágenes y las guarda en `tests/db_images/`.
   - **Captar rostro con webcam** → abre la cámara y compara rostros en vivo.
   - **Captar rostro desde imagen** → permite comparar una foto con la base.
   - **Regenerar encodings** → recalcula los datos de reconocimiento de toda la base.
   - **Detectar imágenes problemáticas** → lista archivos sin encodings válidos.

👉 Para salir de la ventana de la webcam, presioná **q**.

---

## 🧪 Correr tests

```bash
venv_proyecto\Scripts\activate
python -m unittest tests\file.py
deactivate
```

---

## 📂 Estructura del proyecto

```
.
├─ app.py               # Punto de entrada de la aplicación
├─ gui.py               # Interfaz gráfica (Tkinter)
├─ actions.py           # Lógica de la aplicación
├─ helpers.py           # Funciones auxiliares
├─ pyproject.toml       # Configuración del paquete y dependencias
├─ src/
│  └─ utils_recognition.py
└─ tests/
   ├─ db_images/        # Carpeta de imágenes de usuarios
   └─ img_test.jpg      # Imagen de prueba (opcional)
```

---

## 🙌 Notas finales

- Conservá el archivo **`pyproject.toml`** → es el estándar moderno y permite compartir fácilmente el proyecto.  
- Si alguna imagen no genera encoding, usá el botón **“Detectar imágenes problemáticas”** en la interfaz.  
- Para publicar en **PyPI** más adelante, ya tenés lo esencial en `pyproject.toml`.

---
