# Arquitectura Técnica y Bitácora de Decisiones - ArchivesOrganizer

## 1. Visión General del Proyecto
**ArchivesOrganizer** es una herramienta de escritorio 100% local desarrollada en Python y PySide6 (Qt) diseñada para clasificar y organizar archivos de forma automatizada y segura. No requiere conexión a internet ni envía telemetría.

## 2. Decisiones Técnicas y Justificación

### 2.1 Interfaz Gráfica: PySide6 (Qt for Python)
- **Motivo de elección:** PySide6 ofrece rendimiento nativo en Windows, gestión de hilos mediante `QThread`/`Signal` para no congelar la GUI durante operaciones intensivas de E/S de disco, y soporte para estilos avanzados mediante Qt Style Sheets (QSS).
- **Estética Monocromática:** Se implementa una paleta sobria en escala de grises / negro y blanco con acentos neutros, asegurando contraste accesible, legibilidad técnica y aspecto moderno sin saturación visual.

### 2.2 Modalidades de Organización Soportadas
1. **Por Categoría:** Agrupa los archivos según su propósito semántico (Documentos, Imágenes, Videos, Audio, Comprimidos, Código, Ejecutables, Otros).
2. **Por Extensión Exacta:** Crea una carpeta por cada extensión encontrada (ej. `pdf/`, `docx/`, `png/`).
3. **Por Fecha (Año/Mes):** Organiza según la fecha de última modificación del archivo en carpetas estructuradas como `YYYY/YYYY-MM/` o `YYYY-MM/`.

### 2.3 Seguridad y Prevención de Pérdida de Datos
- **Modo Vista Previa / Simulación (Dry Run):** Permite al usuario escanear la carpeta y ver la tabla de origen -> destino proyectado antes de alterar cualquier archivo en disco.
- **Resolución de Colisiones:** Si un archivo con el mismo nombre ya existe en la carpeta de destino, se añade automáticamente un sufijo numérico incremental (ej. `reporte (1).pdf`), impidiendo sobreescrituras accidentales.
- **Operación Local Atómica:** Las operaciones utilizan `shutil.move` / `os.replace` controlando excepciones por permisos, bloqueos de archivo o rutas largas.
- **Registro de Auditoría (Logging):** Se emiten registros de cada acción realizada en la consola de la app y opcionalmente en un log local.

### 2.4 Empaquetado: PyInstaller
- Se compila en modo `--windowed` (sin ventana de consola de comandos emergente).
- Se genera un ícono personalizado representativo en `assets/icon.ico` y `assets/icon.png` incluido en el binario final.

## 3. Estructura de Módulos
- `main.py`: Punto de entrada de la aplicación.
- `src/organizer.py`: Lógica del motor de organización (escaneo, clasificación, simulación y ejecución).
- `src/ui/`: Componentes de interfaz gráfica, ventana principal y estilos QSS monocromáticos.
- `config/`: Configuración de categorías de archivos y metadatos.
- `assets/`: Ícono de la aplicación y recursos visuales.
- `tests/`: Pruebas unitarias de clasificación y resolución de colisiones.
- `docs/`: Documentación técnica y bitácora.
