"""SQLite storage for offline receipt history and settings."""

from __future__ import annotations

import json
import shutil
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

from .paths import backup_dir, database_path


PRODUCT_NAME = "Signature Smoked Guinea Fowl"
DEFAULT_PRICE = 14000
DEFAULT_DELIVERY_FEE = 0


@dataclass
class Document:
    id: int
    number: str
    kind: str  # invoice | receipt
    customer_name: str
    customer_phone: str
    product_name: str
    quantity: int
    unit_price: int
    preparation: str
    fulfilment: str
    delivery_fee: int
    subtotal: int
    total: int
    amount_paid: int
    payment_status: str  # unpaid | paid
    notes: str
    created_at: str


@dataclass
class Settings:
    product_name: str = PRODUCT_NAME
    unit_price: int = DEFAULT_PRICE
    delivery_fee: int = DEFAULT_DELIVERY_FEE
    business_phone: str = ""
    business_note: str = "Thank you for choosing KING'S GRILLZ!"


class Connection(sqlite3.Connection):
    def __exit__(self, exc_type, exc, tb):
        try:
            super().__exit__(exc_type, exc, tb)
        finally:
            self.close()


def connect(path: Path | None = None) -> Connection:
    db = path or database_path()
    db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db, factory=Connection)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(path: Path | None = None) -> None:
    with connect(path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY,
                number TEXT NOT NULL UNIQUE,
                kind TEXT NOT NULL,
                customer_name TEXT NOT NULL,
                customer_phone TEXT NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price INTEGER NOT NULL,
                preparation TEXT NOT NULL,
                fulfilment TEXT NOT NULL,
                delivery_fee INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                total INTEGER NOT NULL,
                amount_paid INTEGER NOT NULL,
                payment_status TEXT NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS counters (
                day TEXT PRIMARY KEY,
                value INTEGER NOT NULL
            );
            """
        )


def next_number(conn: sqlite3.Connection, when: datetime | None = None) -> str:
    when = when or datetime.now()
    day = when.strftime("%Y%m%d")
    row = conn.execute("SELECT value FROM counters WHERE day = ?", (day,)).fetchone()
    value = (row["value"] if row else 0) + 1
    conn.execute(
        "INSERT INTO counters(day, value) VALUES(?, ?) "
        "ON CONFLICT(day) DO UPDATE SET value = excluded.value",
        (day, value),
    )
    return f"KG-{day}-{value:04d}"


def save_document(doc: dict, path: Path | None = None) -> Document:
    init_db(path)
    with connect(path) as conn:
        number = next_number(conn)
        created = datetime.now().isoformat(timespec="seconds")
        cur = conn.execute(
            """
            INSERT INTO documents (
                number, kind, customer_name, customer_phone, product_name,
                quantity, unit_price, preparation, fulfilment, delivery_fee,
                subtotal, total, amount_paid, payment_status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                number, doc["kind"], doc["customer_name"], doc["customer_phone"],
                doc["product_name"], doc["quantity"], doc["unit_price"],
                doc["preparation"], doc["fulfilment"], doc["delivery_fee"],
                doc["subtotal"], doc["total"], doc["amount_paid"],
                doc["payment_status"], doc.get("notes", ""), created,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (cur.lastrowid,)).fetchone()
        return Document(**dict(row))


def list_documents(query: str = "", path: Path | None = None) -> list[Document]:
    init_db(path)
    with connect(path) as conn:
        if query.strip():
            like = f"%{query.strip()}%"
            rows = conn.execute(
                """
                SELECT * FROM documents
                WHERE number LIKE ? OR customer_name LIKE ? OR customer_phone LIKE ?
                   OR product_name LIKE ? OR payment_status LIKE ?
                ORDER BY id DESC
                """,
                (like, like, like, like, like),
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
        return [Document(**dict(row)) for row in rows]


def get_document(doc_id: int, path: Path | None = None) -> Document | None:
    init_db(path)
    with connect(path) as conn:
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return Document(**dict(row)) if row else None


def mark_paid(doc_id: int, path: Path | None = None) -> Document | None:
    """Explicit conversion of an invoice to a paid receipt. Never automatic."""
    init_db(path)
    with connect(path) as conn:
        conn.execute(
            """
            UPDATE documents
            SET kind = 'receipt', payment_status = 'paid', amount_paid = total
            WHERE id = ? AND payment_status != 'paid'
            """,
            (doc_id,),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,)).fetchone()
        return Document(**dict(row)) if row else None


def load_settings(path: Path | None = None) -> Settings:
    init_db(path)
    with connect(path) as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = 'app'").fetchone()
        if not row:
            return Settings()
        data = json.loads(row["value"])
        return Settings(**{**asdict(Settings()), **data})


def save_settings(settings: Settings, path: Path | None = None) -> None:
    init_db(path)
    with connect(path) as conn:
        conn.execute(
            "INSERT INTO settings(key, value) VALUES('app', ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (json.dumps(asdict(settings)),),
        )
        conn.commit()


def backup_database(destination: Path | None = None) -> Path:
    source = database_path()
    init_db(source)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = destination or (backup_dir() / f"receipts-{stamp}.db")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def restore_database(source: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Backup not found: {source}")
    init_db()
    shutil.copy2(source, database_path())
