"""Transaction categorization logic."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Optional, Tuple

from PyQt5 import QtWidgets

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "demo", "demo_finance.db") if DEMO_MODE else os.path.join(BASE_DIR, "data", "finance.db")

if DEMO_MODE and not os.path.exists(DB_PATH):
    sql_path = os.path.join(BASE_DIR, "demo", "demo_finance.sql")
    conn = sqlite3.connect(DB_PATH)
    with open(sql_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def _ensure_db(conn: sqlite3.Connection) -> None:
    """Ensure required tables exist using the schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


class Categoriser:
    """Classify transactions using stored mappings."""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        _ensure_db(self.conn)

    def classify(self, description: str, amount: float, parent: Optional[QtWidgets.QWidget] = None) -> Tuple[Optional[int], bool]:
        """Classify a transaction and detect if it is recurring."""
        category_id = self._lookup_mapping(description, amount)
        if category_id is None:
            category_id = self._prompt_user(description, parent)
            if category_id is not None:
                keyword = self._prompt_keyword(description, parent)
                if keyword:
                    self._save_mapping(keyword, category_id)
        return category_id, self._is_recurring(description, amount)

    def _lookup_mapping(self, desc: str, amt: float) -> Optional[int]:
        cur = self.conn.execute("SELECT id, keyword, category_id FROM mappings")
        for row in cur.fetchall():
            if row["keyword"].lower() in desc.lower():
                min_amt, max_amt = self._amount_range(row["keyword"])
                if min_amt is None or (min_amt <= amt <= max_amt):
                    self.conn.execute(
                        "UPDATE mappings SET last_used = ? WHERE id = ?",
                        (datetime.now().isoformat(), row["id"]),
                    )
                    self.conn.commit()
                    return row["category_id"]
        return None

    def _amount_range(self, keyword: str) -> Tuple[Optional[float], Optional[float]]:
        cur = self.conn.execute(
            "SELECT MIN(amount), MAX(amount) FROM transactions WHERE description LIKE ?",
            (f"%{keyword}%",),
        )
        result = cur.fetchone()
        return result[0], result[1]

    def _prompt_user(self, desc: str, parent: Optional[QtWidgets.QWidget]) -> Optional[int]:
        text, ok = QtWidgets.QInputDialog.getText(
            parent, "Categorise", f"Enter category for:\n{desc}"
        )
        if not ok or not text.strip():
            return None
        cur = self.conn.execute("SELECT id FROM categories WHERE name = ?", (text.strip(),))
        row = cur.fetchone()
        if row:
            category_id = row[0]
        else:
            cur = self.conn.execute(
                "INSERT INTO categories (name, type) VALUES (?, 'expense')",
                (text.strip(),),
            )
            category_id = cur.lastrowid
            self.conn.commit()
        return category_id

    def _prompt_keyword(self, desc: str, parent: Optional[QtWidgets.QWidget]) -> Optional[str]:
        default = desc.split()[0] if desc.split() else desc
        keyword, ok = QtWidgets.QInputDialog.getText(
            parent, "Mapping Keyword", f"Keyword to map to this description:",
            text=default,
        )
        return keyword.strip().lower() if ok and keyword.strip() else None

    def _save_mapping(self, keyword: str, category_id: int) -> None:
        self.conn.execute(
            "INSERT INTO mappings (keyword, category_id, recurring_guess, last_used) VALUES (?, ?, 0, ?)",
            (keyword, category_id, datetime.now().isoformat()),
        )
        self.conn.commit()

    def _is_recurring(self, desc: str, amt: float) -> bool:
        cur = self.conn.execute(
            "SELECT COUNT(*) FROM transactions WHERE description LIKE ? AND ABS(amount - ?) < 0.01",
            (f"%{desc.split()[0]}%", amt),
        )
        count = cur.fetchone()[0]
        return count >= 2


__all__ = ["Categoriser"]
