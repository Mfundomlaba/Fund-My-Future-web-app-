from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, session, send_file
from app import app
from database.db_setup import db
from models.scholarship_model import Scholarship
from models.documents_model import Document
from models.application_model import Application
from models.uploaded_documents_model import UploadedDocument
from models.application_review_model import ApplicationReview
from models.student_model import Student
from services.email_service import send_application_status_email
from services.contract_pdf_service import build_contract_pdf


VALID_APPLICATION_STATUSES = [
    "submitted",
    "under_review",
    "needs_revision",
    "shortlisted",
    "approved",
    "rejected"
]

VALID_SCHOLARSHIP_STATUSES = [
    "open",
    "closed"
]


@app.route("/staff/dashboard")
def staff_dashboard():
    if session.get("user_type") != "staff":
        flash("Please log in as staff.")
        return redirect(url_for("login"))

    return render_template("admin/dashboard.html")


@app.route("/staff/create-scholarship", methods=["GET", "POST"])
def create_scholarship():
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"].strip()
        provider = request.form["provider"].strip()
        amount = request.form["amount"].strip()
        deadline_str = request.form["deadline"]
        description = request.form["description"].strip()
        max_applicants = request.form.get("max_applicants", "").strip()
        status = request.form.get("status", "open").strip()

        required_profile_documents = request.form.getlist("required_profile_documents")
        custom_documents = request.form.get("custom_documents", "").strip()

        if status not in VALID_SCHOLARSHIP_STATUSES:
            flash("Invalid scholarship status.")
            return redirect(url_for("create_scholarship"))

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        if deadline < datetime.today().date():
            flash("Deadline cannot be in the past.")
            return redirect(url_for("create_scholarship"))

        max_applicants_value = None
        if max_applicants:
            try:
                max_applicants_value = int(max_applicants)
                if max_applicants_value < 1:
                    flash("Max applicants must be at least 1.")
                    return redirect(url_for("create_scholarship"))
            except ValueError:
                flash("Max applicants must be a valid whole number.")
                return redirect(url_for("create_scholarship"))

        scholarship = Scholarship(
            title=title,
            provider=provider,
            amount=amount,
            max_applicants=max_applicants_value,
            deadline=deadline,
            description=description,
            status=status
        )

        db.session.add(scholarship)
        db.session.commit()

        all_documents = []

        for doc_name in required_profile_documents:
            clean_name = doc_name.strip()
            if clean_name:
                all_documents.append(clean_name)

        if custom_documents:
            custom_list = [doc.strip() for doc in custom_documents.split(",") if doc.strip()]
            all_documents.extend(custom_list)

        unique_documents = []
        seen = set()

        for doc_name in all_documents:
            key = doc_name.lower()
            if key not in seen:
                seen.add(key)
                unique_documents.append(doc_name)

        for doc_name in unique_documents:
            document = Document(
                scholarship_id=scholarship.id,
                document_name=doc_name
            )
            db.session.add(document)

        db.session.commit()

        flash("Scholarship created successfully.")
        return redirect(url_for("manage_scholarships"))

    return render_template(
        "admin/create_scholarship.html",
        date_today=datetime.today().strftime("%Y-%m-%d")
    )

@app.route("/staff/manage-scholarships")
def manage_scholarships():
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarships = Scholarship.query.order_by(Scholarship.created_at.desc()).all()

    scholarship_stats = []
    for scholarship in scholarships:
        total_applications = Application.query.filter_by(
            scholarship_id=scholarship.id
        ).count()

        scholarship_stats.append({
            "scholarship": scholarship,
            "total_applications": total_applications
        })

    return render_template(
        "admin/manage_scholarships.html",
        scholarship_stats=scholarship_stats
    )


