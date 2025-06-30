"""CSV importer for bank statements."""

from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

import pandas as pd

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "archived")


def _find_column(columns: List[str], names: List[str]) -> Optional[str]:
    for name in names:
        if name in columns:
            return name
    return None


def parse_csv(file_path: str) -> List[Dict[str, Any]]:
    """Parse a CSV bank statement and return standardized transactions."""
    df = pd.read_csv(file_path)
    df.columns = [c.strip().lower() for c in df.columns]

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

    _archive(file_path)
    return transactions


def _archive(file_path: str) -> None:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(file_path)
    archived_path = os.path.join(ARCHIVE_DIR, f"{ts}_{base}")
    os.replace(file_path, archived_path)


__all__ = ["parse_csv"]
