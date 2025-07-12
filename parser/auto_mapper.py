"""Utilities to guess column mappings for CSV imports."""

from __future__ import annotations

from difflib import SequenceMatcher
from typing import List, Dict

KEYWORDS = {
    "date": ["date", "transaction date", "posted date"],
    "description": ["description", "details", "merchant", "narrative"],
    "amount": ["amount", "value", "debit", "credit"],
}


def _fuzzy_match(target: str, options: List[str]) -> float:
    """Return the best fuzzy match score for target against options."""
    target = target.lower()
    return max(SequenceMatcher(None, target, opt).ratio() for opt in options)


def guess_column_mapping(header_row: List[str], sample_row: List[str]) -> Dict[str, str]:
    """Guess mapping from standard keys to CSV column names."""
    lower_headers = [h.strip().lower() for h in header_row]
    mapping: Dict[str, str] = {}

    for key, options in KEYWORDS.items():
        best_col = None
        best_score = 0.0
        for col in lower_headers:
            score = _fuzzy_match(col, options)
            if score > best_score:
                best_col = col
                best_score = score
        if best_score >= 0.6 and best_col is not None:
            mapping[key] = best_col

    # Fallback using sample row to detect numeric amount column
    if "amount" not in mapping and sample_row:
        for col, value in zip(lower_headers, sample_row):
            cleaned = str(value).replace(",", "").replace("£", "").replace("$", "")
            try:
                float(cleaned)
            except ValueError:
                continue
            mapping["amount"] = col
            break

    return mapping


__all__ = ["guess_column_mapping"]
