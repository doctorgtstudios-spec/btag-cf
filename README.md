# BTag CF

A Flask-based control panel for Gorilla Tag / PlayFab-compatible backend projects.

## Current status

The dashboard supports account registration/login, backend creation, user-defined backend names, and editing/saving each backend's Python source. New backends start with the name **ALL UPDATE BACKEND**; users can rename them.

**Saving code is not the same as hosting it.** Customer Python files are stored as text and are never executed by the control panel. Public API hosting and local-runner support are not enabled until a separate isolated runner and routing layer are deployed.

## URL structure

The reserved account URL is:

`https://btag-cf.com/<username>/`

The dashboard's backend names are labels and can be changed by the account owner. They do not change the URL.

## Development

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://127.0.0.1:5000.

Set a long, random `SECRET_KEY` before deployment. Do not commit real PlayFab keys, Oculus tokens, Discord webhooks, or user backend files.

## Hosting requirements

A production deployment needs persistent database storage, HTTPS, a reverse proxy, and a container/process manager. Each user's Python code must run in a separate isolated worker with resource limits, restricted filesystem/network access, non-root execution, and controlled dependencies. Never execute uploaded code inside the main Flask web process.

The control panel supports PostgreSQL through the `DATABASE_URL` environment variable and keeps SQLite for local development. On Render, create a PostgreSQL database and add its **Internal Database URL** as the web service's `DATABASE_URL` environment variable. The app creates its tables automatically on startup.

**Important:** The current `/tmp` SQLite database is temporary. Existing accounts stored there will not automatically move to PostgreSQL; users will need to register again after the database is connected. Back up/export any data you still need before changing databases.

Render's free web service filesystem is temporary, and Render's free Postgres databases expire after 30 days. For accounts that must persist indefinitely, use a database plan without that expiry (or another managed PostgreSQL provider with durable storage). Do not use the free Render Postgres database as permanent account storage.
