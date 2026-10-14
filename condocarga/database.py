from contextlib import contextmanager
from pathlib import Path
import sqlite3

from .settings import DB_PATH

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS units (
    id TEXT PRIMARY KEY,
    number TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    unit_id TEXT NOT NULL REFERENCES units(id),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS vehicles (
    id TEXT PRIMARY KEY,
    unit_id TEXT NOT NULL REFERENCES units(id),
    label TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS rfid_cards (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1))
);
CREATE TABLE IF NOT EXISTS chargers (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    operational INTEGER NOT NULL DEFAULT 1 CHECK (operational IN (0, 1))
);
CREATE TABLE IF NOT EXISTS tariff_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    brl_per_kwh TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    source_event_id TEXT NOT NULL UNIQUE,
    user_id TEXT NOT NULL REFERENCES users(id),
    unit_id TEXT NOT NULL REFERENCES units(id),
    vehicle_id TEXT REFERENCES vehicles(id),
    charger_id TEXT NOT NULL REFERENCES chargers(id),
    started_at TEXT NOT NULL,
    ended_at TEXT,
    meter_start_kwh TEXT NOT NULL,
    meter_end_kwh TEXT,
    tariff_brl_per_kwh TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('ACTIVE', 'CLOSED'))
);
CREATE INDEX IF NOT EXISTS sessions_unit_end_idx ON sessions(unit_id, ended_at);
CREATE INDEX IF NOT EXISTS sessions_charger_status_idx ON sessions(charger_id, status);
CREATE TABLE IF NOT EXISTS hourly_measurements (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    charger_id TEXT NOT NULL REFERENCES chargers(id),
    interval_start TEXT NOT NULL,
    interval_end TEXT NOT NULL,
    energy_kwh TEXT NOT NULL,
    source TEXT NOT NULL CHECK (source IN ('synthetic')),
    UNIQUE(session_id, interval_start)
);
CREATE INDEX IF NOT EXISTS measurements_start_idx ON hourly_measurements(interval_start);
CREATE TABLE IF NOT EXISTS queue_requests (
    request_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    charger_id TEXT NOT NULL REFERENCES chargers(id),
    created_at TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('WAITING', 'CANCELLED', 'SERVED'))
);
CREATE INDEX IF NOT EXISTS queue_order_idx ON queue_requests(charger_id, status, created_at, request_id);
"""


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


@contextmanager
def transaction(db_path: Path | str | None = None):
    conn = connect(db_path)
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: Path | str | None = None) -> None:
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()
