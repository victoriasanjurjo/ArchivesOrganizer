"""
Unit tests for granular error management (src/errors.py) and
local audit database operations (src/database.py).
"""

import errno
import os
import shutil
import sqlite3
import tempfile
import unittest
from datetime import datetime

from src.errors import format_file_error, format_db_error
from src.database import AuditDatabaseManager
from src.organizer import FileOrganizer, FileTask, OrganizationMode


class TestGranularErrorsAndDatabase(unittest.TestCase):
    """
    Validates granular file I/O error formatting and SQLite audit database resiliency.
    """

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, "test_audit.db")
        self.db = AuditDatabaseManager(db_path=self.db_path)
        self.organizer = FileOrganizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # =========================================================================
    # 1. GRANULAR FILE ERROR FORMATTING TESTS
    # =========================================================================

    def test_permission_error_formatting(self):
        """Verifies friendly translation for permission and file lock issues."""
        err_generic = PermissionError("Permission denied")
        msg = format_file_error(err_generic, "/path/to/locked_file.xlsx")
        self.assertIn("locked_file.xlsx", msg)
        self.assertIn("Permission was denied", msg)

        # Windows file lock error (winerror = 32)
        err_locked = PermissionError("The process cannot access the file")
        setattr(err_locked, 'winerror', 32)
        msg_locked = format_file_error(err_locked, "budget.xlsx")
        self.assertIn("budget.xlsx", msg_locked)
        self.assertIn("File in use", msg_locked)

        # Windows access denied (winerror = 5)
        err_admin = PermissionError("Access is denied")
        setattr(err_admin, 'winerror', 5)
        msg_admin = format_file_error(err_admin, "system.dll")
        self.assertIn("Access denied", msg_admin)
        self.assertIn("Administrator", msg_admin)

    def test_file_not_found_formatting(self):
        """Verifies friendly translation when a file vanishes."""
        err = FileNotFoundError("No such file or directory")
        msg = format_file_error(err, "deleted_document.pdf")
        self.assertIn("File not found", msg)
        self.assertIn("deleted_document.pdf", msg)

    def test_not_a_directory_formatting(self):
        """Verifies friendly message when a file is passed where directory was expected."""
        err = NotADirectoryError("Not a directory")
        msg = format_file_error(err, "file_as_dir.txt")
        self.assertIn("Invalid directory", msg)
        self.assertIn("points to a file", msg)

    def test_disk_full_error_formatting(self):
        """Verifies friendly message when storage is full (ENOSPC)."""
        err = OSError()
        err.errno = errno.ENOSPC
        msg = format_file_error(err, "huge_video.mp4")
        self.assertIn("Disk full", msg)
        self.assertIn("huge_video.mp4", msg)

    def test_path_too_long_formatting(self):
        """Verifies friendly message for path exceeding 260 character limit."""
        err = OSError()
        err.errno = errno.ENAMETOOLONG
        msg = format_file_error(err, "deeply_nested_file.txt")
        self.assertIn("Path too long", msg)
        self.assertIn("260 characters", msg)

    def test_invalid_characters_formatting(self):
        """Verifies friendly message for illegal path characters."""
        err = OSError()
        err.errno = errno.EINVAL
        msg = format_file_error(err, "invalid*name?.txt")
        self.assertIn("Invalid path characters", msg)

    def test_shutil_errors_formatting(self):
        """Verifies handling of same file error and generic shutil errors."""
        err_same = shutil.SameFileError("Source and target are the same")
        msg_same = format_file_error(err_same, "repeat.txt")
        self.assertIn("Duplicate file conflict", msg_same)

        err_move = shutil.Error("Destination path already exists")
        msg_move = format_file_error(err_move, "sample.docx")
        self.assertIn("Relocation conflict", msg_move)

    # =========================================================================
    # 2. GRANULAR DATABASE ERROR FORMATTING TESTS
    # =========================================================================

    def test_database_error_formatting(self):
        """Verifies friendly translation for SQLite database errors."""
        err_busy = sqlite3.OperationalError("database is locked")
        msg_busy = format_db_error(err_busy, "session record")
        self.assertIn("Database temporarily busy", msg_busy)

        err_integrity = sqlite3.IntegrityError("UNIQUE constraint failed")
        msg_integrity = format_db_error(err_integrity, "audit log")
        self.assertIn("Database integrity warning", msg_integrity)

        err_perm = PermissionError("Database file access denied")
        msg_perm = format_db_error(err_perm, "writing history")
        self.assertIn("Database permission denied", msg_perm)

    # =========================================================================
    # 3. LOCAL DATABASE MANAGER OPERATIONS (SQLite)
    # =========================================================================

    def test_database_initialization_and_schema(self):
        """Verifies that the audit database creates tables properly."""
        self.assertTrue(os.path.exists(self.db_path))
        self.assertIsNone(self.db.last_error_message)

        # Inspect tables in the SQLite database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            self.assertIn("sessions", tables)
            self.assertIn("file_records", tables)

    def test_log_organization_run_success(self):
        """Verifies logging a full session with tasks into SQLite."""
        task1 = FileTask(
            filename="report.pdf",
            source_path=os.path.join(self.test_dir, "report.pdf"),
            target_folder=os.path.join(self.test_dir, "Documents"),
            target_path=os.path.join(self.test_dir, "Documents", "report.pdf"),
            category="Documents",
            size_bytes=1024,
            modified_time=datetime.now(),
            status="Moved"
        )
        task2 = FileTask(
            filename="locked.xlsx",
            source_path=os.path.join(self.test_dir, "locked.xlsx"),
            target_folder=os.path.join(self.test_dir, "Documents"),
            target_path=os.path.join(self.test_dir, "Documents", "locked.xlsx"),
            category="Documents",
            size_bytes=2048,
            modified_time=datetime.now(),
            status="Error",
            error_message="File in use by another program"
        )

        session_id = self.db.log_organization_run(
            source_dir=self.test_dir,
            dest_dir=self.test_dir,
            mode="By Category",
            recursive=False,
            dry_run=False,
            tasks=[task1, task2]
        )

        self.assertIsNotNone(session_id)
        self.assertIsNone(self.db.last_error_message)

        # Query recent sessions
        sessions = self.db.get_recent_sessions(limit=5)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["total_files"], 2)
        self.assertEqual(sessions[0]["moved_count"], 1)
        self.assertEqual(sessions[0]["error_count"], 1)

    def test_database_empty_tasks_returns_none(self):
        """Verifies that passing empty tasks list returns None without error."""
        session_id = self.db.log_organization_run(
            source_dir=self.test_dir,
            dest_dir=self.test_dir,
            mode="By Category",
            recursive=False,
            dry_run=True,
            tasks=[]
        )
        self.assertIsNone(session_id)

    # =========================================================================
    # 4. GRANULAR ERROR CAPTURE DURING FILE MOVEMENT
    # =========================================================================

    def test_execute_tasks_granular_missing_file_error(self):
        """Verifies that missing files produce user-friendly error messages."""
        ghost_path = os.path.join(self.test_dir, "ghost_file.txt")
        task = FileTask(
            filename="ghost_file.txt",
            source_path=ghost_path,
            target_folder=os.path.join(self.test_dir, "Documents"),
            target_path=os.path.join(self.test_dir, "Documents", "ghost_file.txt"),
            category="Documents",
            size_bytes=50,
            modified_time=datetime.now(),
            status="Pending"
        )

        results = self.organizer.execute_tasks([task], dry_run=False)
        self.assertEqual(results[0].status, "Error")
        self.assertIn("File not found", results[0].error_message)
        self.assertIn("ghost_file.txt", results[0].error_message)


if __name__ == "__main__":
    unittest.main()
