from flask import Flask, render_template, redirect, url_for, request, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# ==========================================================
# SECRET KEY (from Render)
# ==========================================================
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_key")

# ==========================================================
# DATABASE — Render allows writing ONLY in /tmp/
# ==========================================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================================
# USER MODEL
# ==========================================================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# ==========================================================
# CREATE DB ON STARTUP
# ==========================================================
with app.app_context():
    db.create_all()

# ==========================================================
# ROUTES
# ==========================================================

@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("draw"))
    return redirect(url_for("login"))

# ----------------------------------------------------------
# SIGNUP
# ----------------------------------------------------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # Check if user already exists
        user = User.query.filter_by(username=username).first()
        if user:
            return "Username already exists."

        # FIXED HASH METHOD — REQUIRED BY WERKZEUG
        hashed = generate_password_hash(password, method="pbkdf2:sha256")

        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for("login"))

    return render_template("signup.html")

# ----------------------------------------------------------
# LOGIN
# ----------------------------------------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session["username"] = username
            return redirect(url_for("draw"))
        else:
            return "Invalid login."

    return render_template("login.html")

# ----------------------------------------------------------
# DRAW PAGE
# ----------------------------------------------------------
@app.route("/draw", methods=["GET", "POST"])
def draw():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        drawing = request.form.get("drawing")
        return f"Saved drawing: {drawing}"

    return render_template("draw.html")

# ----------------------------------------------------------
# LOGOUT
# ----------------------------------------------------------
@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))

# ==========================================================
# RUN (local use only — Render ignores this)
# ==========================================================
if __name__ == "__main__":
    app.run(debug=True)