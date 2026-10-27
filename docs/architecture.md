# Technical Architecture & Decision Log - ArchivesOrganizer

## 1. Project Overview
**ArchivesOrganizer** is a 100% local desktop tool developed in Python and PySide6 (Qt) designed to classify and reorganize files automatically and securely. It operates completely offline, requiring no internet connectivity and emitting no telemetry.

## 2. Technical Decisions and Rationale

### 2.1 Graphical User Interface: PySide6 (Qt for Python)
- **Selection Rationale:** PySide6 provides native performance on Windows, robust thread management via `QThread`/`Signal` to prevent GUI freezing during heavy disk I/O operations, and support for advanced styling through Qt Style Sheets (QSS).
- **Monochrome Aesthetics:** A minimalist palette of charcoal, dark gray, white, and neutral accents was implemented, ensuring high contrast, clean typography, and a modern feel without visual distraction.

### 2.2 Supported Organization Modes
1. **By Category:** Groups files according to their semantic purpose (Documents, Images, Videos, Audio, Compressed, Code, Executables & Installers, Others).
2. **By Exact Extension:** Creates a folder for each extension discovered (e.g., `PDF/`, `DOCX/`, `PNG/`).
3. **By Date (Year/Month):** Organizes files based on their last modified timestamp into folders structured as `YYYY-MM/`.

### 2.3 Safety and Data Loss Prevention
- **Simulation / Preview Mode (Dry Run):** Allows users to scan folders and inspect the projected source-to-target mapping in a visual table before altering any physical file on disk.
- **Collision Resolution:** If a file with the same name already exists in the destination folder, an incremental numerical suffix is automatically appended (e.g., `report (1).pdf`), preventing accidental overwrites.
- **Atomic Local Operations:** Relocation relies on `shutil.move` with exception isolation for permissions, file locks, or long paths.
- **Audit Logging:** Every operation and status change is emitted in real time to the application activity console.

### 2.4 Packaging: PyInstaller
- Compiled in `--windowed` mode (suppressing the terminal console).
- Incorporates a custom icon located at `assets/icon.ico` and `assets/icon.png` into the final standalone binary.

## 3. Module Structure
- `main.py`: Application entry point.
- `src/organizer.py`: Core organization logic (scanning, classification, simulation, and physical execution).
- `src/ui/`: Graphical user interface components, main window, and monochrome QSS styling.
- `config/`: File category definitions, default extensions, and metadata.
- `assets/`: Application icon and visual resources.
- `tests/`: General unit tests (`test_organizer.py`) and edge case test suite (`test_edge_cases.py`).
- `docs/`: Technical architecture documentation (`architecture.md`) and modification register (`changelog.md`).

## 4. Unit Testing Strategy and Edge Case Handling

To ensure enterprise-grade reliability in production environments with messy and arbitrary user data, `FileOrganizer` implements defensive programming verified by a comprehensive automated test suite (`tests/test_edge_cases.py`):

1. **Giant Text Inputs:**
   - *Mitigated Risk:* Buffer overflows, quadratic parsing latency, or memory exhaustion on filenames or extensions exceeding 100,000 characters.
   - *Behavior:* Suffixes and extensions are processed safely using `os.path.splitext` without unbounded string concatenations.

2. **Special Characters and Multilingual Filenames:**
   - *Mitigated Risk:* Character encoding corruptions on non-ASCII characters, accents (`á, é, í, ó, ú, ñ, ü`), non-Latin scripts (Cyrillic, Chinese, Japanese, Arabic, Greek), and emojis (`📸, 🚀, 💻`).
   - *Behavior:* Transparent UTF-8 handling preserved natively by the operating system, with error isolation when encountering OS-restricted path characters (`*`, `?`, `<`, `>`, `|`, `:`).
   - *System and Hidden Files:* Robust parsing of `.gitignore`, `.env`, and files ending in solitary dots (`file.`), safely classifying them as `No Extension` / `No_Extension`.

3. **Empty Strings and Blank Values:**
   - *Mitigated Risk:* `IndexError` or string split failures.
   - *Behavior:* Empty strings (`""`) or whitespace-only inputs (`"   "`) immediately fall back to safe defaults (`"No Extension"` or `"No_Extension"`).

4. **Null Values (`None`):**
   - *Mitigated Risk:* `TypeError: expected str, bytes or os.PathLike object, not NoneType`.
   - *Behavior:* Explicit `isinstance(..., str)` type checks before path operations. When `None` is passed to scanning functions, a clear and actionable `ValueError` is raised.

5. **Invalid Formats and Unexpected Types:**
   - *Mitigated Risk:* Passing integers, booleans, lists, or custom objects where strings or enum modes are expected.
   - *Behavior:* Graceful fallback to safe categories and destination names (`"No Extension"`, `"Miscellaneous"`), with exception shielding in progress callbacks to avoid interrupting active file moving operations.
