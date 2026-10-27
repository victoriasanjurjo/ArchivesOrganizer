# ArchivesOrganizer

**ArchivesOrganizer** es una aplicación de escritorio diseñada para clasificar y organizar archivos de forma automatizada, segura y **100% local**. Posee una interfaz gráfica moderna, sobria y monocromática desarrollada con **PySide6 (Qt)**, garantizando privacidad absoluta al operar sin conexiones a internet ni telemetría externa.

---

## Características Principales

- **Operación 100% Local y Privada:** Todo el escaneo y reubicación de archivos se ejecuta en el almacenamiento local del equipo sin enviar información a ningún servidor.
- **Múltiples Criterios de Organización:**
  - **Por Categoría:** Agrupa por propósito semántico (*Documentos*, *Imágenes*, *Videos*, *Audio*, *Comprimidos*, *Programación*, *Ejecutables e Instaladores*, *Otros*).
  - **Por Extensión:** Crea carpetas basadas en la extensión exacta del archivo (ej. `PDF/`, `PNG/`, `DOCX/`).
  - **Por Fecha (Año/Mes):** Organiza según la fecha de modificación en carpetas temporales (ej. `2026-10/`).
- **Modo Simulación / Vista Previa (Dry Run):** Inspecciona visualmente las operaciones proyectadas antes de realizar cualquier cambio físico en el disco.
- **Prevención de Sobreescritura (Resolución de Colisiones):** Si ya existe un archivo con el mismo nombre en la carpeta de destino, se añade automáticamente un sufijo correlativo incremental (ej. `documento (1).pdf`).
- **Soporte de Escaneo Recursivo:** Opción para organizar solo la raíz de la carpeta seleccionada o procesar también las subcarpetas.
- **Auditoría y Registro en Tiempo Real:** Consola de eventos integrada con registro cronológico de cada operación realizada.
- **Estética Monocromática Profesional:** Interfaz en escala de grises y carbón de alto contraste y legibilidad.

---

## Arquitectura del Proyecto

```text
ArchivesOrganizer/
├── docs/                        # Documentación técnica, decisiones y bitácora
│   ├── architecture.md          # Arquitectura técnica y justificaciones
│   └── changelog.md             # Registro de modificaciones y bitácora (en inglés claro)
├── tests/                       # Pruebas unitarias automatizadas
│   ├── test_organizer.py        # Pruebas estándar de lógica y simulación
│   └── test_edge_cases.py       # Pruebas de casos extremos (nulos, gigantes, etc.)
├── config/                      # Ajustes y configuración de categorías
│   └── default_config.py
├── assets/                      # Íconos y recursos visuales (.ico, .png)
│   ├── icon.ico
│   └── icon.png
├── outputs/                     # Directorio de salida
├── src/                         # Código fuente de la aplicación
│   ├── __init__.py
│   ├── organizer.py             # Motor lógico de organización de archivos
│   ├── generate_assets.py       # Generador de íconos de la app
│   └── ui/                      # Módulo de interfaz gráfica PySide6
│       ├── __init__.py
│       ├── main_window.py       # Ventana principal e integración multihilo
│       └── styles.py            # Hoja de estilos QSS monocromática
├── .gitignore                   # Exclusiones de control de versiones
├── requirements.txt             # Dependencias exactas instaladas
├── LICENSE.txt                  # Licencia de software MIT
├── README.md                    # Manual y documentación general
└── main.py                      # Punto de entrada de la aplicación
```

---

## Pruebas Unitarias Automatizadas

El proyecto cuenta con una cobertura integral de pruebas que abarca el flujo nominal y la tolerancia a anomalías del entorno:

```bash
# Ejecutar todas las pruebas unitarias (estándar y casos extremos)
python -m unittest discover tests

# Ejecutar específicamente la suite de casos extremos
python -m unittest tests/test_edge_cases.py
```

---

## Versión y Distribución

Actualmente se encuentra disponible la **primera versión (v1.0.0)** de la aplicación provista directamente como ejecutable listo para usar:

- **Ejecutable compilado:** `dist/ArchivesOrganizer/ArchivesOrganizer.exe`

No requiere instalaciones adicionales ni ejecución mediante consola; basta con iniciar el archivo `.exe` para acceder a la interfaz gráfica.

---

## Licencia

Este proyecto está distribuido bajo la licencia **MIT**. Para más detalles, consulta el archivo [LICENSE.txt](file:///d:/Proyectos/ArchivesOrganizer/LICENSE.txt).
