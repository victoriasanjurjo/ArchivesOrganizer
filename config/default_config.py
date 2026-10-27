"""
Default configuration for ArchivesOrganizer.
Defines categories and associated file extensions for file classification.
"""

from typing import Dict, List

DEFAULT_CATEGORIES: Dict[str, List[str]] = {
    "Documents": [
        ".pdf", ".doc", ".docx", ".odt", ".rtf", ".tex", ".txt", ".md",
        ".xls", ".xlsx", ".ods", ".csv", ".ppt", ".pptx", ".odp"
    ],
    "Images": [
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
    "Compressed": [
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso", ".tgz"
    ],
    "Code": [
        ".py", ".js", ".ts", ".html", ".css", ".java", ".c", ".cpp", ".cs",
        ".go", ".rs", ".php", ".rb", ".json", ".xml", ".yaml", ".yml", ".sql", ".sh", ".bat", ".ps1"
    ],
    "Executables & Installers": [
        ".exe", ".msi", ".bat", ".cmd", ".apk", ".dmg", ".app", ".bin"
    ],
    "Others": []
}

APP_TITLE = "ArchivesOrganizer"
APP_VERSION = "1.0.0"

