import os
from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///caseflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Case(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(120), nullable=False)
    complaint = db.Column(db.Text, nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(100), nullable=False)
    severity = db.Column(db.String(30), nullable=False)
    medical_history = db.Column(db.Text)
    medications = db.Column(db.Text)
    allergies = db.Column(db.Text)
    fever = db.Column(db.String(10))
    breathing_difficulty = db.Column(db.String(10))
    additional_notes = db.Column(db.Text)
    status = db.Column(db.String(30), default="New", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Doctor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(60), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)


def doctor_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "doctor_id" not in session:
            return redirect(url_for("doctor_login"))
        return view(*args, **kwargs)
    return wrapped


with app.app_context():
    db.create_all()
    # Create demo account only when deployment credentials are configured.
demo_username = os.environ.get("DEMO_DOCTOR_USERNAME")
demo_password = os.environ.get("DEMO_DOCTOR_PASSWORD")

if demo_username and demo_password:
    if not Doctor.query.filter_by(username=demo_username).first():
        db.session.add(Doctor(
            username=demo_username,
            password_hash=generate_password_hash(demo_password)
        ))
        db.session.commit()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/intake", methods=["GET", "POST"])
def intake():
    if request.method == "POST":
        required = ["patient_name", "age", "email", "complaint",
                    "symptoms", "duration", "severity"]
        if any(not request.form.get(field, "").strip() for field in required):
            flash("Please complete all required fields.", "error")
            return redirect(url_for("intake"))

        try:
            age = int(request.form["age"])
            if age < 1 or age > 120:
                raise ValueError
        except ValueError:
            flash("Please enter a valid age.", "error")
            return redirect(url_for("intake"))

        case = Case(
            patient_name=request.form["patient_name"].strip(),
            age=age,
            email=request.form["email"].strip(),
            complaint=request.form["complaint"].strip(),
            symptoms=request.form["symptoms"].strip(),
            duration=request.form["duration"].strip(),
            severity=request.form["severity"].strip(),
            medical_history=request.form.get("medical_history", "").strip(),
            medications=request.form.get("medications", "").strip(),
            allergies=request.form.get("allergies", "").strip(),
            fever=request.form.get("fever", "No"),
            breathing_difficulty=request.form.get("breathing_difficulty", "No"),
            additional_notes=request.form.get("additional_notes", "").strip()
        )
        db.session.add(case)
        db.session.commit()
        return redirect(url_for("submitted", case_id=case.id))
    return render_template("intake.html")


@app.route("/submitted/<int:case_id>")
def submitted(case_id):
    case = db.get_or_404(Case, case_id)
    return render_template("submitted.html", case=case)


@app.route("/doctor/login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        doctor = Doctor.query.filter_by(username=request.form.get("username", "")).first()
        if doctor and check_password_hash(doctor.password_hash, request.form.get("password", "")):
            session.clear()
            session["doctor_id"] = doctor.id
            return redirect(url_for("dashboard"))
        flash("Invalid demo login details.", "error")
    return render_template("doctor_login.html")


@app.route("/doctor/logout")
def doctor_logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/doctor/dashboard")
@doctor_required
def dashboard():
    cases = Case.query.order_by(Case.created_at.desc()).all()
    return render_template("dashboard.html", cases=cases)


@app.route("/doctor/case/<int:case_id>", methods=["GET", "POST"])
@doctor_required
def case_detail(case_id):
    case = db.get_or_404(Case, case_id)
    if request.method == "POST":
        status = request.form.get("status", "New")
        if status in {"New", "Reviewed", "Follow-up"}:
            case.status = status
            db.session.commit()
            flash("Case status updated.", "success")
        return redirect(url_for("case_detail", case_id=case.id))
    return render_template("case_detail.html", case=case)


if __name__ == "__main__":
    app.run(debug=False)
