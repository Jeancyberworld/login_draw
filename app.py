import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
)
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

# -----------------------------
# BASIC FLASK SETUP
# -----------------------------
app = Flask(__name__)

# Secret key for sessions
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-me")

# -----------------------------
# DATABASE CONFIG
# -----------------------------
db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")

if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -----------------------------
# MODELS
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    drawing = db.relationship("Drawing", backref="user", uselist=False)


class Drawing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    image_data = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

# -----------------------------
# HELPERS
# -----------------------------
def require_login():
    return "user_id" in session

def get_current_user():
    if "user_id" not in session:
        return None
    return User.query.get(session["user_id"])

# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def home():
    if require_login():
        return redirect(url_for("draw"))
    return redirect(url_for("login"))

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not password:
            flash("Username and password required.", "error")
            return render_template("signup.html")

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("signup.html")

        user = User(
            username=username,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        session["user_id"] = user.id
        flash("Account created!", "success")
        return redirect(url_for("draw"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            flash("Logged in!", "success")
            return redirect(url_for("draw"))
        else:
            flash("Invalid username or password.", "error")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("Logged out!", "info")
    return redirect(url_for("login"))


@app.route("/draw")
def draw():
    if not require_login():
        flash("Login required.", "error")
        return redirect(url_for("login"))

    user = get_current_user()
    return render_template("draw.html", username=user.username)


@app.route("/save_drawing", methods=["POST"])
def save_drawing():
    if not require_login():
        return jsonify({"error": "Not logged in"}), 401

    user = get_current_user()
    data = request.get_json()
    image_data = data.get("imageData")

    if not image_data:
        return jsonify({"error": "No image data"}), 400

    drawing = Drawing.query.filter_by(user_id=user.id).first()
    if drawing is None:
        drawing = Drawing(user_id=user.id, image_data=image_data)
        db.session.add(drawing)
    else:
        drawing.image_data = image_data

    db.session.commit()
    return jsonify({"status": "ok"})


@app.route("/get_drawing")
def get_drawing():
    if not require_login():
        return jsonify({"imageData": None})

    user = get_current_user()
    drawing = Drawing.query.filter_by(user_id=user.id).first()

    if drawing and drawing.image_data:
        return jsonify({"imageData": drawing.image_data})
    return jsonify({"imageData": None})

# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)