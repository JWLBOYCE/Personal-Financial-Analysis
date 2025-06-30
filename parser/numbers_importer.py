from __future__ import annotations

"""Parser for CSV files exported from Apple Numbers."""

from typing import Dict, List, Any, Tuple, Iterable
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from gui.navigation_table_widget import (
    ORIGINAL_DESC_ROLE,
    CATEGORY_METHOD_ROLE,
    IS_RECURRING_ROLE,
)
from gui.table_manager import TransactionTableManager



def _infer_type(series: Iterable[Any]) -> str:
    """Infer a column's data type as 'float', 'date', or 'str'."""
    s = pd.Series(list(series)).dropna()
    if s.empty:
        return "str"
    if pd.api.types.is_numeric_dtype(s):
        return "float"
    try:
        pd.to_datetime(s, errors="raise")
        return "date"
    except Exception:
        return "str"


def parse_numbers_csv(file_path: str) -> Dict[str, Any]:
    """Parse a Numbers-exported CSV and infer structure and metadata."""
    df = pd.read_csv(file_path)
    headers = [h.strip() for h in df.columns]

    column_types = {h: _infer_type(df[h]) for h in headers}

    section_col = None
    for name in headers:
        lowered = name.lower()
        if lowered in {"section", "type", "category"} or "section" in lowered:
            section_col = name
            break

    tag_col = None
    for name in headers:
        lowered = name.lower()
        if "tag" in lowered or "note" in lowered or "comment" in lowered:
            tag_col = name
            break

    sections: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    recurring_rows: set[int] = set()

    for idx, row in df.iterrows():
        section = str(row[section_col]).strip() if section_col else "Data"
        row_dict = {
            h: row[h] for h in headers if h != section_col
        }
        sections.setdefault(section or "Data", []).append((idx, row_dict))
        if tag_col:
            note = str(row[tag_col]).lower()
            if "recurring" in note or "#recurring" in note:
                recurring_rows.add(idx)

    headers_no_section = [h for h in headers if h != section_col]

    return {
        "headers": headers_no_section,
        "column_types": column_types,
        "sections": sections,
        "recurring_rows": recurring_rows,
    }


def create_numbers_layout(data: Dict[str, Any]) -> QtWidgets.QTabWidget:
    """Create a PyQt tab widget matching the parsed Numbers data."""
    headers: List[str] = data["headers"]
    recurring_rows: set[int] = set(data.get("recurring_rows", set()))
    widget = QtWidgets.QTabWidget()

    for section, rows in data["sections"].items():
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        table = NavigationTableWidget(0, len(headers))
        total_label = QtWidgets.QLabel("Total: 0.00")
        manager = TransactionTableManager(table, total_label)
        manager.set_headers(headers)
        layout.addWidget(table)
        layout.addWidget(total_label, alignment=QtCore.Qt.AlignRight)
        widget.addTab(page, section)

        for idx, row in rows:
            values = [row.get(h, "") for h in headers]
            manager.add_row(values, recurring=_is_recurring(idx, recurring_rows))

        manager.update_total()

    return widget


def _is_recurring(index: int, recurring_rows: set[int]) -> bool:
    return index in recurring_rows


__all__ = ["parse_numbers_csv", "create_numbers_layout", "IS_RECURRING_ROLE"]
