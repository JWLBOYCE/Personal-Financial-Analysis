import os
import sqlite3
import types
import sys
import unittest
from tempfile import TemporaryDirectory

# Stub external GUI dependencies
qt_module = types.ModuleType("QtWidgets")
sys.modules.setdefault("PyQt5", types.ModuleType("PyQt5"))
sys.modules["PyQt5"].QtWidgets = qt_module
sys.modules.setdefault("PyQt5.QtWidgets", qt_module)

from logic.month_manager import duplicate_previous_month
from logic.categoriser import Categoriser


class MonthManagerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        with sqlite3.connect(self.db_path) as conn:
            with open("schema.sql", "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.execute(
                "INSERT INTO months (name, start_date, end_date) VALUES (?, ?, ?)",
                ("May 2025", "2025-05-01", "2025-05-31"),
            )
            conn.execute(
                "INSERT INTO categories (name, type) VALUES ('Rent', 'expense')"
            )
            conn.execute(
                "INSERT INTO transactions (date, description, amount, category, type, is_recurring) VALUES (?, ?, ?, 1, 'expense', 1)",
                ("2025-05-10", "Rent payment", -1000.0),
            )
            conn.execute(
                "INSERT INTO transactions (date, description, amount, category, type, is_recurring) VALUES (?, ?, ?, 1, 'expense', 0)",
                ("2025-05-15", "One-off", -50.0),
            )
            conn.commit()

    def tearDown(self):
        self.tmp.cleanup()

    def test_duplicate_previous_month(self):
        new_id = duplicate_previous_month(
            "June 2025", "2025-06-01", "2025-06-30", db_path=self.db_path
        )
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.execute("SELECT name FROM months WHERE id = ?", (new_id,))
            self.assertEqual(cur.fetchone()[0], "June 2025")
            cur = conn.execute(
                "SELECT date, description FROM transactions WHERE date BETWEEN ? AND ?",
                ("2025-06-01", "2025-06-30"),
            )
            rows = cur.fetchall()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0][1], "Rent payment")
            self.assertEqual(rows[0][0], "2025-06-10")


class CategoriserTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "test.db")
        with sqlite3.connect(self.db_path) as conn:
            with open("schema.sql", "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.execute(
                "INSERT INTO categories (id, name, type) VALUES (1, 'Groceries', 'expense')"
            )
            conn.execute(
                "INSERT INTO mappings (keyword, category_id, recurring_guess, last_used) VALUES ('waitrose', 1, 0, NULL)"
            )
            conn.execute(
                "INSERT INTO transactions (date, description, amount, category, type, is_recurring) VALUES ('2025-05-01', 'Waitrose!!! Grocery', -10.0, 1, 'expense', 1)"
            )
            conn.execute(
                "INSERT INTO transactions (date, description, amount, category, type, is_recurring) VALUES ('2025-05-08', 'Waitrose!!! Grocery', -10.0, 1, 'expense', 1)"
            )
            conn.commit()
        self.categoriser = Categoriser(db_path=self.db_path)

    def tearDown(self):
        self.categoriser.conn.close()
        self.tmp.cleanup()

    def test_irregular_description_recognition(self):
        desc = "  Waitrose!!!   Grocery  "
        cat_id, recurring = self.categoriser.classify(desc, -10.0)
        self.assertEqual(cat_id, 1)
        self.assertTrue(recurring)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.db_path = os.path.join(self.tmp.name, "db.sqlite")
        self.archive = os.path.join(self.tmp.name, "archived")
        os.makedirs(self.archive)
        with sqlite3.connect(self.db_path) as conn:
            pass
        self._patch_modules()
        import importlib
        self.csv_importer = importlib.reload(__import__("parser.csv_importer", fromlist=["*"]))
        self.csv_importer.ARCHIVE_DIR = self.archive
        self.csv_importer.DB_PATH = self.db_path

    def tearDown(self):
        self.tmp.cleanup()
        self._restore_modules()

    def _patch_modules(self):
        self.old_pandas = sys.modules.get("pandas")
        self.old_pdfplumber = sys.modules.get("pdfplumber")
        sys.modules["pandas"] = types.ModuleType("pandas")
        sys.modules["pdfplumber"] = types.ModuleType("pdfplumber")

    def _restore_modules(self):
        if self.old_pandas is not None:
            sys.modules["pandas"] = self.old_pandas
        else:
            sys.modules.pop("pandas", None)
        if self.old_pdfplumber is not None:
            sys.modules["pdfplumber"] = self.old_pdfplumber
        else:
            sys.modules.pop("pdfplumber", None)

    def test_archive_log_and_move(self):
        src = os.path.join(self.tmp.name, "file.csv")
        with open(src, "w") as f:
            f.write("dummy")
        self.csv_importer._archive(src, "csv")
        files = os.listdir(self.archive)
        self.assertEqual(len(files), 1)
        archived = os.path.join(self.archive, files[0])
        self.assertTrue(os.path.exists(archived))
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT file_name, type FROM import_logs"
            ).fetchone()
            self.assertEqual(row["type"], "csv")
            self.assertEqual(row["file_name"], os.path.basename(archived))


if __name__ == "__main__":
    unittest.main()
