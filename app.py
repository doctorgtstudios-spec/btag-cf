import re
import sqlite3
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect, generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import get_db, init_app as init_db_app

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,24}$")
BACKEND_NAME_MAX = 48
BACKEND_CODE_MAX = 100 * 1024
STARTER_BACKEND = "from flask import Flask, jsonify\n\napp = Flask(__name__)\n\n@app.get(\"/api/health\")\ndef health():\n    return jsonify({\"status\": \"ok\", \"backend\": \"ALL UPDATE BACKEND\"})\n\n# Add your Gorilla Tag / PlayFab routes below.\n# Keep private keys and tokens in environment variables.\n"
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)
    app.context_processor(lambda: {"csrf_token": generate_csrf})
    init_db_app(app)

    @app.before_request
    def load_user():
        user_id = session.get("user_id")
        g.user = None
        if user_id:
            g.user = get_db().execute(
                "SELECT id, username FROM users WHERE id = ?", (user_id,)
            ).fetchone()

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                flash("Please log in first.", "warning")
                return redirect(url_for("login"))
            return view(*args, **kwargs)
        return wrapped

    def owned_project(project_id):
        return get_db().execute(
            "SELECT id, backend_name, backend_code, hosting_mode, created_at "
            "FROM projects WHERE id = ? AND user_id = ?",
            (project_id, g.user["id"]),
        ).fetchone()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not USERNAME_RE.fullmatch(username):
                flash("Username must be 3–24 characters: letters, numbers, or underscores.", "error")
            elif len(password) < 10:
                flash("Use a password with at least 10 characters.", "error")
            else:
                db = get_db()
                try:
                    cursor = db.execute(
                        "INSERT INTO users (username, password_hash) VALUES (?, ?) RETURNING id",
                        (username, generate_password_hash(password)),
                    )
                    db.commit()
                    session.clear()
                    session["user_id"] = cursor.fetchone()["id"]
                    return redirect(url_for("dashboard"))
                except (sqlite3.IntegrityError, psycopg.errors.UniqueViolation):
                    db.rollback()
                    flash("That username is already taken.", "error")
        return render_template("auth.html", mode="register")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_db().execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if user and check_password_hash(user["password_hash"], password):
                session.clear()
                session["user_id"] = user["id"]
                return redirect(url_for("dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("auth.html", mode="login")

    @app.post("/logout")
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("index"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        projects = get_db().execute(
            "SELECT id, backend_name, backend_code, hosting_mode, created_at "
            "FROM projects WHERE user_id = ? ORDER BY id DESC",
            (g.user["id"],),
        ).fetchall()
        return render_template("dashboard.html", projects=projects)

    @app.post("/dashboard/projects")
    @login_required
    def create_project():
        backend_name = request.form.get("backend_name", "ALL UPDATE BACKEND").strip()
        if not backend_name or len(backend_name) > BACKEND_NAME_MAX:
            flash("Give your backend a name (1–48 characters).", "error")
            return redirect(url_for("dashboard"))
        db = get_db()
        db.execute(
            "INSERT INTO projects (user_id, backend_name, backend_code, template_key, hosting_mode) "
            "VALUES (?, ?, ?, 'all_update_backend', 'server')",
            (g.user["id"], backend_name, STARTER_BACKEND),
        )
        db.commit()
        flash("Backend created. You can rename it and edit its Python file below.", "success")
        return redirect(url_for("dashboard"))

    @app.post("/dashboard/projects/<int:project_id>/save")
    @login_required
    def save_project(project_id):
        project = owned_project(project_id)
        if project is None:
            return "Not found", 404
        backend_name = request.form.get("backend_name", "").strip()
        backend_code = request.form.get("backend_code", "")
        if not backend_name or len(backend_name) > BACKEND_NAME_MAX:
            flash("Backend name must be 1–48 characters.", "error")
        elif len(backend_code.encode("utf-8")) > BACKEND_CODE_MAX:
            flash("The Python file is too large (maximum 100 KB).", "error")
        else:
            db = get_db()
            db.execute(
                "UPDATE projects SET backend_name = ?, backend_code = ? "
                "WHERE id = ? AND user_id = ?",
                (backend_name, backend_code, project_id, g.user["id"]),
            )
            db.commit()
            flash("Backend name and Python file saved.", "success")
        return redirect(url_for("dashboard"))

    @app.get("/<username>")
    def public_backend_placeholder(username):
        if not USERNAME_RE.fullmatch(username):
            return "Not found", 404
        return render_template("backend_placeholder.html", username=username), 501

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
