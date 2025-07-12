"""Cashflow projection utilities."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from typing import Dict, Any

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = (
    os.path.join(BASE_DIR, "demo", "demo_finance.db")
    if DEMO_MODE
    else os.path.join(BASE_DIR, "data", "finance.db")
)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

if DEMO_MODE and not os.path.exists(DB_PATH):
    sql_path = os.path.join(BASE_DIR, "demo", "demo_finance.sql")
    conn = sqlite3.connect(DB_PATH)
    with open(sql_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


def _ensure_db(conn: sqlite3.Connection) -> None:
    """Ensure required tables exist."""
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())


def _add_months(date_str: str, months: int) -> datetime:
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    year = dt.year + (dt.month - 1 + months) // 12
    month = (dt.month - 1 + months) % 12 + 1
    return dt.replace(year=year, month=month, day=1)


def generate_projection(month_id: str, months_ahead: int = 3) -> Dict[str, Any]:
    """Return cashflow projection for the next ``months_ahead`` months."""
    if months_ahead <= 0:
        return {}

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_db(conn)

    cur = conn.execute(
        "SELECT start_date FROM months WHERE id = ? OR name = ?",
        (month_id, month_id),
    )
    row = cur.fetchone()
    if not row:
        conn.close()
        raise ValueError(f"Month {month_id} not found")
    start_date = row["start_date"]

    # Average monthly totals for non-recurring transactions
    cur = conn.execute(
        """
        SELECT c.name AS category, t.type, AVG(month_total) AS avg_amount
        FROM (
            SELECT category, type, strftime('%Y-%m', date) AS ym,
                   SUM(amount) AS month_total
            FROM transactions
            WHERE date < ? AND (is_recurring = 0 OR is_recurring IS NULL)
            GROUP BY category, type, ym
        ) t
        LEFT JOIN categories c ON t.category = c.id
        GROUP BY t.category, t.type
        """,
        (start_date,),
    )
    averages = {"income": {}, "expense": {}}
    for r in cur.fetchall():
        cat = r["category"] or "Uncategorised"
        amt = r["avg_amount"] or 0.0
        averages[r["type"]][cat] = abs(amt)

    # Recurring transactions averaged separately
    cur = conn.execute(
        """
        SELECT c.name AS category, type, AVG(amount) AS avg_amount
        FROM transactions
        LEFT JOIN categories c ON category = c.id
        WHERE is_recurring = 1 AND date < ?
        GROUP BY category, type
        """,
        (start_date,),
    )
    for r in cur.fetchall():
        cat = r["category"] or "Uncategorised"
        amt = r["avg_amount"] or 0.0
        averages[r["type"]].setdefault(cat, 0.0)
        averages[r["type"]][cat] += abs(amt)

    projection: Dict[str, Any] = {}
    base_dt = datetime.strptime(start_date, "%Y-%m-%d")
    for i in range(1, months_ahead + 1):
        m_dt = _add_months(start_date, i)
        label = m_dt.strftime("%b %Y")
        incomes = averages.get("income", {}).copy()
        expenses = averages.get("expense", {}).copy()
        total_income = sum(incomes.values())
        total_expense = sum(expenses.values())
        net = total_income - total_expense
        projection[label] = {
            "income": incomes,
            "expenses": expenses,
            "net": net,
            "negative": net < 0,
        }

    conn.close()
    return projection


__all__ = ["generate_projection"]