@app.route("/staff/scholarship/<int:scholarship_id>/edit", methods=["GET", "POST"])
def edit_scholarship(scholarship_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarship = Scholarship.query.get_or_404(scholarship_id)

    if request.method == "POST":
        title = request.form["title"].strip()
        provider = request.form["provider"].strip()
        amount = request.form["amount"].strip()
        deadline_str = request.form["deadline"]
        description = request.form["description"].strip()
        max_applicants = request.form.get("max_applicants", "").strip()
        status = request.form.get("status", "open").strip()

        if status not in VALID_SCHOLARSHIP_STATUSES:
            flash("Invalid scholarship status.")
            return redirect(url_for("edit_scholarship", scholarship_id=scholarship.id))

        deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()

        max_applicants_value = None
        if max_applicants:
            try:
                max_applicants_value = int(max_applicants)
                if max_applicants_value < 1:
                    flash("Max applicants must be at least 1.")
                    return redirect(url_for("edit_scholarship", scholarship_id=scholarship.id))
            except ValueError:
                flash("Max applicants must be a valid whole number.")
                return redirect(url_for("edit_scholarship", scholarship_id=scholarship.id))

        scholarship.title = title
        scholarship.provider = provider
        scholarship.amount = amount
        scholarship.max_applicants = max_applicants_value
        scholarship.deadline = deadline
        scholarship.description = description
        scholarship.status = status

        db.session.commit()

        flash("Scholarship updated successfully.")
        return redirect(url_for("manage_scholarships"))

    return render_template(
        "admin/edit_scholarship.html",
        scholarship=scholarship,
        valid_statuses=VALID_SCHOLARSHIP_STATUSES
    )


@app.route("/staff/scholarship/<int:scholarship_id>/delete", methods=["POST"])
def delete_scholarship(scholarship_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarship = Scholarship.query.get_or_404(scholarship_id)

    application_count = Application.query.filter_by(scholarship_id=scholarship.id).count()
    if application_count > 0:
        flash("This scholarship cannot be deleted because applications have already been submitted.")
        return redirect(url_for("manage_scholarships"))

    documents = Document.query.filter_by(scholarship_id=scholarship.id).all()
    for document in documents:
        db.session.delete(document)

    db.session.delete(scholarship)
    db.session.commit()

    flash("Scholarship deleted successfully.")
    return redirect(url_for("manage_scholarships"))


@app.route("/staff/scholarship/<int:scholarship_id>/documents", methods=["GET", "POST"])
def add_required_documents(scholarship_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarship = Scholarship.query.get_or_404(scholarship_id)

    if request.method == "POST":
        document_name = request.form["document_name"].strip()

        if not document_name:
            flash("Document name is required.")
            return redirect(url_for("add_required_documents", scholarship_id=scholarship_id))

        existing_document = Document.query.filter_by(
            scholarship_id=scholarship_id,
            document_name=document_name
        ).first()

        if existing_document:
            flash("This required document already exists.")
            return redirect(url_for("add_required_documents", scholarship_id=scholarship_id))

        document = Document(
            scholarship_id=scholarship_id,
            document_name=document_name
        )

        db.session.add(document)
        db.session.commit()

        flash("Required document added successfully.")
        return redirect(url_for("add_required_documents", scholarship_id=scholarship_id))

    documents = Document.query.filter_by(scholarship_id=scholarship_id).all()

    return render_template(
        "admin/add_documents.html",
        scholarship=scholarship,
        documents=documents
    )

@app.route("/staff/document/<int:document_id>/delete", methods=["POST"])
def delete_required_document(document_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    document = Document.query.get_or_404(document_id)
    scholarship_id = document.scholarship_id

    db.session.delete(document)
    db.session.commit()

    flash("Required document deleted successfully.")
    return redirect(url_for("add_required_documents", scholarship_id=scholarship_id))

@app.route("/staff/applications")
def staff_applications():
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarships = Scholarship.query.order_by(Scholarship.created_at.desc()).all()

    scholarship_application_summary = []
    for scholarship in scholarships:
        total_applications = Application.query.filter_by(scholarship_id=scholarship.id).count()
        approved_count = Application.query.filter_by(scholarship_id=scholarship.id, status="approved").count()
        accepted_count = Application.query.filter_by(scholarship_id=scholarship.id, status="accepted").count()

        scholarship_application_summary.append({
            "scholarship": scholarship,
            "total_applications": total_applications,
            "approved_count": approved_count,
            "accepted_count": accepted_count
        })

    return render_template(
        "admin/review_applications_by_scholarship.html",
        scholarship_application_summary=scholarship_application_summary
    )


@app.route("/staff/scholarship/<int:scholarship_id>/applications")
def scholarship_applications(scholarship_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    scholarship = Scholarship.query.get_or_404(scholarship_id)

    applications = Application.query.filter_by(
        scholarship_id=scholarship_id
    ).order_by(Application.submitted_at.desc()).all()

    return render_template(
        "admin/scholarship_applications.html",
        scholarship=scholarship,
        applications=applications
    )


@app.route("/staff/application/<int:application_id>", methods=["GET", "POST"])
def view_application(application_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    application = Application.query.get_or_404(application_id)

    if request.method == "POST":
        new_status = request.form["status"].strip()
        comment = request.form.get("comment", "").strip()
        staff_id = session.get("staff_id")

        if new_status not in VALID_APPLICATION_STATUSES:
            flash("Invalid application status selected.")
            return redirect(url_for("view_application", application_id=application_id))

        application.status = new_status

        review_entry = ApplicationReview(
            application_id=application.id,
            staff_id=staff_id,
            status=new_status,
            comment=comment if comment else None
        )

        db.session.add(review_entry)
        db.session.commit()

        student = Student.query.get(application.student_number)
        email_result = None

        if student:
            email_result = send_application_status_email(
                student=student,
                application=application,
                comment=comment if comment else None
            )

        if email_result and email_result["success"]:
            flash("Application status updated and email notification sent successfully.")
        elif email_result and not email_result["success"]:
            flash(f'Application status updated, but email notification was not sent. {email_result["message"]}')
        else:
            flash("Application status updated successfully.")

        return redirect(url_for("view_application", application_id=application_id))

    documents = UploadedDocument.query.filter_by(
        application_id=application_id
    ).all()

    student = Student.query.get(application.student_number)

    profile_documents = {
        "id_document": student.id_document_path if student else None,
        "academic_record": student.academic_record_path if student else None
    }

    review_history = ApplicationReview.query.filter_by(
        application_id=application_id
    ).order_by(ApplicationReview.reviewed_at.desc()).all()

    return render_template(
        "admin/view_application.html",
        application=application,
        documents=documents,
        profile_documents=profile_documents,
        review_history=review_history,
        valid_statuses=VALID_APPLICATION_STATUSES
    )


@app.route("/staff/application/<int:application_id>/download-contract")
def download_staff_contract(application_id):
    if session.get("user_type") != "staff":
        return redirect(url_for("login"))

    application = Application.query.get_or_404(application_id)

    if application.status != "accepted":
        flash("The signed contract is only available after the student has accepted the offer.")
        return redirect(url_for("view_application", application_id=application.id))

    student = Student.query.get(application.student_number)

    contract_text = application.contract_text_snapshot or """
Fund My Future Scholarship Acceptance Agreement

By accepting this scholarship offer, you confirm that:
1. The information you submitted in your application is true and correct.
2. You agree to comply with the scholarship rules and academic requirements.
3. You understand that false information may result in cancellation of the award.
4. You agree that Fund My Future and the scholarship provider may review your academic progress where applicable.
"""

    pdf_buffer = build_contract_pdf(
        application=application,
        student=student,
        contract_text=contract_text
    )

    filename = f"staff_contract_application_{application.id}.pdf"

    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=filename,
        mimetype="application/pdf"
    )