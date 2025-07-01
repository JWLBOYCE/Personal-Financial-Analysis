"""Transaction categorization logic."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from difflib import SequenceMatcher
from typing import Optional, Tuple, List, Iterable
import shutil
import glob

from PyQt5 import QtWidgets

from config import BASE_DIR, get_db_path
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def _ensure_db(conn: sqlite3.Connection) -> None:
    """Ensure required tables exist using the schema."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def _backup_db(db_path: str | None = None) -> None:
    """Create a timestamped backup of the database and keep only 5 recent."""
    db_path = db_path or get_db_path()
    backup_dir = os.path.dirname(db_path)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_finance_{timestamp}.bak"
    backup_path = os.path.join(backup_dir, backup_name)
    os.makedirs(backup_dir, exist_ok=True)
    shutil.copy2(db_path, backup_path)

    backups = sorted(
        glob.glob(os.path.join(backup_dir, "backup_finance_*.bak")),
        reverse=True,
    )
    for old in backups[5:]:
        try:
            os.remove(old)
        except OSError:
            pass


class Categoriser:
    """Classify transactions using stored mappings."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path = db_path or get_db_path()
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        _ensure_db(self.conn)

    def classify(self, description: str, amount: float, parent: Optional[QtWidgets.QWidget] = None) -> Tuple[Optional[int], bool]:
        """Classify a transaction and detect if it is recurring."""
        category_id, confidence = self._lookup_mapping(description, amount)
        if category_id is None or confidence < 90:
            category_id = self._prompt_user(description, parent)
            if category_id is not None:
                keyword = self._prompt_keyword(description, parent)
                if keyword:
                    self._save_mapping(keyword, category_id, amount)
        return category_id, self._is_recurring(description, amount)

    def _lookup_mapping(self, desc: str, amt: float) -> Tuple[Optional[int], float]:
        cur = self.conn.execute(
            "SELECT id, keyword, category_id, min_amount, max_amount FROM mappings"
        )
        best_id: Optional[int] = None
        best_score = 0.0
        best_row_id: Optional[int] = None
        for row in cur.fetchall():
            score = (
                SequenceMatcher(None, row["keyword"].lower(), desc.lower()).ratio() * 100
            )
            if score > best_score and row["min_amount"] <= amt <= row["max_amount"]:
                best_score = score
                best_id = row["category_id"]
                best_row_id = row["id"]
        if best_id is not None and best_score >= 90:
            self.conn.execute(
                "UPDATE mappings SET last_used = ? WHERE id = ?",
                (datetime.now().isoformat(), best_row_id),
            )
            self.conn.commit()
            return best_id, best_score
        return None, 0.0


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

    def _save_mapping(self, keyword: str, category_id: int, amount: float) -> None:
        self.conn.execute(
            "INSERT INTO mappings (keyword, min_amount, max_amount, category_id, recurring_guess, last_used) VALUES (?, ?, ?, ?, 0, ?)",
            (
                keyword,
                amount * 0.95,
                amount * 1.05,
                category_id,
                datetime.now().isoformat(),
            ),
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
import sqlite3
from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from tkinter import simpledialog

DB_PATH = get_db_path()

@dataclass
class Transaction:
    description: str
    amount: float
    category: Optional[str] = None
    is_recurring: bool = False


def _ensure_tables(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS mappings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            min_amount REAL NOT NULL,
            max_amount REAL NOT NULL,
            category TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            is_recurring INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


def _search_mapping(conn: sqlite3.Connection, description: str, amount: float) -> Optional[str]:
    cur = conn.cursor()
    cur.execute("SELECT id, keyword, category, min_amount, max_amount FROM mappings")
    best_cat: Optional[str] = None
    best_score = 0.0
    for row in cur.fetchall():
        score = SequenceMatcher(None, row["keyword"].lower(), description.lower()).ratio() * 100
        if score > best_score and row["min_amount"] <= amount <= row["max_amount"]:
            best_score = score
            best_cat = row["category"]
    if best_score >= 90:
        return best_cat
    return None


def _save_mapping(conn: sqlite3.Connection, keyword: str, amount: float, category: str) -> None:
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO mappings (keyword, min_amount, max_amount, category)
        VALUES (?, ?, ?, ?)
        """,
        (keyword, amount * 0.95, amount * 1.05, category),
    )
    conn.commit()


def _prompt_user_for_category(description: str) -> str:
    root = tk.Tk()
    root.withdraw()
    category = simpledialog.askstring(
        "Categorise Transaction",
        f"Enter category for:\n{description}"
    )
    root.destroy()
    if not category:
        raise ValueError("Category cannot be empty")
    return category


def _detect_recurring(conn: sqlite3.Connection, description: str, amount: float) -> bool:
    cur = conn.cursor()
    cur.execute(
        """
        SELECT COUNT(*) FROM transactions
        WHERE description = ? AND ABS(amount - ?) < 0.01
        """,
        (description, amount),
    )
    count = cur.fetchone()[0]
    return count >= 2


def categorise_transaction(description: str, amount: float, db_path: str | None = None) -> Transaction:
    db_path = db_path or get_db_path()
    conn = sqlite3.connect(db_path)
    try:
        _ensure_tables(conn)
        category = _search_mapping(conn, description, amount)
        if category is None:
            category = _prompt_user_for_category(description)
            keyword = description.split()[0]
            _save_mapping(conn, keyword, amount, category)
        is_recurring = _detect_recurring(conn, description, amount)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO transactions (description, amount, category, is_recurring)
            VALUES (?, ?, ?, ?)
            """,
            (description, amount, category, int(is_recurring)),
        )
        conn.commit()
        return Transaction(description, amount, category, is_recurring)
    finally:
        conn.close()


def categorise_transactions(transactions: Iterable[tuple[str, float]], db_path: str | None = None) -> list[Transaction]:
    db_path = db_path or get_db_path()
    """Categorise multiple transactions and backup the database."""
    results = []
    for desc, amt in transactions:
        results.append(categorise_transaction(desc, amt, db_path))
    _backup_db(db_path)
    return results
