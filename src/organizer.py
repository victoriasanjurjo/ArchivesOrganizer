"""
Core logic module for local file organization.
Provides scanning, classification, simulation (Dry Run), and secure file moving.
"""

import os
import shutil
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional
from config.default_config import DEFAULT_CATEGORIES


class OrganizationMode(Enum):
    CATEGORY = "By Category"
    EXTENSION = "By Extension"
    DATE = "By Date (Year/Month)"


@dataclass
class FileTask:
    filename: str
    source_path: str
    target_folder: str
    target_path: str
    category: str
    size_bytes: int
    modified_time: datetime
    status: str = "Pending"  # "Pending", "Simulated", "Moved", "Skipped", "Error", "Already at destination"
    error_message: str = ""


class FileOrganizer:
    """
    Engine responsible for classifying and reorganizing files on the local file system.
    """

    def __init__(self, categories: Optional[Dict[str, List[str]]] = None):
        self.categories = categories if categories is not None else DEFAULT_CATEGORIES
        self._ext_to_category = self._build_extension_lookup()

    def _build_extension_lookup(self) -> Dict[str, str]:
        """Creates a fast lookup mapping from lowercase extension to category name."""
        lookup = {}
        if not isinstance(self.categories, dict):
            return lookup

        for category, extensions in self.categories.items():
            if not category or not isinstance(extensions, (list, tuple, set)):
                continue
            for ext in extensions:
                if isinstance(ext, str) and ext.strip():
                    clean_ext = ext.strip().lower()
                    if not clean_ext.startswith("."):
                        clean_ext = f".{clean_ext}"
                    lookup[clean_ext] = str(category)
        return lookup

    def get_category_for_file(self, filename: str) -> str:
        """Determines the category of a file based on its extension."""
        if not filename or not isinstance(filename, str):
            return "No Extension"

        _, ext = os.path.splitext(filename)
        ext = ext.strip().lower()
        if not ext or ext == ".":
            return "No Extension"
        return self._ext_to_category.get(ext, "Others")

    def get_destination_folder_name(
        self,
        filepath: str,
        mode: OrganizationMode,
        date_format: str = "%Y-%m"
    ) -> str:
        """Calculates the destination subfolder name based on the selected mode."""
        if not filepath or not isinstance(filepath, str):
            filename = ""
        else:
            filename = os.path.basename(filepath)
        
        if mode == OrganizationMode.CATEGORY:
            return self.get_category_for_file(filename)
            
        elif mode == OrganizationMode.EXTENSION:
            if not filename:
                return "No_Extension"
            _, ext = os.path.splitext(filename)
            ext = ext.strip()
            if not ext or ext == ".":
                return "No_Extension"
            clean_ext = ext.lstrip(".").upper()
            return clean_ext if clean_ext else "No_Extension"
            
        elif mode == OrganizationMode.DATE:
            try:
                if not filepath or not isinstance(filepath, str) or not os.path.exists(filepath):
                    return "Unknown_Date"
                mtime = os.path.getmtime(filepath)
                dt = datetime.fromtimestamp(mtime)
                fmt = date_format if (isinstance(date_format, str) and date_format.strip()) else "%Y-%m"
                formatted = dt.strftime(fmt)
                return formatted if formatted.strip() else "Unknown_Date"
            except Exception:
                return "Unknown_Date"
                
        return "Miscellaneous"

    def resolve_target_collision(self, target_folder: str, filename: str) -> str:
        """
        Ensures existing files are not overwritten by appending an incremental number suffix if needed.
        """
        safe_target_folder = target_folder if (target_folder and isinstance(target_folder, str)) else "."
        safe_filename = filename if (filename and isinstance(filename, str)) else "file"

        base_name, ext = os.path.splitext(safe_filename)
        candidate_path = os.path.join(safe_target_folder, safe_filename)
        counter = 1

        while os.path.exists(candidate_path):
            candidate_path = os.path.join(safe_target_folder, f"{base_name} ({counter}){ext}")
            counter += 1

        return candidate_path

    def scan_files(
        self,
        source_dir: str,
        dest_dir: str,
        mode: OrganizationMode,
        recursive: bool = False,
        date_format: str = "%Y-%m"
    ) -> List[FileTask]:
        """
        Scans files in the source directory and projects operations without modifying disk state.
        """
        if not source_dir or not isinstance(source_dir, str) or not os.path.isdir(source_dir):
            raise ValueError(f"Source directory does not exist or is invalid: {source_dir}")

        if not dest_dir or not isinstance(dest_dir, str):
            dest_dir = source_dir

        tasks: List[FileTask] = []
        normalized_source = os.path.abspath(source_dir)
        normalized_dest = os.path.abspath(dest_dir)

        # Check if destination is inside source to avoid scanning newly created subfolders
        def is_subpath(child: str, parent: str) -> bool:
            try:
                rel = os.path.relpath(child, parent)
                return not rel.startswith("..")
            except ValueError:
                return False

        if recursive:
            for root, dirs, files in os.walk(normalized_source):
                # Avoid entering destination directory if nested
                if is_subpath(root, normalized_dest) and root != normalized_source:
                    continue

                for f in files:
                    full_path = os.path.join(root, f)
                    task = self._create_task(full_path, normalized_dest, mode, date_format)
                    if task:
                        tasks.append(task)
        else:
            try:
                with os.scandir(normalized_source) as entries:
                    for entry in entries:
                        if entry.is_file(follow_symlinks=False):
                            task = self._create_task(entry.path, normalized_dest, mode, date_format)
                            if task:
                                tasks.append(task)
            except PermissionError as e:
                raise PermissionError(f"Permission denied reading directory: {e}")

        return tasks

    def _create_task(
        self,
        filepath: str,
        dest_dir: str,
        mode: OrganizationMode,
        date_format: str
    ) -> Optional[FileTask]:
        """Creates a projected operation task for an individual file."""
        filename = os.path.basename(filepath)
        
        try:
            stat = os.stat(filepath)
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime)
        except Exception:
            size = 0
            mtime = datetime.now()

        subfolder_name = self.get_destination_folder_name(filepath, mode, date_format)
        target_folder = os.path.join(dest_dir, subfolder_name)
        
        # If the file is already in its projected destination, mark as already in destination
        current_folder = os.path.dirname(os.path.abspath(filepath))
        if os.path.abspath(target_folder) == current_folder:
            status = "Already at destination"
            target_path = filepath
        else:
            status = "Pending"
            target_path = os.path.join(target_folder, filename)

        category = self.get_category_for_file(filename)

        return FileTask(
            filename=filename,
            source_path=filepath,
            target_folder=target_folder,
            target_path=target_path,
            category=category,
            size_bytes=size,
            modified_time=mtime,
            status=status
        )

    def execute_tasks(
        self,
        tasks: List[FileTask],
        dry_run: bool = False,
        progress_callback: Optional[Callable[[int, int, FileTask], None]] = None
    ) -> List[FileTask]:
        """
        Executes projected tasks or simulates their execution if dry_run is True.
        """
        if not tasks or not isinstance(tasks, list):
            return []

        total = len(tasks)
        for idx, task in enumerate(tasks):
            if not isinstance(task, FileTask):
                continue

            if task.status == "Already at destination":
                if progress_callback:
                    try:
                        progress_callback(idx + 1, total, task)
                    except Exception:
                        pass
                continue

            if dry_run:
                task.status = "Simulated"
                if progress_callback:
                    try:
                        progress_callback(idx + 1, total, task)
                    except Exception:
                        pass
                continue

            try:
                # Create destination folder if it does not exist
                os.makedirs(task.target_folder, exist_ok=True)
                
                # Resolve real collision at time of moving
                final_target_path = self.resolve_target_collision(
                    task.target_folder,
                    os.path.basename(task.source_path)
                )
                
                shutil.move(task.source_path, final_target_path)
                task.target_path = final_target_path
                task.status = "Moved"
            except Exception as e:
                task.status = "Error"
                task.error_message = str(e)

            if progress_callback:
                try:
                    progress_callback(idx + 1, total, task)
                except Exception:
                    pass

        return tasks

