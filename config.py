import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-change-me")
    # Set DATABASE_URL to a persistent PostgreSQL database in production.
    # SQLite remains available for local development.
    DATABASE_URL = os.environ.get("DATABASE_URL", "").strip() or None
    DATABASE_PATH = os.environ.get(
        "DATABASE_PATH", str(BASE_DIR / "instance" / "btag-cf.sqlite3")
    )
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Enable only behind HTTPS in production.
    SESSION_COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "0") == "1"
