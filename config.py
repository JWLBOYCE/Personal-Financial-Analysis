import os
import sqlite3

BASE_DIR = os.path.dirname(__file__)
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"


def get_db_path() -> str:
    """Return path to the active database, creating demo DB if needed."""
    if DEMO_MODE:
        path = os.path.join(BASE_DIR, "demo", "demo_finance.db")
        if not os.path.exists(path):
            sql_path = os.path.join(BASE_DIR, "demo", "demo_finance.sql")
            conn = sqlite3.connect(path)
            with open(sql_path, "r", encoding="utf-8") as f:
                conn.executescript(f.read())
            conn.close()
        return path
    return os.path.join(BASE_DIR, "data", "finance.db")
