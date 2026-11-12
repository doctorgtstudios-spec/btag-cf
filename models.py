import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        path = Path(current_app.config["DATABASE_PATH"])
        path.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(path)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL COLLATE NOCASE UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title_id TEXT NOT NULL DEFAULT '',
            template_key TEXT NOT NULL DEFAULT 'all_update_backend',
            hosting_mode TEXT NOT NULL DEFAULT 'server',
            backend_name TEXT NOT NULL DEFAULT 'ALL UPDATE BACKEND',
            backend_code TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Upgrade existing preview databases without deleting users or projects.
    columns = {row["name"] for row in db.execute("PRAGMA table_info(projects)")}
    if "backend_name" not in columns:
        db.execute(
            "ALTER TABLE projects ADD COLUMN backend_name TEXT NOT NULL DEFAULT 'ALL UPDATE BACKEND'"
        )
    if "backend_code" not in columns:
        db.execute("ALTER TABLE projects ADD COLUMN backend_code TEXT NOT NULL DEFAULT ''")
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
