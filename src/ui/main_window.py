"""
Ventana principal de ArchivesOrganizer con GUI PySide6.
Diseño monocromático, visualización de tareas, simulación (Dry Run) y ejecución multihilo.
"""

import os
from datetime import datetime
from typing import List, Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFileDialog, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit,
    QProgressBar, QGroupBox, QMessageBox, QSplitter
)

from config.default_config import APP_TITLE, APP_VERSION
from src.organizer import FileOrganizer, OrganizationMode, FileTask
from src.ui.styles import MONOCHROME_STYLE


def format_size(bytes_val: int) -> str:
    """Convierte bytes a formato humano legible."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


class OrganizerWorker(QThread):
    """Hilo secundario para ejecutar o simular operaciones sin bloquear la interfaz."""
    progress = Signal(int, int, object)  # (current, total, task)
    log_message = Signal(str)
    finished_tasks = Signal(list)

    def __init__(self, organizer: FileOrganizer, tasks: List[FileTask], dry_run: bool):
        super().__init__()
        self.organizer = organizer
        self.tasks = tasks
        self.dry_run = dry_run
        self._is_cancelled = False

    def run(self):
        def on_progress(current: int, total: int, task: FileTask):
            if self._is_cancelled:
                return
            self.progress.emit(current, total, task)
            
            action_name = "SIMULADO" if self.dry_run else task.status.upper()
            if task.status == "Error":
                self.log_message.emit(f"[!] ERROR ({task.filename}): {task.error_message}")
            else:
                dest_sub = os.path.basename(task.target_folder)
                self.log_message.emit(f"[{action_name}] {task.filename} -> /{dest_sub}/")

        self.organizer.execute_tasks(self.tasks, dry_run=self.dry_run, progress_callback=on_progress)
        self.finished_tasks.emit(self.tasks)

    def cancel(self):
        self._is_cancelled = True


class MainWindow(QMainWindow):
    """Ventana principal del organizador de archivos."""

    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.organizer = FileOrganizer()
        self.current_tasks: List[FileTask] = []
        self.worker: Optional[OrganizerWorker] = None

        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION} - 100% Local")
        self.resize(1000, 720)
        self.setMinimumSize(850, 600)

        self._setup_icon()
        self.setStyleSheet(MONOCHROME_STYLE)
        self._build_ui()
        self._log("Sistema inicializado en modo 100% local. Listo para operar.")

    def _setup_icon(self):
        """Asigna el ícono monocromático a la ventana."""
        icon_path_png = os.path.join(self.base_dir, "assets", "icon.png")
        icon_path_ico = os.path.join(self.base_dir, "assets", "icon.ico")
        
        if os.path.exists(icon_path_png):
            self.setWindowIcon(QIcon(icon_path_png))
        elif os.path.exists(icon_path_ico):
            self.setWindowIcon(QIcon(icon_path_ico))

    def _build_ui(self):
        """Construye todos los componentes visuales de la interfaz."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 16, 18, 14)
        main_layout.setSpacing(12)

        # Encabezado minimalista
        header_layout = QHBoxLayout()
        header_title = QLabel(APP_TITLE.upper())
        header_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_title.setStyleSheet("color: #FFFFFF; letter-spacing: 2px;")
        
        header_subtitle = QLabel("•  ORGANIZADOR LOCAL DE ARCHIVOS  •")
        header_subtitle.setStyleSheet("color: #777777; font-size: 11px; font-weight: 500;")
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Panel de Configuración de Rutas y Modos
        config_group = QGroupBox("Configuración de Organización")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Fila Origen
        src_layout = QHBoxLayout()
        src_label = QLabel("Carpeta Origen:")
        src_label.setFixedWidth(130)
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Selecciona el directorio con archivos a organizar...")
        self.src_btn = QPushButton("Examinar...")
        self.src_btn.setFixedWidth(100)
        self.src_btn.clicked.connect(self._browse_source)
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(self.src_btn)
        config_layout.addLayout(src_layout)

        # Fila Destino (Opcional)
        dst_layout = QHBoxLayout()
        dst_label = QLabel("Carpeta Destino:")
        dst_label.setFixedWidth(130)
        self.dst_input = QLineEdit()
        self.dst_input.setPlaceholderText("Mismo directorio origen (por defecto) o selecciona otra carpeta...")
        self.dst_btn = QPushButton("Examinar...")
        self.dst_btn.setFixedWidth(100)
        self.dst_btn.clicked.connect(self._browse_destination)
        dst_layout.addWidget(dst_label)
        dst_layout.addWidget(self.dst_input)
        dst_layout.addWidget(self.dst_btn)
        config_layout.addLayout(dst_layout)

        # Fila de Parámetros y Criterios
        params_layout = QHBoxLayout()
        mode_label = QLabel("Criterio:")
        mode_label.setFixedWidth(130)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(OrganizationMode.CATEGORY.value, OrganizationMode.CATEGORY)
        self.mode_combo.addItem(OrganizationMode.EXTENSION.value, OrganizationMode.EXTENSION)
        self.mode_combo.addItem(OrganizationMode.DATE.value, OrganizationMode.DATE)
        
        self.recursive_chk = QCheckBox("Escanear subcarpetas (recursivo)")
        self.recursive_chk.setChecked(False)

        params_layout.addWidget(mode_label)
        params_layout.addWidget(self.mode_combo, 1)
        params_layout.addSpacing(20)
        params_layout.addWidget(self.recursive_chk)
        params_layout.addStretch()
        config_layout.addLayout(params_layout)

        main_layout.addWidget(config_group)

        # Botones de Acción
        actions_layout = QHBoxLayout()
        self.btn_preview = QPushButton("1. Simular / Vista Previa (Dry Run)")
        self.btn_preview.setObjectName("secondaryButton")
        self.btn_preview.clicked.connect(self._run_simulation)

        self.btn_organize = QPushButton("2. Organizar Archivos (Mover)")
        self.btn_organize.setObjectName("primaryButton")
        self.btn_organize.clicked.connect(self._run_organization)
        self.btn_organize.setEnabled(False)

        self.btn_clear = QPushButton("Limpiar")
        self.btn_clear.setFixedWidth(90)
        self.btn_clear.clicked.connect(self._clear_all)

        actions_layout.addWidget(self.btn_preview)
        actions_layout.addWidget(self.btn_organize)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_clear)
        main_layout.addLayout(actions_layout)

        # Splitter central: Tabla arriba, Consola de logs abajo
        splitter = QSplitter(Qt.Vertical)

        # Tabla de Archivos
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Archivo", "Categoría / Criterio", "Tamaño", "Destino Proyectado", "Estado"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Interactive)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(0, 240)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        splitter.addWidget(table_container)

        # Consola de Eventos y Registro
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        log_label = QLabel("Registro de Actividad (Auditoría Local):")
        log_label.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600;")
        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_container)

        # Ajuste de proporciones en el splitter (65% tabla, 35% log)
        splitter.setSizes([380, 180])
        main_layout.addWidget(splitter, 1)

        # Barra de Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Barra de estado inferior
        self.statusBar().showMessage("Listo")

    def _browse_source(self):
        """Selecciona el directorio origen."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Origen")
        if path:
            self.src_input.setText(os.path.normpath(path))
            self._log(f"Origen seleccionado: {path}")

    def _browse_destination(self):
        """Selecciona el directorio destino opcional."""
        path = QFileDialog.getExistingDirectory(self, "Seleccionar Carpeta Destino")
        if path:
            self.dst_input.setText(os.path.normpath(path))
            self._log(f"Destino personalizado seleccionado: {path}")

    def _log(self, text: str):
        """Escribe una línea en la consola de eventos con marca de tiempo."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{ts}] {text}")

    def _run_simulation(self):
        """Escanea los archivos y simula la organización (Dry Run)."""
        src = self.src_input.text().strip()
        if not src or not os.path.isdir(src):
            QMessageBox.warning(self, "Ruta no válida", "Por favor selecciona un directorio origen válido.")
            return

        dst = self.dst_input.text().strip() or src
        mode = self.mode_combo.currentData()
        recursive = self.recursive_chk.isChecked()

        self._log(f"Iniciando escaneo en modo '{mode.value}' (Recursivo: {recursive})...")
        self.statusBar().showMessage("Escaneando archivos...")

        try:
            self.current_tasks = self.organizer.scan_files(src, dst, mode, recursive)
        except Exception as e:
            QMessageBox.critical(self, "Error de Lectura", f"No se pudo escanear el directorio: {e}")
            self._log(f"[ERROR] {e}")
            return

        if not self.current_tasks:
            self._populate_table([])
            self._log("No se encontraron archivos para organizar en la carpeta seleccionada.")
            self.statusBar().showMessage("Sin archivos encontrados")
            self.btn_organize.setEnabled(False)
            return

        # Simular tareas
        self.organizer.execute_tasks(self.current_tasks, dry_run=True)
        self._populate_table(self.current_tasks)

        movable_count = sum(1 for t in self.current_tasks if t.status != "Ya en destino")
        self._log(f"Simulación completa: {len(self.current_tasks)} archivos analizados ({movable_count} listos para mover).")
        self.statusBar().showMessage(f"Simulación: {movable_count} archivos listos")
        
        self.btn_organize.setEnabled(movable_count > 0)

    def _populate_table(self, tasks: List[FileTask]):
        """Carga la lista de tareas en la tabla gráfica."""
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            # Archivo
            item_name = QTableWidgetItem(task.filename)
            self.table.setItem(row, 0, item_name)

            # Categoría
            item_cat = QTableWidgetItem(task.category)
            self.table.setItem(row, 1, item_cat)

            # Tamaño
            item_size = QTableWidgetItem(format_size(task.size_bytes))
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, item_size)

            # Destino proyectado
            rel_dest = os.path.basename(task.target_folder)
            item_dest = QTableWidgetItem(f"/{rel_dest}/{task.filename}")
            self.table.setItem(row, 3, item_dest)

            # Estado
            item_status = QTableWidgetItem(task.status)
            self.table.setItem(row, 4, item_status)

    def _run_organization(self):
        """Ejecuta el movimiento real de los archivos."""
        movable = [t for t in self.current_tasks if t.status != "Ya en destino"]
        if not movable:
            QMessageBox.information(self, "Sin Tareas", "No hay archivos pendientes para organizar.")
            return

        reply = QMessageBox.question(
            self,
            "Confirmación de Organización",
            f"Se van a mover {len(movable)} archivos a sus carpetas correspondientes.\n\n¿Deseas continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            self._log("Operación cancelada por el usuario.")
            return

        self._set_ui_busy(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(movable))
        self.progress_bar.setValue(0)
        self._log(f"Iniciando movimiento físico de {len(movable)} archivos...")

        self.worker = OrganizerWorker(self.organizer, movable, dry_run=False)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log_message.connect(self._log)
        self.worker.finished_tasks.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, current: int, total: int, task: FileTask):
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Organizando {current}/{total}: {task.filename}")
        # Actualizar fila correspondiente en la tabla
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == task.filename:
                self.table.item(row, 4).setText(task.status)
                break

    def _on_worker_finished(self, tasks: List[FileTask]):
        self._set_ui_busy(False)
        self.progress_bar.setVisible(False)
        errors = sum(1 for t in tasks if t.status == "Error")
        success = sum(1 for t in tasks if t.status == "Movido")

        self._log(f"Operación finalizada. Éxito: {success}, Errores: {errors}.")
        self.statusBar().showMessage(f"Completado: {success} movidos, {errors} errores")
        self.btn_organize.setEnabled(False)

        if errors == 0:
            QMessageBox.information(
                self, "Operación Exitosa",
                f"Se han organizado exitosamente {success} archivos."
            )
        else:
            QMessageBox.warning(
                self, "Completado con advertencias",
                f"Se movieron {success} archivos, pero {errors} presentaron errores. Revisa el registro."
            )

    def _set_ui_busy(self, busy: bool):
        self.btn_preview.setEnabled(not busy)
        self.btn_organize.setEnabled(not busy)
        self.btn_clear.setEnabled(not busy)
        self.src_btn.setEnabled(not busy)
        self.dst_btn.setEnabled(not busy)
        self.mode_combo.setEnabled(not busy)
        self.recursive_chk.setEnabled(not busy)

    def _clear_all(self):
        """Reinicia el estado de la interfaz gráfica."""
        self.table.setRowCount(0)
        self.current_tasks.clear()
        self.btn_organize.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self._log("Tabla y estado reiniciados.")
        self.statusBar().showMessage("Listo")
