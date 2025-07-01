"""Utilities for managing monthly data sets."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime

from config import BASE_DIR, get_db_path
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")


def _ensure_db(conn: sqlite3.Connection) -> None:
    """Ensure the required schema is present."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def _shift_date(date_str: str, new_year: int, new_month: int) -> str:
    """Return date_str with the year and month replaced."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.replace(year=new_year, month=new_month).strftime("%Y-%m-%d")


def duplicate_previous_month(
    name: str,
    start_date: str,
    end_date: str,
    db_path: str | None = None,
) -> int:
    """Create a new month by duplicating the last month's recurring transactions.

    The layout and categorisation of the previous month are copied. Only
    transactions marked as recurring are duplicated and flagged. Non-recurring
    rows are omitted, effectively clearing them from the new month. Totals are
    reset implicitly as no balances are carried over.
    """

    db_path = db_path or get_db_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _ensure_db(conn)

    cur = conn.execute(
        "SELECT id, start_date, end_date FROM months ORDER BY id DESC LIMIT 1"
    )
    prev = cur.fetchone()

    cur = conn.execute(
        "INSERT INTO months (name, start_date, end_date) VALUES (?, ?, ?)",
        (name, start_date, end_date),
    )
    new_month_id = cur.lastrowid

    if prev is None:
        conn.commit()
        conn.close()
        return new_month_id

    prev_start = prev["start_date"]
    prev_end = prev["end_date"]
    prev_year, prev_month = [int(x) for x in prev_start.split("-")[:2]]
    new_year, new_month = [int(x) for x in start_date.split("-")[:2]]

    cur = conn.execute(
        """
        SELECT date, description, amount, category, type, is_recurring,
               source_account, notes
        FROM transactions
        WHERE date BETWEEN ? AND ?
        """,
        (prev_start, prev_end),
    )
    rows = cur.fetchall()

    for row in rows:
        if not row["is_recurring"]:
            continue
        new_date = _shift_date(row["date"], new_year, new_month)
        conn.execute(
            """
            INSERT INTO transactions (
                date, description, amount, category, type, is_recurring,
                source_account, notes
            ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
            """,
            (
                new_date,
                row["description"],
                row["amount"],
                row["category"],
                row["type"],
                row["source_account"],
                row["notes"],
            ),
        )

    conn.commit()
    conn.close()
    return new_month_id


__all__ = ["duplicate_previous_month"]
