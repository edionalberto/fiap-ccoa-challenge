from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DEMO_PATH = DATA_DIR / "demo.json"
DB_PATH = Path(os.environ.get("CONDOCARGA_DB_PATH", DATA_DIR / "condocarga.sqlite3"))
TIMEZONE = "America/Sao_Paulo"
DEFAULT_TARIFF = "1.00"
