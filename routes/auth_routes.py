import os
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from flask import render_template, request, redirect, url_for, flash, session

from app import app
from database.db_setup import db
from models.student_model import Student
from models.staff_model import StaffAdmin


ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

INSTITUTION_DOMAINS = {
    "Durban University of Technology": "dut4life.ac.za",
    "University of KwaZulu-Natal": "stu.ukzn.ac.za",
    "University of Cape Town": "myuct.ac.za",
    "University of the Witwatersrand": "students.wits.ac.za",
    "University of Pretoria": "tuks.ac.za",
    "University of Johannesburg": "uj.ac.za",
    "Stellenbosch University": "sun.ac.za",
    "Nelson Mandela University": "mandela.ac.za",
    "Cape Peninsula University of Technology": "mycput.ac.za",
    "Tshwane University of Technology": "tut4life.ac.za"
}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def generate_student_email(student_number, institution_name):
    domain = INSTITUTION_DOMAINS.get(institution_name)
    if not domain:
        return None
    return f"{student_number.strip()}@{domain}".lower()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login_identifier = request.form["email"].strip().lower()
        password = request.form["password"]

        student = Student.query.filter_by(email=login_identifier).first()

        if not student:
            student = Student.query.filter_by(student_number=login_identifier).first()

        if student and check_password_hash(student.password_hash, password):
            session.clear()
            session["student_number"] = student.student_number
            session["user_type"] = "student"

            flash("Login successful.")
            return redirect(url_for("student_dashboard"))

        staff = StaffAdmin.query.filter_by(email=login_identifier).first()

        if staff and check_password_hash(staff.password_hash, password):
            session.clear()
            session["staff_id"] = staff.staff_id
            session["user_type"] = "staff"

            flash("Staff login successful.")
            return redirect(url_for("staff_dashboard"))

        flash("Invalid email, student number, or password.")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        student_number = request.form["student_number"].strip()
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        phone_number = request.form["phone_number"].strip()
        institution = request.form["institution"].strip()
        manual_email = request.form.get("manual_email", "").strip().lower()
        password = request.form["password"]
        current_debt = request.form.get("current_debt", "0").strip()

        if not institution:
            flash("Please select an institution.")
            return redirect(url_for("register"))

        if institution == "Other":
            if not manual_email:
                flash("Please enter your email address.")
                return redirect(url_for("register"))
            final_email = manual_email
        else:
            if institution not in INSTITUTION_DOMAINS:
                flash("Please select a valid institution.")
                return redirect(url_for("register"))

            final_email = generate_student_email(student_number, institution)

            if not final_email:
                flash("Could not generate student email.")
                return redirect(url_for("register"))

        existing_student_number = Student.query.filter_by(student_number=student_number).first()
        if existing_student_number:
            flash("A student with that student number already exists.")
            return redirect(url_for("register"))

        existing_email = Student.query.filter_by(email=final_email).first()
        if existing_email:
            flash("A student with that email already exists.")
            return redirect(url_for("register"))

        file = request.files.get("profile_picture")
        filename = None

        if file and file.filename != "":
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{student_number}_{filename}"

                upload_folder = os.path.join("static", "uploads", "profile_pictures")
                os.makedirs(upload_folder, exist_ok=True)

                upload_path = os.path.join(upload_folder, filename)
                file.save(upload_path)
            else:
                flash("Only PNG, JPG, and JPEG image files are allowed.")
                return redirect(url_for("register"))

        try:
            debt_value = float(current_debt) if current_debt else 0.0
        except ValueError:
            flash("Current debt must be a valid number.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        student = Student(
            student_number=student_number,
            first_name=first_name,
            last_name=last_name,
            email=final_email,
            phone_number=phone_number,
            institution=institution,
            current_debt=debt_value,
            password_hash=password_hash,
            profile_picture=filename
        )

        db.session.add(student)
        db.session.commit()

        session.clear()
        session["student_number"] = student.student_number
        session["user_type"] = "student"

        flash(f"Registration successful. You are now logged in. Your login email is: {final_email}")
        return redirect(url_for("student_dashboard"))

    return render_template(
        "register.html",
        institutions=INSTITUTION_DOMAINS
    )


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.")
    return redirect(url_for("home"))