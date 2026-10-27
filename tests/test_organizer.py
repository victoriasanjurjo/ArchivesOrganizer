"""
Unit tests for the ArchivesOrganizer core engine.
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from src.organizer import FileOrganizer, OrganizationMode, FileTask


class TestFileOrganizer(unittest.TestCase):

    def setUp(self):
        # Create an isolated temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        # Clean up temporary directory
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_category_lookup(self):
        """Verifies correct classification based on extension."""
        self.assertEqual(self.organizer.get_category_for_file("foto.png"), "Images")
        self.assertEqual(self.organizer.get_category_for_file("documento.pdf"), "Documents")
        self.assertEqual(self.organizer.get_category_for_file("cancion.mp3"), "Audio")
        self.assertEqual(self.organizer.get_category_for_file("video.mp4"), "Videos")
        self.assertEqual(self.organizer.get_category_for_file("script.py"), "Code")
        self.assertEqual(self.organizer.get_category_for_file("unknown_file.xyz123"), "Others")
        self.assertEqual(self.organizer.get_category_for_file("no_extension"), "No Extension")

    def test_extension_mode_destination(self):
        """Verifies that extension mode generates the correct uppercase folder."""
        dest = self.organizer.get_destination_folder_name("test.pdf", OrganizationMode.EXTENSION)
        self.assertEqual(dest, "PDF")

        dest_none = self.organizer.get_destination_folder_name("test", OrganizationMode.EXTENSION)
        self.assertEqual(dest_none, "No_Extension")

    def test_date_mode_destination(self):
        """Verifies that date mode produces the expected Year-Month format."""
        test_file = os.path.join(self.test_dir, "test_date.txt")
        with open(test_file, "w") as f:
            f.write("test")

        dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE)
        current_year_month = datetime.now().strftime("%Y-%m")
        self.assertEqual(dest, current_year_month)

    def test_collision_resolution(self):
        """Verifies that resolving collisions appends increment numbers without overwriting."""
        folder = os.path.join(self.test_dir, "Target")
        os.makedirs(folder, exist_ok=True)
        
        file1 = os.path.join(folder, "note.txt")
        with open(file1, "w") as f:
            f.write("version 1")

        # Resolution should suggest "note (1).txt"
        new_path = self.organizer.resolve_target_collision(folder, "note.txt")
        self.assertEqual(os.path.basename(new_path), "note (1).txt")

        # Create "note (1).txt" and verify next increment
        with open(new_path, "w") as f:
            f.write("version 2")

        new_path_2 = self.organizer.resolve_target_collision(folder, "note.txt")
        self.assertEqual(os.path.basename(new_path_2), "note (2).txt")

    def test_dry_run_simulation(self):
        """Verifies that simulation mode does not modify disk state."""
        file_to_scan = os.path.join(self.test_dir, "report.docx")
        with open(file_to_scan, "w") as f:
            f.write("simulated content")

        tasks = self.organizer.scan_files(self.test_dir, self.test_dir, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].filename, "report.docx")

        results = self.organizer.execute_tasks(tasks, dry_run=True)
        self.assertEqual(results[0].status, "Simulated")
        # Original file must still exist in root
        self.assertTrue(os.path.exists(file_to_scan))

    def test_real_move_execution(self):
        """Verifies that real move physically relocates file to destination folder."""
        file_to_move = os.path.join(self.test_dir, "image.png")
        with open(file_to_move, "w") as f:
            f.write("image data")

        tasks = self.organizer.scan_files(self.test_dir, self.test_dir, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)

        results = self.organizer.execute_tasks(tasks, dry_run=False)
        self.assertEqual(results[0].status, "Moved")

        # Original must no longer exist in root
        self.assertFalse(os.path.exists(file_to_move))
        # Must exist in Images subfolder
        expected_path = os.path.join(self.test_dir, "Images", "image.png")
        self.assertTrue(os.path.exists(expected_path))


if __name__ == "__main__":
    unittest.main()

