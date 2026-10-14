from pathlib import Path

from .database import connect, initialize_database
from .settings import DEMO_PATH
from .services import load_demo_data


def ensure_demo_loaded() -> None:
    initialize_database()
    conn = connect()
    try:
        seeded = conn.execute("SELECT EXISTS(SELECT 1 FROM sessions)").fetchone()[0]
    finally:
        conn.close()
    if not seeded and Path(DEMO_PATH).exists():
        load_demo_data(DEMO_PATH)


def measurement_count() -> int:
    conn = connect()
    try:
        return int(conn.execute("SELECT COUNT(*) FROM hourly_measurements").fetchone()[0])
    finally:
        conn.close()


