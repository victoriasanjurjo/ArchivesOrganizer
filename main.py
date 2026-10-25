"""
Punto de entrada principal para ArchivesOrganizer.
Inicializa la aplicación PySide6 y la ventana con tema monocromático.
"""

import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

from config.default_config import APP_TITLE
from src.ui.main_window import MainWindow


def main():
    # Soporte para DPI alto en Windows
    app = QApplication(sys.argv)
    app.setApplicationName(APP_TITLE)
    app.setOrganizationName("ArchivesOrganizer")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    icon_path_ico = os.path.join(base_dir, "assets", "icon.ico")
    icon_path_png = os.path.join(base_dir, "assets", "icon.png")
    
    if os.path.exists(icon_path_ico):
        app.setWindowIcon(QIcon(icon_path_ico))
    elif os.path.exists(icon_path_png):
        app.setWindowIcon(QIcon(icon_path_png))

    window = MainWindow(base_dir=base_dir)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
