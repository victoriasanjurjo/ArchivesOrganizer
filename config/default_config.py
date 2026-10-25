"""
Configuración por defecto para ArchivesOrganizer.
Define las categorías y extensiones asociadas para la clasificación de archivos.
"""

from typing import Dict, List

DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Documentos": [
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".tex", ".txt", ".md",
        ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx", ".odp"
    ],
    "Imágenes": [
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg",
        ".ico", ".raw", ".psd", ".ai"
    ],
    "Videos": [
        ".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".3gp", ".mpeg", ".mpg"
    ],
    "Audio": [
        ".mp3", ".wav", ".aac", ".flac", ".ogg", ".wma", ".m4a", ".opus",
        ".mid", ".midi"
    ],
    "Comprimidos": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz"
    ],
    "Programación": [
        ".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".cs",
        ".go", ".rs", ".php", ".rb", ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".bat", ".ps1"
    ],
    "Ejecutables e Instaladores": [
        ".exe", ".msi", ".bat", ".cmd", ".apk", ".dmg", ".app", ".bin"
    ],
    "Otros": []
}

APP_TITLE = "ArchivesOrganizer"
APP_VERSION = "1.0.0"
