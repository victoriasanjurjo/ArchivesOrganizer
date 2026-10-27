"""
Granular error management and user-friendly message formatting.
Translates low-level OS, file system, and database exceptions into clear, actionable explanations.
"""

import errno
import os
import shutil
import sqlite3
from typing import Optional


def format_file_error(
    exc: Exception,
    filepath: Optional[str] = None,
    context: str = "operation"
) -> str:
    """
    Analyzes an exception originating from file system I/O and converts it
    into a plain-English, user-friendly explanation with recovery advice.
    """
    filename = os.path.basename(filepath) if filepath else "the file"

    # 1. Permission and File Lock Errors
    if isinstance(exc, PermissionError):
        # On Windows, error 32 or 13 indicates file is in use or read-only
        winerror = getattr(exc, 'winerror', None)
        if winerror == 32:
            return (
                f"File in use: '{filename}' is currently locked by another program. "
                "Please close any application using it and try again."
            )
        elif winerror == 5:
            return (
                f"Access denied: You do not have permission to modify '{filename}'. "
                "Check folder permissions or run the app as Administrator."
            )
        return (
            f"Access restricted: Permission was denied while accessing '{filename}'. "
            "Ensure the file is not marked read-only or in use."
        )

    # 2. File or Directory Missing
    if isinstance(exc, FileNotFoundError):
        return (
            f"File not found: '{filename}' was moved, renamed, or deleted "
            "by another process before this operation could complete."
        )

    # 3. Path is a regular file where folder was expected
    if isinstance(exc, NotADirectoryError):
        return (
            f"Invalid directory: The path '{filename}' points to a file, "
            "not a folder."
        )

    # 4. Target already exists where unique name was required
    if isinstance(exc, (FileExistsError, shutil.SameFileError)):
        return (
            f"Duplicate file conflict: A file identical to '{filename}' "
            "already exists in the destination folder."
        )

    # 5. OS-Level Errors with specific errno codes
    if isinstance(exc, OSError):
        err_code = getattr(exc, 'errno', None)

        if err_code == errno.ENOSPC:
            return (
                f"Disk full: There is not enough free storage space on the "
                f"target drive to complete the {context} for '{filename}'."
            )

        if err_code == errno.ENAMETOOLONG:
            return (
                f"Path too long: The path for '{filename}' exceeds the maximum "
                "allowed character limit on Windows (260 characters)."
            )

        if err_code == errno.EINVAL:
            return (
                f"Invalid path characters: The name '{filename}' contains characters "
                "not permitted by Windows (such as <, >, :, \", /, \\, |, ?, *)."
            )

        if err_code in (errno.EACCES, errno.EBUSY):
            return (
                f"Resource busy: '{filename}' is locked or actively being written "
                "by another process."
            )

        if err_code == errno.EROFS:
            return (
                f"Read-only storage: The destination drive or media containing "
                f"'{filename}' is write-protected."
            )

    # 6. Shutil-specific move/copy errors
    if isinstance(exc, shutil.Error):
        return (
            f"Relocation conflict: Could not move '{filename}'. "
            f"Reason: {str(exc).strip()}"
        )

    # 7. Unicode decoding/encoding issues
    if isinstance(exc, (UnicodeDecodeError, UnicodeEncodeError)):
        return (
            f"Encoding error: The name of '{filename}' contains special characters "
            "that cannot be decoded using the current system encoding."
        )

    # 8. Fallback for unexpected exceptions
    clean_msg = str(exc).strip()
    return f"Unexpected {context} error with '{filename}': {clean_msg}"


def format_db_error(exc: Exception, operation: str = "database operation") -> str:
    """
    Translates SQLite database exceptions into friendly user notices.
    """
    if isinstance(exc, sqlite3.OperationalError):
        msg_lower = str(exc).lower()
        if "locked" in msg_lower or "busy" in msg_lower:
            return (
                f"Database temporarily busy: Another process is accessing the audit log. "
                "The operation will retry automatically."
            )
        if "disk" in msg_lower or "full" in msg_lower:
            return (
                f"Storage warning: Disk space is full. Could not save {operation} "
                "to the audit database."
            )
        return f"Database operational warning during {operation}: {exc}"

    if isinstance(exc, sqlite3.IntegrityError):
        return (
            f"Database integrity warning: An audit record conflict occurred during {operation}."
        )

    if isinstance(exc, PermissionError):
        return (
            f"Database permission denied: Cannot write to the audit database file. "
            "Please check folder permissions."
        )

    if isinstance(exc, (sqlite3.DatabaseError, OSError)):
        return f"Database storage warning: Could not record {operation}. Reason: {exc}"

    return f"Unexpected database issue during {operation}: {exc}"
