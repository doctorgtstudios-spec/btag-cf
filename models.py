import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from flask import current_app, g


class PostgresDB:
    """Small adapter so existing parameterized queries work on SQLite and Postgres."""
    def __init__(self, connection):
        self.connection = connection

    def execute(self, sql, params=()):
        return self.connection.execute(sql.replace("?", "%s"), params)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def get_db():
    if "db" not in g:
        database_url = current_app.config.get("DATABASE_URL")
        if database_url:
            connection = psycopg.connect(database_url, row_factory=dict_row)
            g.db = PostgresDB(connection)
        else:
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
    if isinstance(db, PostgresDB):
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title_id TEXT NOT NULL DEFAULT '',
                template_key TEXT NOT NULL DEFAULT 'all_update_backend',
                hosting_mode TEXT NOT NULL DEFAULT 'server',
                backend_name TEXT NOT NULL DEFAULT 'ALL UPDATE BACKEND',
                backend_code TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS backend_name TEXT NOT NULL DEFAULT 'ALL UPDATE BACKEND'")
        db.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS backend_code TEXT NOT NULL DEFAULT ''")
    else:
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
        columns = {row["name"] for row in db.execute("PRAGMA table_info(projects)")}
        if "backend_name" not in columns:
            db.execute("ALTER TABLE projects ADD COLUMN backend_name TEXT NOT NULL DEFAULT 'ALL UPDATE BACKEND'")
        if "backend_code" not in columns:
            db.execute("ALTER TABLE projects ADD COLUMN backend_code TEXT NOT NULL DEFAULT ''")
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        init_db()
