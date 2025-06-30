"""PDF importer for bank statements using pdfplumber."""

from __future__ import annotations

import os
import re
import sqlite3
from datetime import datetime
from typing import List, Dict, Any

import pdfplumber

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "archived")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "finance.db")

PATTERN = re.compile(
    r"(?P<date>\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+(?P<desc>.*?)\s+(?P<amt>-?\$?[\d,]+\.\d{2})$"
)


def parse_pdf(file_path: str) -> List[Dict[str, Any]]:
    """Parse a PDF bank statement and return standardized transactions."""
    transactions: List[Dict[str, Any]] = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.split("\n"):
                match = PATTERN.search(line.strip())
                if not match:
                    continue
                date = match.group("date")
                desc = match.group("desc").strip()
                amt_raw = match.group("amt").replace("$", "").replace(",", "")
                try:
                    amount = float(amt_raw)
                except ValueError:
                    continue
                transactions.append({"date": date, "description": desc, "amount": amount})

    _archive(file_path, "pdf")
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


__all__ = ["parse_pdf"]
