"""
Unit tests for UI lockouts, critical action button states, and reentrancy prevention.
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication

from src.ui.main_window import MainWindow
from src.organizer import FileTask, OrganizationMode

# Ensure single QApplication instance for Qt tests
app = QApplication.instance() or QApplication([])


class TestUILocksAndReentrancy(unittest.TestCase):
    """Verifies that critical action buttons are disabled immediately and duplicate calls are prevented."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.window = MainWindow(base_dir=self.temp_dir.name)

    def tearDown(self):
        self.window.close()
        self.temp_dir.cleanup()

    def test_initial_button_states(self):
        """Initial state should have preview and clear enabled, organize and export disabled."""
        self.assertTrue(self.window.btn_preview.isEnabled())
        self.assertFalse(self.window.btn_organize.isEnabled())
        self.assertFalse(self.window.btn_export.isEnabled())
        self.assertTrue(self.window.btn_clear.isEnabled())
        self.assertFalse(self.window._is_busy)

    def test_set_ui_busy_locks_all_controls(self):
        """_set_ui_busy(True) must immediately disable all critical action buttons and input controls."""
        # Setup fake task so organize and export could normally be enabled
        target_dir = os.path.join(self.temp_dir.name, "Documents")
        fake_task = FileTask(
            filename="doc.pdf",
            source_path=os.path.join(self.temp_dir.name, "doc.pdf"),
            target_folder=target_dir,
            target_path=os.path.join(target_dir, "doc.pdf"),
            category="Documents",
            size_bytes=1024,
            modified_time=datetime.now(),
            status="Pending"
        )
        self.window.current_tasks = [fake_task]

        # Lock UI
        self.window._set_ui_busy(True)
        self.assertTrue(self.window._is_busy)
        self.assertFalse(self.window.btn_preview.isEnabled())
        self.assertFalse(self.window.btn_organize.isEnabled())
        self.assertFalse(self.window.btn_export.isEnabled())
        self.assertFalse(self.window.btn_clear.isEnabled())
        self.assertFalse(self.window.src_btn.isEnabled())
        self.assertFalse(self.window.dst_btn.isEnabled())
        self.assertFalse(self.window.src_input.isEnabled())
        self.assertFalse(self.window.dst_input.isEnabled())
        self.assertFalse(self.window.mode_combo.isEnabled())
        self.assertFalse(self.window.recursive_chk.isEnabled())

        # Unlock UI
        self.window._set_ui_busy(False)
        self.assertFalse(self.window._is_busy)
        self.assertTrue(self.window.btn_preview.isEnabled())
        self.assertTrue(self.window.btn_organize.isEnabled())
        self.assertTrue(self.window.btn_export.isEnabled())
        self.assertTrue(self.window.btn_clear.isEnabled())
        self.assertTrue(self.window.src_btn.isEnabled())
        self.assertTrue(self.window.dst_btn.isEnabled())
        self.assertTrue(self.window.src_input.isEnabled())
        self.assertTrue(self.window.dst_input.isEnabled())
        self.assertTrue(self.window.mode_combo.isEnabled())
        self.assertTrue(self.window.recursive_chk.isEnabled())

    def test_reentrancy_blocked_when_busy(self):
        """When _is_busy is True, duplicate calls to critical action methods must be rejected immediately."""
        self.window._is_busy = True

        with patch.object(self.window.organizer, "scan_files") as mock_scan:
            self.window._run_simulation()
            mock_scan.assert_not_called()

        with patch("PySide6.QtWidgets.QMessageBox.question") as mock_msg:
            self.window._run_organization()
            mock_msg.assert_not_called()

        with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName") as mock_save:
            self.window._export_log()
            mock_save.assert_not_called()

        with patch.object(self.window.table, "setRowCount") as mock_set_rows:
            self.window._clear_all()
            mock_set_rows.assert_not_called()

    def test_reentrancy_blocked_when_worker_is_running(self):
        """When worker thread is running, duplicate calls to critical action methods must be rejected immediately."""
        fake_worker = MagicMock()
        fake_worker.isRunning.return_value = True
        self.window.worker = fake_worker

        with patch.object(self.window.organizer, "scan_files") as mock_scan:
            self.window._run_simulation()
            mock_scan.assert_not_called()

        with patch("PySide6.QtWidgets.QMessageBox.question") as mock_msg:
            self.window._run_organization()
            mock_msg.assert_not_called()

        with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName") as mock_save:
            self.window._export_log()
            mock_save.assert_not_called()

        with patch.object(self.window.table, "setRowCount") as mock_set_rows:
            self.window._clear_all()
            mock_set_rows.assert_not_called()

    def test_export_log_writes_csv_and_restores_state(self):
        """_export_log exports task records to a CSV file and restores UI state safely."""
        target_dir = os.path.join(self.temp_dir.name, "Documents")
        fake_task = FileTask(
            filename="report.pdf",
            source_path=os.path.join(self.temp_dir.name, "report.pdf"),
            target_folder=target_dir,
            target_path=os.path.join(target_dir, "report.pdf"),
            category="Documents",
            size_bytes=2048,
            modified_time=datetime.now(),
            status="Moved",
            error_message=None
        )
        self.window.current_tasks = [fake_task]
        export_csv_path = os.path.join(self.temp_dir.name, "test_output.csv")

        with patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=(export_csv_path, "CSV Files (*.csv)")):
            with patch("PySide6.QtWidgets.QMessageBox.information"):
                self.window._export_log()

        self.assertFalse(self.window._is_busy)
        self.assertTrue(os.path.exists(export_csv_path))

        with open(export_csv_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("Filename,Category,Size (Bytes)", lines[0])
        self.assertIn("report.pdf,Documents,2048", lines[1])


if __name__ == "__main__":
    unittest.main()
