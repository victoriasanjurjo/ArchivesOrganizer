"""
Módulo de lógica principal para la organización local de archivos.
Provee escaneo, clasificación, simulación (Dry Run) y ejecución de movimientos seguros.
"""

import os
import shutil
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Callable, Optional
from config.default_config import DEFAULT_CATEGORIES


class OrganizationMode(Enum):
    CATEGORY = "Por Categoría"
    EXTENSION = "Por Extensión"
    DATE = "Por Fecha (Año/Mes)"


@dataclass
class FileTask:
    filename: str
    source_path: str
    target_folder: str
    target_path: str
    category: str
    size_bytes: int
    modified_time: datetime
    status: str = "Pendiente"  # "Pendiente", "Simulado", "Movido", "Omitido", "Error"
    error_message: str = ""


class FileOrganizer:
    """
    Motor encargado de clasificar y reubicar archivos en el sistema local.
    """

    def __init__(self, categories: Optional[Dict[str, List[str]]] = None):
        self.categories = categories or DEFAULT_CATEGORIES
        self._ext_to_category = self._build_extension_lookup()

    def _build_extension_lookup(self) -> Dict[str, str]:
        """Crea un mapa rápido de extensión en minúsculas a nombre de categoría."""
        lookup = {}
        for category, extensions in self.categories.items():
            for ext in extensions:
                lookup[ext.lower()] = category
        return lookup

    def get_category_for_file(self, filename: str) -> str:
        """Determina la categoría de un archivo basándose en su extensión."""
        _, ext = os.path.splitext(filename)
        ext = ext.lower()
        if not ext:
            return "Sin Extensión"
        return self._ext_to_category.get(ext, "Otros")

    def get_destination_folder_name(
        self,
        filepath: str,
        mode: OrganizationMode,
        date_format: str = "%Y-%m"
    ) -> str:
        """Calcula el nombre de la subcarpeta destino según el modo seleccionado."""
        filename = os.path.basename(filepath)
        
        if mode == OrganizationMode.CATEGORY:
            return self.get_category_for_file(filename)
            
        elif mode == OrganizationMode.EXTENSION:
            _, ext = os.path.splitext(filename)
            if not ext:
                return "Sin_Extension"
            return ext.lstrip(".").upper()
            
        elif mode == OrganizationMode.DATE:
            try:
                mtime = os.path.getmtime(filepath)
                dt = datetime.fromtimestamp(mtime)
                return dt.strftime(date_format)
            except Exception:
                return "Fecha_Desconocida"
                
        return "Varios"

    def resolve_target_collision(self, target_folder: str, filename: str) -> str:
        """
        Garantiza que no se sobreescriba un archivo existente, agregando un sufijo numérico si es necesario.
        """
        base_name, ext = os.path.splitext(filename)
        candidate_path = os.path.join(target_folder, filename)
        counter = 1

        while os.path.exists(candidate_path):
            candidate_path = os.path.join(target_folder, f"{base_name} ({counter}){ext}")
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
        Escanea los archivos en el directorio origen y proyecta las operaciones sin modificar disco.
        """
        if not os.path.isdir(source_dir):
            raise ValueError(f"El directorio origen no existe: {source_dir}")

        if not dest_dir:
            dest_dir = source_dir

        tasks: List[FileTask] = []
        normalized_source = os.path.abspath(source_dir)
        normalized_dest = os.path.abspath(dest_dir)

        # Determinar si el destino está dentro del origen para evitar procesar carpetas creadas
        def is_subpath(child: str, parent: str) -> bool:
            try:
                rel = os.path.relpath(child, parent)
                return not rel.startswith("..")
            except ValueError:
                return False

        if recursive:
            for root, dirs, files in os.walk(normalized_source):
                # Evitar entrar al directorio destino si está anidado
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
                raise PermissionError(f"Sin permiso para leer la carpeta: {e}")

        return tasks

    def _create_task(
        self,
        filepath: str,
        dest_dir: str,
        mode: OrganizationMode,
        date_format: str
    ) -> Optional[FileTask]:
        """Crea una tarea proyectada para un archivo individual."""
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
        
        # Si el archivo ya se encuentra en su destino proyectado, se marca como no necesario
        current_folder = os.path.dirname(os.path.abspath(filepath))
        if os.path.abspath(target_folder) == current_folder:
            status = "Ya en destino"
            target_path = filepath
        else:
            status = "Pendiente"
            # Proyectar resolución de nombre
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
        Ejecuta las tareas proyectadas o simula su ejecución si dry_run es True.
        """
        total = len(tasks)
        for idx, task in enumerate(tasks):
            if task.status == "Ya en destino":
                if progress_callback:
                    progress_callback(idx + 1, total, task)
                continue

            if dry_run:
                task.status = "Simulado"
                if progress_callback:
                    progress_callback(idx + 1, total, task)
                continue

            try:
                # Crear carpeta destino si no existe
                os.makedirs(task.target_folder, exist_ok=True)
                
                # Resolver colisión real al momento de mover
                final_target_path = self.resolve_target_collision(
                    task.target_folder,
                    os.path.basename(task.source_path)
                )
                
                shutil.move(task.source_path, final_target_path)
                task.target_path = final_target_path
                task.status = "Movido"
            except Exception as e:
                task.status = "Error"
                task.error_message = str(e)

            if progress_callback:
                progress_callback(idx + 1, total, task)

        return tasks
