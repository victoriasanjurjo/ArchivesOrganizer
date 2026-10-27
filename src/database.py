"""
Local SQLite database manager for audit history and file operation tracking.
Provides granular error management and persistence without blocking GUI operations.
"""

import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from src.errors import format_db_error


class AuditDatabaseManager:
    """
    Manages local SQLite database operations for logging file organization history.
    All operations are shielded with granular error handling so database issues
    never disrupt or crash the primary file organization workflows.
    """

    def __init__(self, db_path: Optional[str] = None):
        if not db_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            outputs_dir = os.path.join(base_dir, "outputs")
            try:
                os.makedirs(outputs_dir, exist_ok=True)
                self.db_path = os.path.join(outputs_dir, "archives_history.db")
            except (PermissionError, OSError):
                # Fallback to local directory if outputs is unwritable
                self.db_path = os.path.join(base_dir, "archives_history.db")
        else:
            self.db_path = db_path

        self.last_error_message: Optional[str] = None
        self._initialize_schema()

    def _get_connection(self) -> sqlite3.Connection:
        """Creates a connection with strict timeout and row factory."""
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_schema(self) -> bool:
        """Creates the required tables if they do not exist."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Sessions table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source_folder TEXT NOT NULL,
                        destination_folder TEXT NOT NULL,
                        mode TEXT NOT NULL,
                        is_recursive INTEGER NOT NULL,
                        is_dry_run INTEGER NOT NULL,
                        total_files INTEGER NOT NULL,
                        moved_count INTEGER NOT NULL,
                        error_count INTEGER NOT NULL
                    )
                """)

                # File operations table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS file_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        session_id INTEGER,
                        timestamp TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        target_path TEXT NOT NULL,
                        category TEXT NOT NULL,
                        size_bytes INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        error_message TEXT,
                        FOREIGN KEY (session_id) REFERENCES sessions (id)
                    )
                """)
                conn.commit()
            self.last_error_message = None
            return True
        except sqlite3.OperationalError as e:
            self.last_error_message = format_db_error(e, "schema initialization")
            return False
        except (PermissionError, OSError) as e:
            self.last_error_message = format_db_error(e, "creating database file")
            return False
        except Exception as e:
            self.last_error_message = format_db_error(e, "unexpected schema setup")
            return False

    def log_organization_run(
        self,
        source_dir: str,
        dest_dir: str,
        mode: str,
        recursive: bool,
        dry_run: bool,
        tasks: List[Any]
    ) -> Optional[int]:
        """
        Saves a full scan or move session and its individual file operations.
        Returns the created session ID, or None if the write failed gracefully.
        """
        if not tasks:
            return None

        total_files = len(tasks)
        moved_count = sum(1 for t in tasks if getattr(t, 'status', '') == "Moved")
        error_count = sum(1 for t in tasks if getattr(t, 'status', '') == "Error")
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sessions (
                        timestamp, source_folder, destination_folder, mode,
                        is_recursive, is_dry_run, total_files, moved_count, error_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    now_str,
                    str(source_dir),
                    str(dest_dir),
                    str(mode),
                    1 if recursive else 0,
                    1 if dry_run else 0,
                    total_files,
                    moved_count,
                    error_count
                ))
                session_id = cursor.lastrowid

                # Batch insert task records
                records = []
                for task in tasks:
                    records.append((
                        session_id,
                        now_str,
                        str(getattr(task, 'filename', '')),
                        str(getattr(task, 'source_path', '')),
                        str(getattr(task, 'target_path', '')),
                        str(getattr(task, 'category', '')),
                        int(getattr(task, 'size_bytes', 0)),
                        str(getattr(task, 'status', '')),
                        str(getattr(task, 'error_message', ''))
                    ))

                cursor.executemany("""
                    INSERT INTO file_records (
                        session_id, timestamp, filename, source_path,
                        target_path, category, size_bytes, status, error_message
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, records)
                conn.commit()

            self.last_error_message = None
            return session_id

        except sqlite3.OperationalError as e:
            self.last_error_message = format_db_error(e, "logging session")
            return None
        except sqlite3.IntegrityError as e:
            self.last_error_message = format_db_error(e, "session record integrity")
            return None
        except (PermissionError, OSError) as e:
            self.last_error_message = format_db_error(e, "writing session to disk")
            return None
        except Exception as e:
            self.last_error_message = format_db_error(e, "saving session record")
            return None

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieves recent organization sessions for audit verification."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, timestamp, source_folder, destination_folder, mode,
                           is_recursive, is_dry_run, total_files, moved_count, error_count
                    FROM sessions
                    ORDER BY id DESC
                    LIMIT ?
                """, (max(1, int(limit)),))
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.OperationalError as e:
            self.last_error_message = format_db_error(e, "fetching recent sessions")
            return []
        except (PermissionError, OSError) as e:
            self.last_error_message = format_db_error(e, "reading database file")
            return []
        except Exception as e:
            self.last_error_message = format_db_error(e, "querying sessions")
            return []
