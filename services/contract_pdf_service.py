import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image,
    Table,
    TableStyle
)


def get_scaled_image(image_path, max_width_mm, max_height_mm, h_align="LEFT"):
    img = Image(image_path)

    max_width = max_width_mm * mm
    max_height = max_height_mm * mm

    original_width = img.imageWidth
    original_height = img.imageHeight

    width_scale = max_width / original_width
    height_scale = max_height / original_height
    scale = min(width_scale, height_scale)

    img.drawWidth = original_width * scale
    img.drawHeight = original_height * scale
    img.hAlign = h_align

    return img


def build_contract_pdf(application, student, contract_text):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ContractTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1d4ed8"),
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "ContractSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        spaceAfter=16
    )

    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=8,
        spaceBefore=12
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#1f2937")
    )

    small_style = ParagraphStyle(
        "SmallStyle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b")
    )

    story = []

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # =========================
    # BRANDING HEADER
    # =========================
    possible_logo_paths = [
        os.path.join(base_dir, "static", "images", "logo.png"),
        os.path.join(base_dir, "static", "images", "fundmyfuture_logo.png"),
        os.path.join(base_dir, "static", "img", "logo.png")
    ]

    logo_path = None
    for path in possible_logo_paths:
        if os.path.exists(path):
            logo_path = path
            break

    if logo_path:
        try:
            logo = get_scaled_image(
                image_path=logo_path,
                max_width_mm=80,   # increased size
                max_height_mm=30,  # increased height
                h_align="CENTER"   # center alignment
            )
            story.append(logo)
            story.append(Spacer(1, 14))
        except Exception:
            story.append(Paragraph("Fund My Future", title_style))

        story.append(Paragraph("Scholarship Offer Acceptance Contract", subtitle_style))
    else:
        story.append(Paragraph("Fund My Future", title_style))
        story.append(Paragraph("Scholarship Offer Acceptance Contract", subtitle_style))

    acceptance_date = (
        application.accepted_at.strftime("%Y-%m-%d %H:%M")
        if application.accepted_at else "N/A"
    )

    info_data = [
        ["Student Number", student.student_number],
        ["Student Name", f"{student.first_name} {student.last_name}"],
        ["Email", student.email],
        ["Institution", student.institution],
        ["Scholarship", application.scholarship.title],
        ["Provider", application.scholarship.provider],
        ["Accepted By", application.accepted_by_name or "N/A"],
        ["Accepted At", acceptance_date],
        ["Application Status", application.status.replace("_", " ").title()]
    ]

    info_table = Table(info_data, colWidths=[45 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eff6ff")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("LEADING", (0, 0), (-1, -1), 14),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 16))

    story.append(Paragraph("Terms and Conditions", section_heading_style))
    for line in contract_text.strip().split("\n"):
        if line.strip():
            story.append(Paragraph(line.strip(), body_style))
            story.append(Spacer(1, 4))

    story.append(Spacer(1, 12))
    story.append(Paragraph("Student Declaration", section_heading_style))
    story.append(Paragraph(
        f"I, <b>{application.accepted_by_name or 'N/A'}</b>, confirm that I have read and accepted the scholarship offer and its terms.",
        body_style
    ))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Signatures", section_heading_style))

    # =========================
    # STUDENT SIGNATURE
    # =========================
    student_signature_path = None
    if application.signature_file_path:
        candidate = os.path.join(
            base_dir,
            "static",
            "uploads",
            "signatures",
            application.signature_file_path
        )
        if os.path.exists(candidate):
            student_signature_path = candidate

    student_signature_elements = []

    if student_signature_path:
        try:
            student_signature_elements.append(
                get_scaled_image(
                    image_path=student_signature_path,
                    max_width_mm=60,
                    max_height_mm=25,
                    h_align="LEFT"
                )
            )
        except Exception:
            student_signature_elements.append(
                Paragraph("No signature available", body_style)
            )
    else:
        student_signature_elements.append(
            Paragraph("No signature available", body_style)
        )

    student_signature_elements.append(
        Paragraph(f"<b>{application.accepted_by_name or 'N/A'}</b>", body_style)
    )
    student_signature_elements.append(
        Paragraph("Student Signature", small_style)
    )

    # =========================
    # ADMIN SIGNATURE
    # =========================
    admin_signature_path = os.path.join(
        base_dir,
        "static",
        "images",
        "admin_signature.png"
    )

    admin_signature_elements = []

    if os.path.exists(admin_signature_path):
        try:
            admin_signature_elements.append(
                get_scaled_image(
                    image_path=admin_signature_path,
                    max_width_mm=60,
                    max_height_mm=25,
                    h_align="LEFT"
                )
            )
        except Exception:
            admin_signature_elements.append(
                Paragraph("Authorized Signature", body_style)
            )
    else:
        admin_signature_elements.append(
            Paragraph("Authorized Signature", body_style)
        )

    admin_signature_elements.append(
        Paragraph("<b>Grants Administrator</b>", body_style)
    )
    admin_signature_elements.append(
        Paragraph("Fund My Future", small_style)
    )

    signature_table = Table(
        [[student_signature_elements, admin_signature_elements]],
        colWidths=[85 * mm, 85 * mm]
    )

    signature_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(signature_table)

    story.append(Spacer(1, 18))
    story.append(Paragraph(
        "This document was generated electronically by Fund My Future.",
        small_style
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer