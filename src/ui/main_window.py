"""
Main window for ArchivesOrganizer with PySide6 GUI.
Monochrome design, task visualization, simulation (Dry Run), and multithreaded execution.
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
from src.database import AuditDatabaseManager
from src.ui.styles import MONOCHROME_STYLE


def format_size(bytes_val: int) -> str:
    """Converts bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"


class OrganizerWorker(QThread):
    """Background thread to execute or simulate operations without blocking UI."""
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
            
            action_name = "SIMULATED" if self.dry_run else task.status.upper()
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
    """Main window for the file organizer application."""

    def __init__(self, base_dir: str):
        super().__init__()
        self.base_dir = base_dir
        self.organizer = FileOrganizer()
        self.db = AuditDatabaseManager()
        self.current_tasks: List[FileTask] = []
        self.worker: Optional[OrganizerWorker] = None

        self.setWindowTitle(f"{APP_TITLE} v{APP_VERSION} - 100% Local")
        self.resize(1000, 720)
        self.setMinimumSize(850, 600)

        self._setup_icon()
        self.setStyleSheet(MONOCHROME_STYLE)
        self._build_ui()
        self._log("System initialized in 100% local mode. Ready to operate.")
        if self.db.last_error_message:
            self._log(f"[Audit Notice] {self.db.last_error_message}")

    def _setup_icon(self):
        """Sets the application icon on the window."""
        icon_path_png = os.path.join(self.base_dir, "assets", "icon.png")
        icon_path_ico = os.path.join(self.base_dir, "assets", "icon.ico")
        
        if os.path.exists(icon_path_png):
            self.setWindowIcon(QIcon(icon_path_png))
        elif os.path.exists(icon_path_ico):
            self.setWindowIcon(QIcon(icon_path_ico))

    def _build_ui(self):
        """Builds all visual components of the user interface."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 16, 18, 14)
        main_layout.setSpacing(12)

        # Minimalist Header
        header_layout = QHBoxLayout()
        header_title = QLabel(APP_TITLE.upper())
        header_title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        header_title.setStyleSheet("color: #FFFFFF; letter-spacing: 2px;")
        
        header_subtitle = QLabel("•  LOCAL FILE ORGANIZER  •")
        header_subtitle.setStyleSheet("color: #777777; font-size: 11px; font-weight: 500;")
        
        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Path and Rule Configuration Panel
        config_group = QGroupBox("Organization Settings")
        config_layout = QVBoxLayout(config_group)
        config_layout.setSpacing(10)

        # Source Row
        src_layout = QHBoxLayout()
        src_label = QLabel("Source Folder:")
        src_label.setFixedWidth(130)
        self.src_input = QLineEdit()
        self.src_input.setPlaceholderText("Select the directory containing files to organize...")
        self.src_btn = QPushButton("Browse...")
        self.src_btn.setFixedWidth(100)
        self.src_btn.clicked.connect(self._browse_source)
        src_layout.addWidget(src_label)
        src_layout.addWidget(self.src_input)
        src_layout.addWidget(self.src_btn)
        config_layout.addLayout(src_layout)

        # Destination Row (Optional)
        dst_layout = QHBoxLayout()
        dst_label = QLabel("Destination Folder:")
        dst_label.setFixedWidth(130)
        self.dst_input = QLineEdit()
        self.dst_input.setPlaceholderText("Same as source directory (default) or select another folder...")
        self.dst_btn = QPushButton("Browse...")
        self.dst_btn.setFixedWidth(100)
        self.dst_btn.clicked.connect(self._browse_destination)
        dst_layout.addWidget(dst_label)
        dst_layout.addWidget(self.dst_input)
        dst_layout.addWidget(self.dst_btn)
        config_layout.addLayout(dst_layout)

        # Parameters and Mode Row
        params_layout = QHBoxLayout()
        mode_label = QLabel("Mode / Rule:")
        mode_label.setFixedWidth(130)
        self.mode_combo = QComboBox()
        self.mode_combo.addItem(OrganizationMode.CATEGORY.value, OrganizationMode.CATEGORY)
        self.mode_combo.addItem(OrganizationMode.EXTENSION.value, OrganizationMode.EXTENSION)
        self.mode_combo.addItem(OrganizationMode.DATE.value, OrganizationMode.DATE)
        
        self.recursive_chk = QCheckBox("Scan subfolders (recursive)")
        self.recursive_chk.setChecked(False)

        params_layout.addWidget(mode_label)
        params_layout.addWidget(self.mode_combo, 1)
        params_layout.addSpacing(20)
        params_layout.addWidget(self.recursive_chk)
        params_layout.addStretch()
        config_layout.addLayout(params_layout)

        main_layout.addWidget(config_group)

        # Action Buttons
        actions_layout = QHBoxLayout()
        self.btn_preview = QPushButton("1. Simulate / Preview (Dry Run)")
        self.btn_preview.setObjectName("secondaryButton")
        self.btn_preview.clicked.connect(self._run_simulation)

        self.btn_organize = QPushButton("2. Organize Files (Move)")
        self.btn_organize.setObjectName("primaryButton")
        self.btn_organize.clicked.connect(self._run_organization)
        self.btn_organize.setEnabled(False)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setFixedWidth(90)
        self.btn_clear.clicked.connect(self._clear_all)

        actions_layout.addWidget(self.btn_preview)
        actions_layout.addWidget(self.btn_organize)
        actions_layout.addStretch()
        actions_layout.addWidget(self.btn_clear)
        main_layout.addLayout(actions_layout)

        # Central Splitter: Table above, Log view below
        splitter = QSplitter(Qt.Vertical)

        # File Table
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Filename", "Category / Rule", "Size", "Projected Target", "Status"
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

        # Event and Audit Log Console
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        log_layout.setContentsMargins(0, 0, 0, 0)
        
        log_label = QLabel("Activity Log (Local Audit):")
        log_label.setStyleSheet("color: #888888; font-size: 11px; font-weight: 600;")
        self.log_view = QTextEdit()
        self.log_view.setObjectName("logView")
        self.log_view.setReadOnly(True)
        
        log_layout.addWidget(log_label)
        log_layout.addWidget(self.log_view)
        splitter.addWidget(log_container)

        # Adjust proportions (65% table, 35% log)
        splitter.setSizes([380, 180])
        main_layout.addWidget(splitter, 1)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Bottom Status Bar
        self.statusBar().showMessage("Ready")

    def _browse_source(self):
        """Opens dialog to select source directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Source Folder")
        if path:
            self.src_input.setText(os.path.normpath(path))
            self._log(f"Source folder selected: {path}")

    def _browse_destination(self):
        """Opens dialog to select optional destination directory."""
        path = QFileDialog.getExistingDirectory(self, "Select Destination Folder")
        if path:
            self.dst_input.setText(os.path.normpath(path))
            self._log(f"Custom destination selected: {path}")

    def _log(self, text: str):
        """Writes a timestamped line to the activity log console."""
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_view.append(f"[{ts}] {text}")

    def _run_simulation(self):
        """Scans files and projects the reorganization (Dry Run) with granular error handling."""
        src = self.src_input.text().strip()
        if not src:
            QMessageBox.warning(self, "Missing Path", "Please select a source folder before scanning.")
            return

        dst = self.dst_input.text().strip() or src
        mode = self.mode_combo.currentData()
        recursive = self.recursive_chk.isChecked()

        self._log(f"Starting scan in '{mode.value}' mode (Recursive: {recursive})...")
        self.statusBar().showMessage("Scanning files...")

        try:
            self.current_tasks = self.organizer.scan_files(src, dst, mode, recursive)
        except PermissionError as e:
            QMessageBox.critical(self, "Access Denied", str(e))
            self._log(f"[Access Error] {e}")
            self.statusBar().showMessage("Scan failed: Access denied")
            return
        except FileNotFoundError as e:
            QMessageBox.critical(self, "Folder Missing", str(e))
            self._log(f"[Not Found Error] {e}")
            self.statusBar().showMessage("Scan failed: Folder missing")
            return
        except OSError as e:
            QMessageBox.critical(self, "File System Error", str(e))
            self._log(f"[System Error] {e}")
            self.statusBar().showMessage("Scan failed: System error")
            return
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Path", str(e))
            self._log(f"[Validation Error] {e}")
            self.statusBar().showMessage("Scan failed: Invalid path")
            return

        if not self.current_tasks:
            self._populate_table([])
            self._log("No files found to organize in the selected folder.")
            self.statusBar().showMessage("No files found")
            self.btn_organize.setEnabled(False)
            return

        # Simulate tasks
        self.organizer.execute_tasks(self.current_tasks, dry_run=True)
        self._populate_table(self.current_tasks)

        movable_count = sum(1 for t in self.current_tasks if t.status != "Already at destination")
        self._log(f"Simulation complete: {len(self.current_tasks)} files analyzed ({movable_count} ready to move).")
        self.statusBar().showMessage(f"Simulation: {movable_count} files ready")
        
        # Log simulation session in local database
        self.db.log_organization_run(
            source_dir=src,
            dest_dir=dst,
            mode=mode.value,
            recursive=recursive,
            dry_run=True,
            tasks=self.current_tasks
        )
        if self.db.last_error_message:
            self._log(f"[Audit Notice] {self.db.last_error_message}")

        self.btn_organize.setEnabled(movable_count > 0)

    def _populate_table(self, tasks: List[FileTask]):
        """Populates the visual table with file tasks and friendly status tooltips."""
        self.table.setRowCount(len(tasks))
        for row, task in enumerate(tasks):
            # Filename
            item_name = QTableWidgetItem(task.filename)
            self.table.setItem(row, 0, item_name)

            # Category / Rule
            item_cat = QTableWidgetItem(task.category)
            self.table.setItem(row, 1, item_cat)

            # Size
            item_size = QTableWidgetItem(format_size(task.size_bytes))
            item_size.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 2, item_size)

            # Projected Target
            rel_dest = os.path.basename(task.target_folder)
            item_dest = QTableWidgetItem(f"/{rel_dest}/{task.filename}")
            self.table.setItem(row, 3, item_dest)

            # Status with friendly tooltip if error occurred
            item_status = QTableWidgetItem(task.status)
            if task.status == "Error" and task.error_message:
                item_status.setToolTip(task.error_message)
            self.table.setItem(row, 4, item_status)

    def _run_organization(self):
        """Executes the physical relocation of files."""
        movable = [t for t in self.current_tasks if t.status != "Already at destination"]
        if not movable:
            QMessageBox.information(self, "No Tasks", "There are no pending files to organize.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Organization",
            f"About to move {len(movable)} files to their respective folders.\n\nDo you wish to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )

        if reply != QMessageBox.Yes:
            self._log("Operation cancelled by user.")
            return

        self._set_ui_busy(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(movable))
        self.progress_bar.setValue(0)
        self._log(f"Starting physical relocation of {len(movable)} files...")

        self.worker = OrganizerWorker(self.organizer, movable, dry_run=False)
        self.worker.progress.connect(self._on_worker_progress)
        self.worker.log_message.connect(self._log)
        self.worker.finished_tasks.connect(self._on_worker_finished)
        self.worker.start()

    def _on_worker_progress(self, current: int, total: int, task: FileTask):
        self.progress_bar.setValue(current)
        self.statusBar().showMessage(f"Organizing {current}/{total}: {task.filename}")
        # Update matching row in table
        for row in range(self.table.rowCount()):
            if self.table.item(row, 0).text() == task.filename:
                status_item = self.table.item(row, 4)
                status_item.setText(task.status)
                if task.status == "Error" and task.error_message:
                    status_item.setToolTip(task.error_message)
                break

    def _on_worker_finished(self, tasks: List[FileTask]):
        self._set_ui_busy(False)
        self.progress_bar.setVisible(False)
        errors = sum(1 for t in tasks if t.status == "Error")
        success = sum(1 for t in tasks if t.status == "Moved")

        self._log(f"Operation complete. Success: {success}, Errors: {errors}.")
        self.statusBar().showMessage(f"Completed: {success} moved, {errors} errors")
        self.btn_organize.setEnabled(False)

        # Log physical execution session in local audit database
        src = self.src_input.text().strip()
        dst = self.dst_input.text().strip() or src
        mode = self.mode_combo.currentData()
        recursive = self.recursive_chk.isChecked()
        self.db.log_organization_run(
            source_dir=src,
            dest_dir=dst,
            mode=mode.value if mode else "Unknown",
            recursive=recursive,
            dry_run=False,
            tasks=tasks
        )
        if self.db.last_error_message:
            self._log(f"[Audit Notice] {self.db.last_error_message}")

        if errors == 0:
            QMessageBox.information(
                self, "Operation Successful",
                f"Successfully organized {success} files into their destination folders."
            )
        else:
            # Collect unique user-friendly error samples to display directly in the alert
            error_samples = []
            for t in tasks:
                if t.status == "Error" and t.error_message and t.error_message not in error_samples:
                    error_samples.append(f"• {t.error_message}")
                    if len(error_samples) >= 3:
                        break
            
            sample_text = "\n".join(error_samples)
            QMessageBox.warning(
                self, "Completed with warnings",
                f"Moved {success} files, but {errors} could not be organized.\n\n"
                f"Encountered issues:\n{sample_text}\n\n"
                "Check the Activity Log below for full details on each affected file."
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
        """Resets the state of the user interface."""
        self.table.setRowCount(0)
        self.current_tasks.clear()
        self.btn_organize.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self._log("Table and state reset.")
        self.statusBar().showMessage("Ready")

