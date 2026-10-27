"""
QSS Stylesheets with minimalist, modern, and monochrome design.
Palette: Grayscale, charcoal, whites, and neutral contrasts.
"""

MONOCHROME_STYLE = """
/* Ventana principal y fondos base */
QMainWindow, QDialog {
    background-color: #121212;
    color: #E0E0E0;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QWidget {
    background-color: #121212;
    color: #E0E0E0;
    font-size: 13px;
}

/* Agrupadores y Marcos */
QGroupBox {
    border: 1px solid #333333;
    border-radius: 8px;
    margin-top: 18px;
    padding-top: 14px;
    font-weight: 600;
    color: #F0F0F0;
    background-color: #181818;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 6px;
    background-color: #181818;
    color: #FFFFFF;
}

/* Campos de entrada de texto */
QLineEdit {
    background-color: #1E1E1E;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 7px 10px;
    color: #FFFFFF;
    selection-background-color: #555555;
    selection-color: #FFFFFF;
}

QLineEdit:focus {
    border: 1px solid #888888;
}

QLineEdit:read-only {
    background-color: #181818;
    color: #999999;
}

/* Botones estándar */
QPushButton {
    background-color: #242424;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 16px;
    color: #F0F0F0;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #323232;
    border-color: #606060;
    color: #FFFFFF;
}

QPushButton:pressed {
    background-color: #181818;
    border-color: #202020;
}

QPushButton:disabled {
    background-color: #1A1A1A;
    border-color: #2A2A2A;
    color: #555555;
}

/* Botón principal (Acento monocromático: blanco puro con texto oscuro) */
QPushButton#primaryButton {
    background-color: #EAEAEA;
    color: #101010;
    border: 1px solid #FFFFFF;
    font-weight: 700;
}

QPushButton#primaryButton:hover {
    background-color: #FFFFFF;
    border-color: #FFFFFF;
}

QPushButton#primaryButton:pressed {
    background-color: #CCCCCC;
}

QPushButton#primaryButton:disabled {
    background-color: #333333;
    color: #777777;
    border-color: #333333;
}

/* Botón secundario resaltado */
QPushButton#secondaryButton {
    background-color: #2C2C2C;
    border: 1px solid #505050;
    color: #FFFFFF;
    font-weight: 600;
}

QPushButton#secondaryButton:hover {
    background-color: #383838;
    border-color: #707070;
}

/* Menús desplegables */
QComboBox {
    background-color: #1E1E1E;
    border: 1px solid #383838;
    border-radius: 6px;
    padding: 6px 12px;
    color: #F0F0F0;
}

QComboBox:hover {
    border: 1px solid #666666;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #303030;
}

QComboBox QAbstractItemView {
    background-color: #1E1E1E;
    border: 1px solid #444444;
    color: #E0E0E0;
    selection-background-color: #383838;
    selection-color: #FFFFFF;
}

/* Casillas de verificación */
QCheckBox {
    spacing: 8px;
    color: #D5D5D5;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #505050;
    border-radius: 4px;
    background-color: #1A1A1A;
}

QCheckBox::indicator:hover {
    border-color: #888888;
}

QCheckBox::indicator:checked {
    background-color: #FFFFFF;
    border-color: #FFFFFF;
    image: none;
}

/* Tablas */
QTableWidget {
    background-color: #161616;
    border: 1px solid #2C2C2C;
    border-radius: 6px;
    gridline-color: #242424;
    color: #E0E0E0;
    selection-background-color: #333333;
    selection-color: #FFFFFF;
}

QTableWidget::item {
    padding: 5px;
}

QHeaderView::section {
    background-color: #1F1F1F;
    color: #C0C0C0;
    padding: 6px 8px;
    border: 1px solid #292929;
    font-weight: 600;
    font-size: 12px;
}

/* Consola de logs */
QTextEdit#logView {
    background-color: #101010;
    border: 1px solid #282828;
    border-radius: 6px;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 11px;
    color: #CCCCCC;
    padding: 6px;
}

/* Barra de progreso */
QProgressBar {
    border: 1px solid #333333;
    border-radius: 5px;
    background-color: #181818;
    text-align: center;
    color: #FFFFFF;
    font-size: 11px;
    font-weight: 600;
    height: 14px;
}

QProgressBar::chunk {
    background-color: #888888;
    border-radius: 4px;
}

/* Barra de estado */
QStatusBar {
    background-color: #141414;
    color: #8E8E93;
    border-top: 1px solid #222222;
    font-size: 12px;
}

/* Barras de desplazamiento */
QScrollBar:vertical {
    background-color: #141414;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #333333;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background-color: #555555;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background-color: #141414;
    height: 10px;
    margin: 0;
}

QScrollBar::handle:horizontal {
    background-color: #333333;
    min-width: 20px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #555555;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
"""
