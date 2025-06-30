import sqlite3
from dataclasses import dataclass
from typing import Optional
import tkinter as tk
from tkinter import simpledialog

DB_PATH = 'finance.db'

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
    cur.execute(
        """
        SELECT category FROM mappings
        WHERE ? LIKE '%' || keyword || '%'
        AND ? BETWEEN min_amount AND max_amount
        LIMIT 1
        """,
        (description, amount),
    )
    row = cur.fetchone()
    return row[0] if row else None


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


def categorise_transaction(description: str, amount: float, db_path: str = DB_PATH) -> Transaction:
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
