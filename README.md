# BTag CF

A Flask-based control panel for Gorilla Tag / PlayFab-compatible backend projects.

## Status

This repository starts with the web application foundation. Backend hosting is intentionally **not enabled yet**: uploaded Python files are executable code and must never run inside the main Flask web process. Server hosting requires an isolated worker/container runner and deployment infrastructure; local hosting will use a separate runner on the user's computer.

## Planned features

- Username registration and login
- Per-user routes such as `/<username>/api/PlayFabAuthentication`, `CachePlayfabId`, and `TitleData`
- Backend template selection and user configuration
- Free local hosting and free server hosting, subject to fair-use resource limits
- Python Flask backends only; no JavaScript backend runtime

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Open http://127.0.0.1:5000.

Set a long, random `SECRET_KEY` in `.env` before deploying. Do not commit real secrets, PlayFab secret keys, Oculus tokens, or user backend files.

## Deployment notes

GitHub Pages cannot run Flask. Production requires a Python-capable server, a reverse proxy for user backend paths, persistent storage, and an isolated process/container manager. Do not expose the development server to the public internet.
