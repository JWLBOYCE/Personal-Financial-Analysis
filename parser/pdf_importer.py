"""PDF importer for bank statements using pdfplumber."""

from __future__ import annotations

import os
import re
from datetime import datetime
from typing import List, Dict, Any

import pdfplumber

ARCHIVE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "archived")

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

    _archive(file_path)
    return transactions


def _archive(file_path: str) -> None:
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(file_path)
    archived_path = os.path.join(ARCHIVE_DIR, f"{ts}_{base}")
    os.replace(file_path, archived_path)


__all__ = ["parse_pdf"]
