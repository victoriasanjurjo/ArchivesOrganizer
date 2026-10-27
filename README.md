# ArchivesOrganizer

**ArchivesOrganizer** is a desktop application designed to classify and reorganize files automatically, securely, and **100% locally**. It features a modern, clean, and monochrome graphical user interface developed with **PySide6 (Qt)**, ensuring complete privacy by operating entirely offline without internet connections or telemetry.

---

## Key Features

- **100% Local & Private Operation:** All scanning and file relocation takes place strictly on your local storage without transmitting data anywhere.
- **Multiple Organization Rules:**
  - **By Category:** Groups files by semantic purpose (*Documents*, *Images*, *Videos*, *Audio*, *Compressed*, *Code*, *Executables & Installers*, *Others*).
  - **By Exact Extension:** Creates folders named after the exact extension (e.g., `PDF/`, `PNG/`, `DOCX/`).
  - **By Date (Year/Month):** Organizes files according to their last modified date into time-based folders (e.g., `2026-10/`).
- **Simulation / Preview Mode (Dry Run):** Visually inspect projected operations before making any physical alterations to disk.
- **Immediate Button Lockout & Reentrancy Safety:** All critical buttons (Simulate, Organize, Export, Clear) and inputs lock immediately upon being triggered, avoiding race conditions, duplicate worker threads, or corrupted states.
- **Audit Export to CSV:** One-click export of analyzed or organized files to standard `.csv` spreadsheet reports.
- **Overwrite Prevention (Collision Resolution):** If a file with the same name already exists in the destination folder, an incremental counter is automatically appended (e.g., `document (1).pdf`).
- **Recursive Scanning Support:** Option to organize only the root of the chosen folder or process all nested subfolders.
- **Real-Time Audit Logging:** Integrated activity console providing a live chronological record of every operation.
- **Professional Monochrome Aesthetic:** High-contrast grayscale and charcoal theme designed for maximum clarity and readability.

---

## Project Architecture

```text
ArchivesOrganizer/
├── docs/                        # Technical documentation, decisions, and changelog
│   ├── architecture.md          # Technical architecture & design rationale
│   └── changelog.md             # Plain-English modification register & logbook
├── tests/                       # Automated unit test suite
│   ├── test_organizer.py        # Standard logic and simulation tests
│   ├── test_edge_cases.py       # Comprehensive edge case tests (nulls, giant inputs, etc.)
│   ├── test_errors_and_db.py    # Granular I/O error formatting and SQLite database tests
│   └── test_ui_locks.py         # Immediate button lockout and reentrancy safety tests
├── config/                      # Category and extension configurations
│   └── default_config.py
├── assets/                      # Icons and visual resources (.ico, .png)
│   ├── icon.ico
│   └── icon.png
├── outputs/                     # Output directory (contains local SQLite audit database)
│   └── archives_history.db
├── src/                         # Application source code
│   ├── __init__.py
│   ├── organizer.py             # Core organization logic engine
│   ├── errors.py                # Granular file system & DB error translation
│   ├── database.py              # Local SQLite database manager for audit history
│   ├── generate_assets.py       # Application icon generator
│   └── ui/                      # PySide6 graphical user interface module
│       ├── __init__.py
│       ├── main_window.py       # Main window & multithreaded task management
│       └── styles.py            # Monochrome QSS stylesheet
├── .gitignore                   # Version control exclusions
├── requirements.txt             # Exact installed dependencies
├── LICENSE.txt                  # MIT open source license
├── README.md                    # General project manual & execution guide
└── main.py                      # Application entry point
```

---

## Automated Unit Testing

The project maintains comprehensive test coverage across standard workflows, extreme edge cases, granular error handling, and button safety:

```bash
# Run all unit tests (58 passing tests)
python -m unittest discover tests

# Run UI lockout and reentrancy prevention tests specifically
python -m unittest tests/test_ui_locks.py
```

---

## Release & Distribution

A standalone, ready-to-run Windows executable (**Version 1.0.0**) is provided directly:

- **Compiled Executable:** `dist/ArchivesOrganizer/ArchivesOrganizer.exe`

No installation or terminal commands are required; simply double-click the `.exe` file to start the desktop interface.

---

## License

This project is distributed under the **MIT License**. For full details, see the [LICENSE.txt](file:///d:/Proyectos/ArchivesOrganizer/LICENSE.txt) file.
