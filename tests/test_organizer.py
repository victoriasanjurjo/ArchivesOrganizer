"""
Pruebas unitarias para el motor de organización de archivos (ArchivesOrganizer).
"""

import os
import shutil
import tempfile
import unittest
from datetime import datetime
from src.organizer import FileOrganizer, OrganizationMode, FileTask


class TestFileOrganizer(unittest.TestCase):

    def setUp(self):
        # Crear un directorio temporal para pruebas aisladas
        self.test_dir = tempfile.mkdtemp()
        self.organizer = FileOrganizer()

    def tearDown(self):
        # Limpiar el directorio temporal
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_category_lookup(self):
        """Verifica la correcta clasificación según la extensión."""
        self.assertEqual(self.organizer.get_category_for_file("foto.png"), "Imágenes")
        self.assertEqual(self.organizer.get_category_for_file("documento.pdf"), "Documentos")
        self.assertEqual(self.organizer.get_category_for_file("cancion.mp3"), "Audio")
        self.assertEqual(self.organizer.get_category_for_file("video.mp4"), "Videos")
        self.assertEqual(self.organizer.get_category_for_file("script.py"), "Programación")
        self.assertEqual(self.organizer.get_category_for_file("archivo_desconocido.xyz123"), "Otros")
        self.assertEqual(self.organizer.get_category_for_file("sin_extension"), "Sin Extensión")

    def test_extension_mode_destination(self):
        """Verifica que el modo extensión genere la carpeta correcta en mayúsculas."""
        dest = self.organizer.get_destination_folder_name("test.pdf", OrganizationMode.EXTENSION)
        self.assertEqual(dest, "PDF")

        dest_none = self.organizer.get_destination_folder_name("test", OrganizationMode.EXTENSION)
        self.assertEqual(dest_none, "Sin_Extension")

    def test_date_mode_destination(self):
        """Verifica que el modo fecha produzca el formato esperado Año-Mes."""
        test_file = os.path.join(self.test_dir, "test_date.txt")
        with open(test_file, "w") as f:
            f.write("test")

        dest = self.organizer.get_destination_folder_name(test_file, OrganizationMode.DATE)
        current_year_month = datetime.now().strftime("%Y-%m")
        self.assertEqual(dest, current_year_month)

    def test_collision_resolution(self):
        """Verifica que resolver colisiones no sobrescriba archivos existentes."""
        folder = os.path.join(self.test_dir, "Target")
        os.makedirs(folder, exist_ok=True)
        
        file1 = os.path.join(folder, "nota.txt")
        with open(file1, "w") as f:
            f.write("versión 1")

        # La resolución debe sugerir "nota (1).txt"
        new_path = self.organizer.resolve_target_collision(folder, "nota.txt")
        self.assertEqual(os.path.basename(new_path), "nota (1).txt")

        # Crear el archivo "nota (1).txt" y verificar siguiente incremento
        with open(new_path, "w") as f:
            f.write("versión 2")

        new_path_2 = self.organizer.resolve_target_collision(folder, "nota.txt")
        self.assertEqual(os.path.basename(new_path_2), "nota (2).txt")

    def test_dry_run_simulation(self):
        """Verifica que el modo simulación no modifique la estructura en disco."""
        file_to_scan = os.path.join(self.test_dir, "reporte.docx")
        with open(file_to_scan, "w") as f:
            f.write("contenido simulado")

        tasks = self.organizer.scan_files(self.test_dir, self.test_dir, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].filename, "reporte.docx")

        results = self.organizer.execute_tasks(tasks, dry_run=True)
        self.assertEqual(results[0].status, "Simulado")
        # El archivo original debe seguir en su ubicación original
        self.assertTrue(os.path.exists(file_to_scan))

    def test_real_move_execution(self):
        """Verifica que el movimiento real mueva físicamente el archivo a la subcarpeta correcta."""
        file_to_move = os.path.join(self.test_dir, "imagen.png")
        with open(file_to_move, "w") as f:
            f.write("datos imagen")

        tasks = self.organizer.scan_files(self.test_dir, self.test_dir, OrganizationMode.CATEGORY)
        self.assertEqual(len(tasks), 1)

        results = self.organizer.execute_tasks(tasks, dry_run=False)
        self.assertEqual(results[0].status, "Movido")

        # El original ya no debe existir en la raíz
        self.assertFalse(os.path.exists(file_to_move))
        # Debe existir en la subcarpeta Imágenes
        expected_path = os.path.join(self.test_dir, "Imágenes", "imagen.png")
        self.assertTrue(os.path.exists(expected_path))


if __name__ == "__main__":
    unittest.main()
