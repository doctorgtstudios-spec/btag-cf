"""Production WSGI entry point for Gunicorn."""
import os

from app import create_app

if os.environ.get("FLASK_DEBUG") == "1":
    raise RuntimeError("FLASK_DEBUG must not be enabled in production.")

if not os.environ.get("SECRET_KEY") or os.environ.get("SECRET_KEY") == "dev-only-change-me":
    raise RuntimeError("Set a unique SECRET_KEY environment variable before starting BTag CF.")

app = create_app()
app.config["SESSION_COOKIE_SECURE"] = True
