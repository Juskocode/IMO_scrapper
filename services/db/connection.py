import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "data.db"

def get_connection():
    return sqlite3.connect(DB_PATH)
