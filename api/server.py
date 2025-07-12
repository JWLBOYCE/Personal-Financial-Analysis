import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, jsonify, request, abort
from flask_cors import CORS
from dotenv import load_dotenv

from logic.categoriser import DB_PATH, _ensure_db

load_dotenv()

logging.basicConfig(
    filename="access.log",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)

app = Flask(__name__)
CORS(app, resources={r"*": {"origins": ["http://localhost", "http://127.0.0.1"]}})

API_TOKEN = os.getenv("ACCESS_TOKEN") or os.getenv("API_TOKEN")
USE_NGROK = os.getenv("USE_NGROK", "false").lower() == "true"
SSL_CERT = os.getenv("SSL_CERT", os.path.join("certs", "cert.pem"))
SSL_KEY = os.getenv("SSL_KEY", os.path.join("certs", "key.pem"))


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_db(conn)
    return conn


def _log_access(ok: bool) -> None:
    ip = request.remote_addr or "unknown"
    status = "OK" if ok else "DENIED"
    logging.info(f"{ip} {request.path} {status}")


def _check_auth() -> None:
    if not API_TOKEN:
        return
    auth = request.headers.get("Authorization", "")
    ok = auth == f"Bearer {API_TOKEN}"
    _log_access(ok)
    if not ok:
        abort(401)


@app.route("/months", methods=["GET"])
def get_months():
    _check_auth()
    conn = _get_conn()
    cur = conn.execute(
        "SELECT id, name, start_date, end_date FROM months ORDER BY start_date"
    )
    months = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(months)


@app.route("/transactions/<int:month_id>", methods=["GET"])
def get_transactions(month_id: int):
    _check_auth()
    conn = _get_conn()
    cur = conn.execute("SELECT start_date, end_date FROM months WHERE id = ?", (month_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        abort(404)
    start, end = row["start_date"], row["end_date"]
    cur = conn.execute(
        "SELECT * FROM transactions WHERE date BETWEEN ? AND ? ORDER BY date",
        (start, end),
    )
    transactions = [dict(r) for r in cur.fetchall()]
    conn.close()
    return jsonify(transactions)


@app.route("/categories", methods=["GET"])
def get_categories():
    _check_auth()
    conn = _get_conn()
    cur = conn.execute("SELECT id, name, type FROM categories ORDER BY name")
    categories = [dict(row) for row in cur.fetchall()]
    conn.close()
    return jsonify(categories)


@app.route("/summary/<int:month_id>", methods=["GET"])
def get_summary(month_id: int):
    _check_auth()
    conn = _get_conn()
    cur = conn.execute("SELECT start_date, end_date FROM months WHERE id = ?", (month_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        abort(404)
    start, end = row["start_date"], row["end_date"]
    cur = conn.execute(
        "SELECT type, SUM(amount) as total FROM transactions WHERE date BETWEEN ? AND ? GROUP BY type",
        (start, end),
    )
    totals = {r["type"]: r["total"] for r in cur.fetchall()}
    income = totals.get("income", 0.0) or 0.0
    expenses = totals.get("expense", 0.0) or 0.0
    summary = {
        "income": income,
        "expenses": abs(expenses),
        "net": income + expenses,
    }
    conn.close()
    return jsonify(summary)


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    if USE_NGROK:
        try:
            from pyngrok import ngrok

            public_url = ngrok.connect(port, bind_tls=True).public_url
            print(f" * ngrok tunnel available at {public_url}")
        except Exception as exc:
            print(f"Failed to start ngrok tunnel: {exc}")
    app.run(host="0.0.0.0", port=port, ssl_context=(SSL_CERT, SSL_KEY))
