from __future__ import annotations

import os
import sqlite3
import tempfile
import json
from datetime import datetime
from typing import Iterable

import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .projection_engine import generate_projection

DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = (
    os.path.join(BASE_DIR, "demo", "demo_finance.db")
    if DEMO_MODE
    else os.path.join(BASE_DIR, "data", "finance.db")
)
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")

THEMES = {
    "Personal": {"font": "Helvetica", "grid": False, "charts_first": False},
    "Executive": {"font": "Times-Roman", "grid": True, "charts_first": False},
    "Investor": {"font": "Helvetica", "grid": True, "charts_first": True},
}

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


def _cleanup(paths: Iterable[str]) -> None:
    for p in paths:
        try:
            os.remove(p)
        except Exception:
            pass


def generate_monthly_report(
    month_id: str,
    output_path: str,
    tone: str = "formal",
    theme: str = "Personal",
    logo_path: str | None = None,
    footer: str = "",
) -> None:
    """Generate a PDF financial summary for ``month_id``.

    Parameters
    ----------
    month_id:
        Month identifier (id or name).
    output_path:
        Destination PDF path.
    tone:
        Writing tone for the report ("formal" or "plain").
    theme:
        Visual theme to apply ("Personal", "Executive" or "Investor").
    logo_path:
        Optional logo image to embed.
    footer:
        Footer text shown on each page.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_db(conn)

    cur = conn.execute(
        "SELECT id, name, start_date, end_date FROM months WHERE id = ? OR name = ?",
        (month_id, month_id),
    )
    month = cur.fetchone()
    if not month:
        conn.close()
        raise ValueError(f"Month {month_id} not found")

    start_date = month["start_date"]
    end_date = month["end_date"]

    cur = conn.execute(
        "SELECT type, SUM(amount) AS total FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type",
        (start_date, end_date),
    )
    totals = {"income": 0.0, "expense": 0.0}
    for row in cur.fetchall():
        totals[row["type"]] = row["total"] or 0.0
    net = totals.get("income", 0.0) - abs(totals.get("expense", 0.0))

    cur = conn.execute(
        """
        SELECT c.name AS category, SUM(t.amount) AS total
        FROM transactions t
        LEFT JOIN categories c ON t.category = c.id
        WHERE t.date BETWEEN ? AND ?
        GROUP BY t.category
        """,
        (start_date, end_date),
    )
    cat_labels: list[str] = []
    cat_values: list[float] = []
    for row in cur.fetchall():
        cat_labels.append(row["category"] or "Uncategorised")
        cat_values.append(abs(row["total"] or 0.0))

    # Net worth history
    cur = conn.execute(
        "SELECT name, start_date, end_date FROM months ORDER BY start_date"
    )
    history = cur.fetchall()
    dates = []
    net_worth_values = []
    running_total = 0.0
    month_net_worth = 0.0
    for row in history:
        cur2 = conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE date BETWEEN ? AND ?",
            (row["start_date"], row["end_date"]),
        )
        total = cur2.fetchone()[0] or 0.0
        running_total += total
        dates.append(row["name"])
        net_worth_values.append(running_total)
        if row["name"] == month["name"]:
            month_net_worth = running_total

    conn.close()

    temp_files: list[str] = []
    try:
        net_chart = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_files.append(net_chart.name)
        plt.figure(figsize=(4, 2.5))
        plt.plot(dates, net_worth_values, marker="o")
        plt.title("Net Worth Over Time")
        plt.xticks(rotation=45, ha="right")
        plt.tight_layout()
        plt.savefig(net_chart.name)
        plt.close()

        cash_chart = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_files.append(cash_chart.name)
        plt.figure(figsize=(4, 2.5))
        plt.bar(["Income", "Expenses"], [totals["income"], abs(totals["expense"])] )
        plt.title("Cashflow")
        plt.tight_layout()
        plt.savefig(cash_chart.name)
        plt.close()

        pie_chart = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temp_files.append(pie_chart.name)
        if cat_values:
            plt.figure(figsize=(4, 2.5))
            plt.pie(cat_values, labels=cat_labels, autopct="%1.1f%%")
            plt.title("Spending by Category")
            plt.tight_layout()
            plt.savefig(pie_chart.name)
            plt.close()

        styles = getSampleStyleSheet()
        theme_cfg = THEMES.get(theme, THEMES["Personal"])
        styles["Normal"].fontName = theme_cfg["font"]
        styles["Heading1"].fontName = theme_cfg["font"]

        proj = generate_projection(month["name"], months_ahead=1)
        projection_delta = 0.0
        if proj:
            first_month = next(iter(proj.values()))
            projection_delta = first_month.get("net", 0.0)

        doc = SimpleDocTemplate(output_path, pagesize=A4)

        elements = []
        elements.append(Paragraph(f"{month['name']} Financial Summary", styles["Heading1"]))
        elements.append(Paragraph(f"{start_date} to {end_date}", styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))

        data = [
            ["Total Income", f"{totals['income']:.2f}"],
            ["Total Expenses", f"{abs(totals['expense']):.2f}"],
            ["Net Cashflow", f"{net:.2f}"],
        ]
        tbl = Table(data, hAlign="LEFT")
        if theme_cfg.get("grid", False):
            tbl.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, "black")]))
        elements_tbl = [tbl, Spacer(1, 0.2 * inch)]

        charts = [
            Image(net_chart.name, width=5 * inch, height=3 * inch),
            Spacer(1, 0.1 * inch),
            Image(cash_chart.name, width=5 * inch, height=3 * inch),
        ]
        if cat_values:
            charts += [Spacer(1, 0.1 * inch), Image(pie_chart.name, width=5 * inch, height=3 * inch)]

        if theme_cfg.get("charts_first", False):
            elements.extend(charts)
            elements.append(Spacer(1, 0.2 * inch))
            elements.extend(elements_tbl)
        else:
            elements.extend(elements_tbl)
            elements.extend(charts)

        def _on_page(canvas, _doc):
            if logo_path and os.path.exists(logo_path):
                img_w = 1.0 * inch
                x = A4[0] - img_w - 0.5 * inch
                y = A4[1] - 1.0 * inch
                canvas.drawImage(logo_path, x, y, width=img_w, preserveAspectRatio=True, mask='auto')
            if footer:
                canvas.setFont(theme_cfg["font"], 9)
                canvas.drawCentredString(A4[0] / 2, 0.5 * inch, footer)

        doc.build(elements, onFirstPage=_on_page, onLaterPages=_on_page)

        meta = {
            "month": month["name"],
            "net_worth": month_net_worth,
            "income_total": totals["income"],
            "expense_total": abs(totals["expense"]),
            "projection_delta": projection_delta,
        }
        json_path = os.path.splitext(output_path)[0] + ".json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2)
    finally:
        _cleanup(temp_files)


__all__ = ["generate_monthly_report"]
