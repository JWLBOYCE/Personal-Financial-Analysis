"""CSV importer for bank statements."""

from __future__ import annotations

import csv
import os
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
ARCHIVE_DIR = os.path.join(BASE_DIR, "archived")
DB_PATH = os.path.join(BASE_DIR, "demo", "demo_finance.db") if DEMO_MODE else os.path.join(BASE_DIR, "data", "finance.db")

if DEMO_MODE and not os.path.exists(DB_PATH):
    sql_path = os.path.join(BASE_DIR, "demo", "demo_finance.sql")
    conn = sqlite3.connect(DB_PATH)
    with open(sql_path, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.close()


def _find_column(columns: List[str], names: List[str]) -> Optional[str]:
    for name in names:
        if name in columns:
            return name
    return None


def parse_csv(file_path: str, mapping: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    """Parse a CSV bank statement and return standardized transactions."""
    df = pd.read_csv(file_path)
    df.columns = [c.strip().lower() for c in df.columns]

    if mapping:
        mapping = {k: v.lower() for k, v in mapping.items()}
        date_col = mapping.get("date")
        desc_col = mapping.get("description")
        amount_col = mapping.get("amount")
    else:
        date_col = _find_column(
            df.columns.tolist(),
            ["date", "transaction date", "posted date", "created"],
        )
        desc_col = _find_column(
            df.columns.tolist(),
            ["description", "memo", "reference", "details", "transaction description"],
        )
        amount_col = _find_column(df.columns.tolist(), ["amount", "value"])


    if amount_col is None:
        credit_col = _find_column(
            df.columns.tolist(), ["money in", "credit amount", "paid in", "credit"]
        )
        debit_col = _find_column(
            df.columns.tolist(), ["money out", "debit amount", "paid out", "debit"]
        )
        if credit_col or debit_col:
            credit = df.get(credit_col, 0).fillna(0)
            debit = df.get(debit_col, 0).fillna(0)
            df["amount"] = credit - debit
            amount_col = "amount"

    if date_col is None or desc_col is None or amount_col is None:
        raise ValueError("Required columns not found in CSV")

    transactions: List[Dict[str, Any]] = []
    for _, row in df.iterrows():
        date = str(row[date_col]).strip()
        desc = str(row[desc_col]).strip()
        amt_raw = str(row[amount_col]).replace(",", "").replace("$", "")
        try:
            amount = float(amt_raw)
        except ValueError:
            continue
        transactions.append({"date": date, "description": desc, "amount": amount})

    _archive(file_path, "csv")
    return transactions


def _archive(file_path: str, file_type: str) -> None:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y-%m-%d")
    base = os.path.basename(file_path)
    name, ext = os.path.splitext(base)
    archived_name = f"{name}_{ts}{ext}"
    archived_path = os.path.join(ARCHIVE_DIR, archived_name)
    os.replace(file_path, archived_path)

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS import_logs (id INTEGER PRIMARY KEY, file_name TEXT, date TEXT, type TEXT)"
    )
    conn.execute(
        "INSERT INTO import_logs (file_name, date, type) VALUES (?, ?, ?)",
        (archived_name, ts, file_type),
    )
    conn.commit()
    conn.close()


__all__ = ["parse_csv"]
