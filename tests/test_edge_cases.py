"""
Unit tests specifically targeting edge cases:
- Giant text inputs
- Special characters (Unicode, emojis, accents, restricted characters)
- Empty strings and whitespace-only strings
- Null values (None)
- Invalid formats and unexpected data types
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime

from src.organizer import FileOrganizer, OrganizationMode, FileTask
from config.default_config import DEFAULT_CATEGORIES


class TestEdgeCasesFileOrganizer(unittest.TestCase):
    """
    Comprehensive test suite to evaluate the resilience of FileOrganizer
    against atypical inputs, system boundaries, and corrupt data.
    """

    def setUp(self):
        """Initializes test environment with an isolated temporary directory."""
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        """Cleans up the temporary directory after each test."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    # =========================================================================
    # 1. GIANT TEXT INPUTS
    # =========================================================================

    def test_giant_filename_classification(self):
        """Verifies that filenames with extreme length (100k characters) are processed without memory exhaustion."""
        giant_base = "a" * 100000
        filename_pdf = f"{giant_base}.pdf"
        filename_png = f"{giant_base}.png"
        filename_unknown = f"{giant_base}.verylongextension123456"

        self.assertEqual(self.organizer.get_category_for_file(filename_pdf), "Documents")
        self.assertEqual(self.organizer.get_category_for_file(filename_png), "Images")
        self.assertEqual(self.organizer.get_category_for_file(filename_unknown), "Others")

    def test_giant_extension_classification(self):
        """Verifies behavior with excessively long file extensions."""
        giant_ext = "." + "x" * 10000
        filename = f"document{giant_ext}"
        self.assertEqual(self.organizer.get_category_for_file(filename), "Others")

    def test_giant_destination_folder_name(self):
        """Verifies destination calculation with extensive paths and massive date formats."""
        giant_path = os.path.join(self.test_dir, "sub" * 50, "file" * 20 + ".pdf")
        
        # Category Mode
        cat_dest = self.organizer.get_destination_folder_name(giant_path, OrganizationMode.CATEGORY)
        self.assertEqual(cat_dest, "Documents")

        # Extension Mode
        ext_dest = self.organizer.get_destination_folder_name(giant_path, OrganizationMode.EXTENSION)
        self.assertEqual(ext_dest, "PDF")

        # Date Mode with giant format (1000 repetitions of '%Y-')
        giant_date_format = "%Y-" * 1000
        test_file = os.path.join(self.test_dir, "date_test_file.txt")
        with open(test_file, "w") as f:
            f.write("content")
        
        date_dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE, date_format=giant_date_format)
        self.assertTrue(len(date_dest) > 1000)
        self.assertTrue(date_dest.startswith(str(datetime.now().year)))

    def test_giant_collision_resolution(self):
        """Verifies collision resolution with long filenames."""
        giant_filename = ("long_filename_" * 15) + ".txt"
        target_folder = os.path.join(self.test_dir, "target_folder")
        os.makedirs(target_folder, exist_ok=True)

        # Create collision
        first_file = os.path.join(target_folder, giant_filename)
        with open(first_file, "w") as f:
            f.write("first file")

        resolved_path = self.organizer.resolve_target_collision(target_folder, giant_filename)
        self.assertTrue(resolved_path.endswith("(1).txt"))
        self.assertNotEqual(resolved_path, first_file)

    # =========================================================================
    # 2. SPECIAL CHARACTERS AND UNICODE
    # =========================================================================

    def test_unicode_accents_and_spanish_characters(self):
        """Verifies support for accented and special characters (tildes, ñ, umlauts, opening signs)."""
        files = [
            ("annual_report_2026_ñandú.pdf", "Documents"),
            ("canción_música_acústica.mp3", "Audio"),
            ("diseño_pingüino_vídeo.mp4", "Videos"),
            ("código_fuente_español.py", "Code"),
            ("¿¡presentation_graphics!?.pptx", "Documents")
        ]
        for fname, expected_cat in files:
            with self.subTest(filename=fname):
                self.assertEqual(self.organizer.get_category_for_file(fname), expected_cat)

    def test_multilingual_unicode_characters(self):
        """Verifies filenames in non-Latin scripts (Cyrillic, Chinese, Japanese, Arabic, Greek)."""
        cases = [
            ("отчет_финансы.docx", "Documents"),      # Russian / Cyrillic
            ("财务报告_2026.xlsx", "Documents"),       # Chinese
            ("会議録_日本語.pdf", "Documents"),         # Japanese
            ("ملخص_التقرير.txt", "Documents"),       # Arabic
            ("μουσική_τραγούδι.wav", "Audio")         # Greek
        ]
        for fname, expected_cat in cases:
            with self.subTest(filename=fname):
                self.assertEqual(self.organizer.get_category_for_file(fname), expected_cat)

    def test_emojis_in_filenames_and_folders(self):
        """Verifies files containing emojis in their filenames and folder paths."""
        emoji_files = [
            ("📸_vacation_beach_🏖️.png", "Images", "PNG"),
            ("🎥_full_movie_🍿.mkv", "Videos", "MKV"),
            ("🎵_relaxing_sound_🎧.flac", "Audio", "FLAC"),
            ("💻_smart_algorithm_🤖.py", "Code", "PY")
        ]
        for fname, expected_cat, expected_ext in emoji_files:
            with self.subTest(filename=fname):
                self.assertEqual(self.organizer.get_category_for_file(fname), expected_cat)
                ext_res = self.organizer.get_destination_folder_name(fname, OrganizationMode.EXTENSION)
                self.assertEqual(ext_res, expected_ext)

    def test_special_symbols_and_delimiters(self):
        """Verifies complex punctuation and symbols in filenames."""
        symbols = [
            "file #1 (final version) [rev-2] {backup} ~ $100.pdf",
            "log@backup&data+test=ok;run^now!.txt",
            "__init__--v1..2...3.final.min.js"
        ]
        for fname in symbols:
            with self.subTest(filename=fname):
                cat = self.organizer.get_category_for_file(fname)
                self.assertIn(cat, ["Documents", "Code", "Others"])

    def test_multiple_consecutive_dots(self):
        """Verifies filenames with multiple consecutive dots and double extensions."""
        self.assertEqual(self.organizer.get_category_for_file("archive.tar.gz"), "Compressed")
        self.assertEqual(self.organizer.get_category_for_file("library.bundle.min.js"), "Code")
        self.assertEqual(self.organizer.get_category_for_file("name...with...dots...png"), "Images")

    def test_hidden_files_starting_with_dot(self):
        """Verifies UNIX/Windows hidden system files starting with a dot (.gitignore, .env)."""
        self.assertEqual(self.organizer.get_category_for_file(".gitignore"), "No Extension")
        self.assertEqual(self.organizer.get_category_for_file(".env"), "No Extension")
        self.assertEqual(self.organizer.get_category_for_file(".bashrc"), "No Extension")
        self.assertEqual(self.organizer.get_category_for_file(".DS_Store"), "No Extension")

        dest = self.organizer.get_destination_folder_name(".gitignore", OrganizationMode.EXTENSION)
        self.assertEqual(dest, "No_Extension")

    def test_whitespace_and_tabs_in_filenames(self):
        """Verifies filenames with leading, trailing, and multiple spaces."""
        self.assertEqual(self.organizer.get_category_for_file("   leading_spaces.pdf"), "Documents")
        self.assertEqual(self.organizer.get_category_for_file("file with many   spaces.docx"), "Documents")
        self.assertEqual(self.organizer.get_category_for_file("trailing_space.png  "), "Images")

    # =========================================================================
    # 3. EMPTY STRINGS AND BLANK VALUES
    # =========================================================================

    def test_empty_string_filename(self):
        """Verifies behavior when filename is an empty string or whitespace only."""
        self.assertEqual(self.organizer.get_category_for_file(""), "No Extension")
        self.assertEqual(self.organizer.get_category_for_file("   "), "No Extension")

    def test_empty_string_destination_folder_name(self):
        """Verifies destination calculation when path is an empty string."""
        self.assertEqual(
            self.organizer.get_destination_folder_name("", OrganizationMode.CATEGORY),
            "No Extension"
        )
        self.assertEqual(
            self.organizer.get_destination_folder_name("", OrganizationMode.EXTENSION),
            "No_Extension"
        )
        self.assertEqual(
            self.organizer.get_destination_folder_name("", OrganizationMode.DATE),
            "Unknown_Date"
        )

    def test_empty_date_format_string(self):
        """Verifies that an empty date format string falls back to default."""
        test_file = os.path.join(self.test_dir, "test_empty_date.txt")
        with open(test_file, "w") as f:
            f.write("sample")

        dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE, date_format="")
        current_year_month = datetime.now().strftime("%Y-%m")
        self.assertEqual(dest, current_year_month)

    def test_files_without_extension(self):
        """Verifies files without any extension (e.g., LICENSE, Makefile, Dockerfile)."""
        no_ext = ["LICENSE", "Makefile", "Dockerfile", "README", "plain_file"]
        for fname in no_ext:
            with self.subTest(filename=fname):
                self.assertEqual(self.organizer.get_category_for_file(fname), "No Extension")
                dest_ext = self.organizer.get_destination_folder_name(fname, OrganizationMode.EXTENSION)
                self.assertEqual(dest_ext, "No_Extension")

    def test_file_ending_in_single_dot(self):
        """Verifies files ending with a single dot ('filename.')."""
        self.assertEqual(self.organizer.get_category_for_file("filename."), "No Extension")
        dest_ext = self.organizer.get_destination_folder_name("filename.", OrganizationMode.EXTENSION)
        self.assertEqual(dest_ext, "No_Extension")

    def test_empty_directory_scan(self):
        """Verifies scanning a completely empty directory."""
        empty_dir = os.path.join(self.test_dir, "empty_folder")
        os.makedirs(empty_dir, exist_ok=True)
        
        tasks = self.organizer.scan_files(empty_dir, empty_dir, OrganizationMode.CATEGORY)
        self.assertEqual(tasks, [])

    def test_empty_tasks_list_execution(self):
        """Verifies that execute_tasks returns empty list safely on empty inputs."""
        self.assertEqual(self.organizer.execute_tasks([]), [])
        self.assertEqual(self.organizer.execute_tasks([], dry_run=True), [])

    # =========================================================================
    # 4. NULL / NONE VALUES
    # =========================================================================

    def test_none_filename_handling(self):
        """Verifies that passing None as filename does not raise unhandled exceptions."""
        self.assertEqual(self.organizer.get_category_for_file(None), "No Extension")

    def test_none_filepath_in_destination(self):
        """Verifies behavior when filepath is None in get_destination_folder_name."""
        self.assertEqual(
            self.organizer.get_destination_folder_name(None, OrganizationMode.CATEGORY),
            "No Extension"
        )
        self.assertEqual(
            self.organizer.get_destination_folder_name(None, OrganizationMode.EXTENSION),
            "No_Extension"
        )
        self.assertEqual(
            self.organizer.get_destination_folder_name(None, OrganizationMode.DATE),
            "Unknown_Date"
        )

    def test_none_mode_in_destination(self):
        """Verifies behavior when organization mode is None."""
        dest = self.organizer.get_destination_folder_name("file.pdf", None)
        self.assertEqual(dest, "Miscellaneous")

    def test_none_date_format_in_destination(self):
        """Verifies that date_format=None safely applies the standard format."""
        test_file = os.path.join(self.test_dir, "test_none_date.txt")
        with open(test_file, "w") as f:
            f.write("content")

        dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE, date_format=None)
        expected = datetime.now().strftime("%Y-%m")
        self.assertEqual(dest, expected)

    def test_none_source_dir_in_scan_raises_value_error(self):
        """Verifies that passing None as source_dir raises ValueError."""
        with self.assertRaises(ValueError):
            self.organizer.scan_files(None, self.test_dir, OrganizationMode.CATEGORY)

    def test_none_dest_dir_defaults_to_source_dir(self):
        """Verifies that passing dest_dir=None defaults to source_dir."""
        test_file = os.path.join(self.test_dir, "sample.docx")
        with open(test_file, "w") as f:
            f.write("data")

        tasks = self.organizer.scan_files(self.test_dir, None, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)
        expected_target_dir = os.path.join(self.test_dir, "Documents")
        self.assertEqual(os.path.normpath(tasks[0].target_folder), os.path.normpath(expected_target_dir))

    def test_none_tasks_in_execute_tasks(self):
        """Verifies that execute_tasks(None) returns an empty list defensively."""
        self.assertEqual(self.organizer.execute_tasks(None), [])

    def test_organizer_init_with_none_categories(self):
        """Verifies that instantiating FileOrganizer(categories=None) uses DEFAULT_CATEGORIES."""
        custom_org = FileOrganizer(categories=None)
        self.assertEqual(custom_org.categories, DEFAULT_CATEGORIES)
        self.assertEqual(custom_org.get_category_for_file("photo.png"), "Images")

    def test_categories_dict_containing_none_values(self):
        """Verifies a category dict containing None keys or None items."""
        corrupt_categories = {
            None: [None, ".custom1"],
            "SecureDocs": [None, ".doc", ".pdf", 12345],
            "EmptyCat": None
        }
        custom_org = FileOrganizer(categories=corrupt_categories)
        self.assertEqual(custom_org.get_category_for_file("report.doc"), "SecureDocs")
        self.assertEqual(custom_org.get_category_for_file("other.xyz"), "Others")

    # =========================================================================
    # 5. INVALID FORMATS AND UNEXPECTED DATA TYPES
    # =========================================================================

    def test_invalid_types_for_filename(self):
        """Verifies that passing non-string types as filename does not raise fatal exceptions."""
        invalid_inputs = [12345, 99.9, True, False, ["test.pdf"], {"file": "a.txt"}, object()]
        for invalid_val in invalid_inputs:
            with self.subTest(invalid_value=invalid_val):
                res = self.organizer.get_category_for_file(invalid_val)
                self.assertEqual(res, "No Extension")

    def test_invalid_mode_type(self):
        """Verifies that modes not belonging to OrganizationMode enum return 'Miscellaneous'."""
        invalid_modes = ["INVENTED_MODE", 999, False, ("CATEGORY",)]
        for inv_mode in invalid_modes:
            with self.subTest(invalid_mode=inv_mode):
                dest = self.organizer.get_destination_folder_name("file.pdf", inv_mode)
                self.assertEqual(dest, "Miscellaneous")

    def test_invalid_date_format_token(self):
        """Verifies that invalid or malformed strftime tokens do not break execution."""
        test_file = os.path.join(self.test_dir, "test_invalid_fmt.txt")
        with open(test_file, "w") as f:
            f.write("date content")

        dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE, date_format="%%Invalid!!%Q")
        self.assertIsInstance(dest, str)
        self.assertTrue(len(dest) > 0)

    def test_nonexistent_source_directory_raises_value_error(self):
        """Verifies that scanning a non-existent path raises ValueError."""
        nonexistent_path = os.path.join(self.test_dir, "folder_that_never_exists_12345")
        with self.assertRaises(ValueError) as ctx:
            self.organizer.scan_files(nonexistent_path, self.test_dir, OrganizationMode.CATEGORY)
        self.assertIn("does not exist", str(ctx.exception).lower())

    def test_source_directory_pointing_to_a_file_raises_value_error(self):
        """Verifies that passing regular file path as source_dir raises ValueError."""
        regular_file = os.path.join(self.test_dir, "regular_file.txt")
        with open(regular_file, "w") as f:
            f.write("I am a file, not a directory")

        with self.assertRaises(ValueError):
            self.organizer.scan_files(regular_file, self.test_dir, OrganizationMode.CATEGORY)

    def test_corrupted_categories_type_in_constructor(self):
        """Verifies that passing non-dict types as categories does not break initialization."""
        org_with_int = FileOrganizer(categories=12345)
        self.assertEqual(org_with_int.get_category_for_file("doc.pdf"), "Others")

        org_with_str = FileOrganizer(categories="invalid_string")
        self.assertEqual(org_with_str.get_category_for_file("photo.png"), "Others")

    def test_execute_tasks_with_missing_source_files(self):
        """Verifies that tasks whose source files were deleted prior to execution record an error."""
        nonexistent_file = os.path.join(self.test_dir, "ghost_file.pdf")
        target_folder = os.path.join(self.test_dir, "Documents")
        
        task = FileTask(
            filename="ghost_file.pdf",
            source_path=nonexistent_file,
            target_folder=target_folder,
            target_path=os.path.join(target_folder, "ghost_file.pdf"),
            category="Documents",
            size_bytes=100,
            modified_time=datetime.now(),
            status="Pending"
        )

        results = self.organizer.execute_tasks([task], dry_run=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, "Error")
        self.assertTrue(len(results[0].error_message) > 0)

    def test_progress_callback_exception_tolerance(self):
        """Verifies that a failing progress callback does not halt execution of tasks."""
        test_file = os.path.join(self.test_dir, "callback_photo.png")
        with open(test_file, "w") as f:
            f.write("image data")

        tasks = self.organizer.scan_files(self.test_dir, self.test_dir, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)

        def failing_callback(current, total, task):
            raise RuntimeError("Simulated internal error inside progress callback")

        # Execution should complete successfully despite callback failures
        results = self.organizer.execute_tasks(tasks, dry_run=False, progress_callback=failing_callback)
        self.assertEqual(results[0].status, "Moved")
        self.assertTrue(os.path.exists(results[0].target_path))


if __name__ == "__main__":
    unittest.main()
