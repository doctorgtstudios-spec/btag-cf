import re
from functools import wraps

from flask import Flask, flash, g, redirect, render_template, request, session, url_for
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash, generate_password_hash

from config import Config
from models import get_db, init_app as init_db_app

USERNAME_RE = re.compile(r"^[a-zA-Z0-9_]{3,24}$")
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    csrf.init_app(app)
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
                        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                        (username, generate_password_hash(password)),
                    )
                    db.commit()
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                    return redirect(url_for("dashboard"))
                except Exception:
                    db.rollback()
                    flash("That username may already be taken.", "error")
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
        return render_template("dashboard.html")

    @app.get("/<username>")
    def public_backend_placeholder(username):
        # Reserved for reverse-proxy routing to an isolated backend worker.
        # Never import or execute a user's uploaded Python file in this process.
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
