import base64
import smtplib
import requests
from email.message import EmailMessage
from flask import current_app


STATUS_MESSAGES = {
    "submitted": "Your application has been submitted successfully.",
    "under_review": "Your application is now under review.",
    "needs_revision": "Your application requires revision. Please check the latest comment in the system.",
    "shortlisted": "Good news. Your application has been shortlisted.",
    "approved": "Congratulations. Your application has been approved.",
    "rejected": "Your application was unfortunately not successful.",
    "accepted": "You have successfully accepted your scholarship offer."
}


def get_status_display(status):
    return status.replace("_", " ").title()


def build_application_status_email(student, application, comment=None):
    scholarship_title = application.scholarship.title
    provider = application.scholarship.provider
    status = application.status

    subject = f"Fund My Future - Application Update for {scholarship_title}"

    intro_message = STATUS_MESSAGES.get(
        status,
        "Your application status has been updated."
    )

    body_lines = [
        f"Dear {student.first_name} {student.last_name},",
        "",
        intro_message,
        "",
        f"Scholarship: {scholarship_title}",
        f"Provider: {provider}",
        f"Current Status: {get_status_display(status)}",
        ""
    ]

    if comment:
        body_lines.extend([
            "Staff Comment:",
            comment,
            ""
        ])

    body_lines.extend([
        "Please log in to Fund My Future to view the latest progress on your application.",
        "",
        "Regards,",
        "Fund My Future"
    ])

    return subject, "\n".join(body_lines)


def build_offer_acceptance_email(student, application):
    subject = f"Fund My Future - Scholarship Offer Accepted for {application.scholarship.title}"

    body_lines = [
        f"Dear {student.first_name} {student.last_name},",
        "",
        "You have successfully accepted your scholarship offer.",
        "",
        f"Scholarship: {application.scholarship.title}",
        f"Provider: {application.scholarship.provider}",
        f"Accepted By: {application.accepted_by_name}",
        f"Accepted Status: {get_status_display(application.status)}",
        ""
    ]

    if application.debt_before_award is not None:
        body_lines.extend([
            f"Debt Before Award: R{application.debt_before_award:.2f}",
            f"Award Amount Applied: R{(application.award_amount_applied or 0):.2f}",
            f"Debt After Award: R{(application.debt_after_award or 0):.2f}",
            ""
        ])

    body_lines.extend([
        "A signed copy of your contract is attached to this email.",
        "Please also log in to Fund My Future to view your application details and acceptance record.",
        "",
        "Regards,",
        "Fund My Future"
    ])

    return subject, "\n".join(body_lines)


def send_email_via_smtp(to_email, subject, body, attachments=None):
    app = current_app

    mail_server = app.config.get("MAIL_SERVER")
    mail_port = app.config.get("MAIL_PORT")
    mail_use_tls = app.config.get("MAIL_USE_TLS")
    mail_username = app.config.get("MAIL_USERNAME")
    mail_password = app.config.get("MAIL_PASSWORD")
    default_sender = app.config.get("MAIL_DEFAULT_SENDER")

    if not all([mail_server, mail_port, mail_username, mail_password, default_sender]):
        return {
            "success": False,
            "message": "SMTP email settings are not configured. Email was skipped."
        }

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = default_sender
    msg["To"] = to_email
    msg.set_content(body)

    if attachments:
        for attachment in attachments:
            msg.add_attachment(
                attachment["content"],
                maintype=attachment["maintype"],
                subtype=attachment["subtype"],
                filename=attachment["filename"]
            )

    try:
        with smtplib.SMTP(mail_server, mail_port) as server:
            if mail_use_tls:
                server.starttls()

            server.login(mail_username, mail_password)
            server.send_message(msg)

        return {
            "success": True,
            "message": "Email sent successfully via SMTP."
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"SMTP email could not be sent: {str(e)}"
        }


def send_email_via_brevo(to_email, to_name, subject, body, attachments=None):
    app = current_app

    api_key = app.config.get("BREVO_API_KEY")
    api_url = app.config.get("BREVO_API_URL")
    sender_email = app.config.get("MAIL_DEFAULT_SENDER")
    sender_name = app.config.get("BREVO_SENDER_NAME", "Fund My Future")

    if not all([api_key, api_url, sender_email]):
        return {
            "success": False,
            "message": "Brevo settings are not configured. Email was skipped."
        }

    payload = {
        "sender": {
            "name": sender_name,
            "email": sender_email
        },
        "to": [
            {
                "email": to_email,
                "name": to_name
            }
        ],
        "subject": subject,
        "textContent": body
    }

    if attachments:
        payload["attachment"] = []
        for attachment in attachments:
            encoded_content = base64.b64encode(attachment["content"]).decode("utf-8")
            payload["attachment"].append({
                "name": attachment["filename"],
                "content": encoded_content
            })

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        if 200 <= response.status_code < 300:
            return {
                "success": True,
                "message": "Email sent successfully via Brevo."
            }

        return {
            "success": False,
            "message": f"Brevo email failed: {response.status_code} - {response.text}"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Brevo email could not be sent: {str(e)}"
        }


def send_email(to_email, to_name, subject, body, attachments=None):
    provider = (current_app.config.get("MAIL_PROVIDER") or "").strip().lower()

    if provider == "brevo":
        return send_email_via_brevo(
            to_email=to_email,
            to_name=to_name,
            subject=subject,
            body=body,
            attachments=attachments
        )

    return send_email_via_smtp(
        to_email=to_email,
        subject=subject,
        body=body,
        attachments=attachments
    )


def send_application_status_email(student, application, comment=None):
    subject, body = build_application_status_email(student, application, comment)
    return send_email(
        to_email=student.email,
        to_name=f"{student.first_name} {student.last_name}",
        subject=subject,
        body=body
    )


def send_offer_acceptance_email(student, application, attachments=None):
    subject, body = build_offer_acceptance_email(student, application)
    return send_email(
        to_email=student.email,
        to_name=f"{student.first_name} {student.last_name}",
        subject=subject,
        body=body,
        attachments=attachments
    )