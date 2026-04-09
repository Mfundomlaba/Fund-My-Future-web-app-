from flask import render_template, session, redirect, url_for, flash, request, send_file
from app import app
from database.db_setup import db
from models.student_model import Student
from models.scholarship_model import Scholarship
from models.application_model import Application
from models.documents_model import Document
from models.uploaded_documents_model import UploadedDocument
from models.application_review_model import ApplicationReview
from werkzeug.utils import secure_filename
from datetime import datetime
from services.email_service import send_offer_acceptance_email
from services.contract_pdf_service import build_contract_pdf
import os
import base64
import uuid


ALLOWED_PROFILE_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}
ALLOWED_DOCUMENT_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

PROFILE_ID_DOCUMENT_NAME = "ID Document"
PROFILE_ACADEMIC_RECORD_NAME = "Academic Record"

OFFER_CONTRACT_TEXT = """
Fund My Future Scholarship Acceptance Agreement

By accepting this scholarship offer, you confirm that:
1. The information you submitted in your application is true and correct.
2. You agree to comply with the scholarship rules and academic requirements.
3. You understand that false information may result in cancellation of the award.
4. You agree that Fund My Future and the scholarship provider may review your academic progress where applicable.
"""


def allowed_profile_image(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PROFILE_IMAGE_EXTENSIONS


def allowed_document_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS


def save_signature_image(signature_data, student_number, application_id):
    if not signature_data or not signature_data.startswith("data:image/png;base64,"):
        return None

    try:
        encoded_data = signature_data.split(",", 1)[1]
        image_data = base64.b64decode(encoded_data)

        upload_folder = os.path.join("static", "uploads", "signatures")
        os.makedirs(upload_folder, exist_ok=True)

        filename = f"{student_number}_{application_id}_{uuid.uuid4().hex}.png"
        file_path = os.path.join(upload_folder, filename)

        with open(file_path, "wb") as f:
            f.write(image_data)

        return filename
    except Exception:
        return None


def parse_currency_to_float(amount_value):
    if amount_value is None:
        return 0.0

    cleaned = str(amount_value).strip()

    if not cleaned:
        return 0.0

    cleaned = cleaned.replace("R", "")
    cleaned = cleaned.replace("r", "")
    cleaned = cleaned.replace(",", "")
    cleaned = cleaned.strip()

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


@app.route("/student/dashboard")
def student_dashboard():
    if session.get("user_type") != "student":
        flash("Please log in as student.")
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    student = Student.query.get(student_number)

    return render_template(
        "students/dashboard.html",
        student=student
    )


@app.route("/student/profile", methods=["GET", "POST"])
def student_profile():
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    student = Student.query.get(student_number)

    has_accepted_scholarship = Application.query.filter_by(
        student_number=student_number,
        status="accepted"
    ).first() is not None

    if not student:
        flash("Student profile not found.")
        return redirect(url_for("login"))

    if request.method == "POST":
        first_name = request.form["first_name"].strip()
        last_name = request.form["last_name"].strip()
        phone_number = request.form["phone_number"].strip()
        current_debt = request.form.get("current_debt", "0").strip()

        if not first_name or not last_name or not phone_number:
            flash("First name, last name, and phone number are required.")
            return redirect(url_for("student_profile"))

        debt_value = student.current_debt or 0.0

        if not has_accepted_scholarship:
            try:
                debt_value = float(current_debt) if current_debt else 0.0
                if debt_value < 0:
                    flash("Current debt cannot be negative.")
                    return redirect(url_for("student_profile"))
            except ValueError:
                flash("Current debt must be a valid number.")
                return redirect(url_for("student_profile"))

        student.first_name = first_name
        student.last_name = last_name
        student.phone_number = phone_number
        student.current_debt = debt_value

        profile_picture = request.files.get("profile_picture")
        if profile_picture and profile_picture.filename != "":
            if allowed_profile_image(profile_picture.filename):
                filename = secure_filename(profile_picture.filename)
                filename = f"{student.student_number}_profile_{filename}"

                upload_folder = os.path.join("static", "uploads", "profile_pictures")
                os.makedirs(upload_folder, exist_ok=True)

                upload_path = os.path.join(upload_folder, filename)
                profile_picture.save(upload_path)

                student.profile_picture = filename
            else:
                flash("Profile picture must be a PNG, JPG, or JPEG file.")
                return redirect(url_for("student_profile"))

        id_document = request.files.get("id_document")
        if id_document and id_document.filename != "":
            if allowed_document_file(id_document.filename):
                filename = secure_filename(id_document.filename)
                filename = f"{student.student_number}_id_{filename}"

                upload_folder = os.path.join("static", "uploads", "student_documents")
                os.makedirs(upload_folder, exist_ok=True)

                upload_path = os.path.join(upload_folder, filename)
                id_document.save(upload_path)

                student.id_document_path = filename
            else:
                flash("ID document must be a PDF, PNG, JPG, or JPEG file.")
                return redirect(url_for("student_profile"))

        academic_record = request.files.get("academic_record")
        if academic_record and academic_record.filename != "":
            if allowed_document_file(academic_record.filename):
                filename = secure_filename(academic_record.filename)
                filename = f"{student.student_number}_academic_{filename}"

                upload_folder = os.path.join("static", "uploads", "student_documents")
                os.makedirs(upload_folder, exist_ok=True)

                upload_path = os.path.join(upload_folder, filename)
                academic_record.save(upload_path)

                student.academic_record_path = filename
            else:
                flash("Academic record must be a PDF, PNG, JPG, or JPEG file.")
                return redirect(url_for("student_profile"))

        db.session.commit()
        flash("Profile updated successfully.")
        return redirect(url_for("student_profile"))

    return render_template(
        "students/profile.html",
        student=student,
        has_accepted_scholarship=has_accepted_scholarship
    )


@app.route("/student/scholarships")
def student_scholarships():
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    scholarships = Scholarship.query.filter_by(status="open").all()

    return render_template(
        "students/scholarships.html",
        scholarships=scholarships
    )


@app.route("/student/apply/<int:scholarship_id>", methods=["GET", "POST"])
def apply_for_scholarship(scholarship_id):
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    student = Student.query.get(student_number)
    scholarship = Scholarship.query.get_or_404(scholarship_id)

    if scholarship.max_applicants:
        current_count = Application.query.filter_by(
            scholarship_id=scholarship_id
    ).count()

    if current_count >= scholarship.max_applicants:
        flash("This scholarship has reached the maximum number of applicants.")
        return redirect(url_for("student_scholarships"))

    existing_application = Application.query.filter_by(
        student_number=student_number,
        scholarship_id=scholarship_id
    ).first()

    if existing_application:
        flash("You have already applied for this scholarship.")
        return redirect(url_for("student_applications"))

    documents = Document.query.filter_by(
        scholarship_id=scholarship_id
    ).all()

    profile_documents = []
    application_documents = []

    for document in documents:
        document_name = document.document_name.strip().lower()

        if document_name == PROFILE_ID_DOCUMENT_NAME.lower():
            profile_documents.append({
                "document": document,
                "is_uploaded": bool(student.id_document_path),
                "file_path": student.id_document_path
            })
        elif document_name == PROFILE_ACADEMIC_RECORD_NAME.lower():
            profile_documents.append({
                "document": document,
                "is_uploaded": bool(student.academic_record_path),
                "file_path": student.academic_record_path
            })
        else:
            application_documents.append(document)

    if request.method == "POST":
        for profile_doc in profile_documents:
            if not profile_doc["is_uploaded"]:
                flash(f'{profile_doc["document"].document_name} is required in your profile before applying.')
                return redirect(url_for("student_profile"))

        for document in application_documents:
            file = request.files.get(f"document_{document.id}")

            if not file or file.filename == "":
                flash(f'Please upload {document.document_name}.')
                return redirect(url_for("apply_for_scholarship", scholarship_id=scholarship_id))

            if not allowed_document_file(file.filename):
                flash(f'{document.document_name} must be a PDF, PNG, JPG, or JPEG file.')
                return redirect(url_for("apply_for_scholarship", scholarship_id=scholarship_id))

        application = Application(
            student_number=student_number,
            scholarship_id=scholarship_id,
            status="submitted"
        )

        db.session.add(application)
        db.session.commit()

        upload_folder = os.path.join("static", "uploads", "application_documents")
        os.makedirs(upload_folder, exist_ok=True)

        for document in application_documents:
            file = request.files.get(f"document_{document.id}")

            if file and file.filename != "":
                filename = secure_filename(file.filename)
                filename = f"{application.id}_{document.id}_{filename}"

                file_path = os.path.join(upload_folder, filename)
                file.save(file_path)

                uploaded_document = UploadedDocument(
                    application_id=application.id,
                    document_id=document.id,
                    file_path=filename
                )

                db.session.add(uploaded_document)

        db.session.commit()

        flash("Application submitted successfully.")
        return redirect(url_for("student_applications"))

    return render_template(
        "students/apply.html",
        scholarship=scholarship,
        student=student,
        profile_documents=profile_documents,
        application_documents=application_documents
    )


@app.route("/student/applications")
def student_applications():
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    applications = Application.query.filter_by(
        student_number=student_number
    ).order_by(Application.submitted_at.desc()).all()

    return render_template(
        "students/applications.html",
        applications=applications
    )


@app.route("/student/awards")
def student_awards():
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    awards = Application.query.filter_by(
        student_number=student_number,
        status="accepted"
    ).order_by(Application.accepted_at.desc()).all()

    return render_template(
        "students/awards.html",
        awards=awards
    )


@app.route("/student/application/<int:application_id>/track")
def track_application(application_id):
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    application = Application.query.filter_by(
        id=application_id,
        student_number=student_number
    ).first_or_404()

    review_history = ApplicationReview.query.filter_by(
        application_id=application_id
    ).order_by(ApplicationReview.reviewed_at.desc()).all()

    return render_template(
        "students/track_application.html",
        application=application,
        review_history=review_history
    )


@app.route("/student/application/<int:application_id>/accept-offer", methods=["GET", "POST"])
def accept_offer(application_id):
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    application = Application.query.filter_by(
        id=application_id,
        student_number=student_number
    ).first_or_404()

    if application.status != "approved":
        flash("This offer is not available for acceptance.")
        return redirect(url_for("track_application", application_id=application.id))

    if request.method == "POST":
        accepted_by_name = request.form.get("accepted_by_name", "").strip()
        acceptance_confirmed = request.form.get("acceptance_confirmed")
        signature_data = request.form.get("signature_data", "").strip()

        if not accepted_by_name:
            flash("Please type your full name to accept the offer.")
            return redirect(url_for("accept_offer", application_id=application.id))

        if not acceptance_confirmed:
            flash("You must agree to the scholarship terms before submitting.")
            return redirect(url_for("accept_offer", application_id=application.id))

        signature_filename = save_signature_image(
            signature_data=signature_data,
            student_number=student_number,
            application_id=application.id
        )

        if not signature_filename:
            flash("Please provide a valid drawn signature before submitting.")
            return redirect(url_for("accept_offer", application_id=application.id))

        if application.accepted_at is not None or application.status == "accepted":
            flash("This scholarship offer has already been accepted.")
            return redirect(url_for("track_application", application_id=application.id))

        scholarship_amount = parse_currency_to_float(application.scholarship.amount)

        student = Student.query.get(application.student_number)

        debt_before_award = student.current_debt or 0.0
        award_amount_applied = scholarship_amount if scholarship_amount > 0 else 0.0
        debt_after_award = debt_before_award

        if student and scholarship_amount > 0:
            debt_after_award = max(0.0, debt_before_award - scholarship_amount)
            student.current_debt = debt_after_award

        application.status = "accepted"
        application.accepted_at = datetime.utcnow()
        application.accepted_by_name = accepted_by_name
        application.acceptance_confirmed = True
        application.signature_file_path = signature_filename
        application.contract_text_snapshot = OFFER_CONTRACT_TEXT
        application.debt_before_award = debt_before_award
        application.award_amount_applied = award_amount_applied
        application.debt_after_award = debt_after_award

        review_entry = ApplicationReview(
            application_id=application.id,
            staff_id=1,
            status="accepted",
            comment="Scholarship offer accepted by student."
        )

        db.session.add(review_entry)
        db.session.commit()

        email_result = None

        if student:
            pdf_buffer = build_contract_pdf(
                application=application,
                student=student,
                contract_text=application.contract_text_snapshot or OFFER_CONTRACT_TEXT
            )

            pdf_bytes = pdf_buffer.getvalue()

            attachments = [
                {
                    "filename": f"contract_application_{application.id}.pdf",
                    "content": pdf_bytes,
                    "maintype": "application",
                    "subtype": "pdf"
                }
            ]

            email_result = send_offer_acceptance_email(
                student,
                application,
                attachments=attachments
            )

        if email_result and email_result["success"]:
            flash("Scholarship offer accepted successfully and confirmation email sent.")
        elif email_result and not email_result["success"]:
            flash(f'Scholarship offer accepted successfully, but confirmation email was not sent. {email_result["message"]}')
        else:
            flash("Scholarship offer accepted successfully.")

        return redirect(url_for("track_application", application_id=application.id))

    return render_template(
        "students/accept_offer.html",
        application=application,
        contract_text=OFFER_CONTRACT_TEXT
    )


@app.route("/student/application/<int:application_id>/download-contract")
def download_student_contract(application_id):
    if session.get("user_type") != "student":
        return redirect(url_for("login"))

    student_number = session.get("student_number")

    if not student_number:
        return redirect(url_for("login"))

    application = Application.query.filter_by(
        id=application_id,
        student_number=student_number
    ).first_or_404()

    if application.status != "accepted":
        flash("The signed contract is only available after the scholarship offer has been accepted.")
        return redirect(url_for("track_application", application_id=application.id))

    student = Student.query.get(application.student_number)

    pdf_buffer = build_contract_pdf(
        application=application,
        student=student,
        contract_text=application.contract_text_snapshot or OFFER_CONTRACT_TEXT
    )

    filename = f"contract_application_{application.id}.pdf"

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )