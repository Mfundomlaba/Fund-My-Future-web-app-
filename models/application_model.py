from database.db_setup import db
from datetime import datetime


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    student_number = db.Column(
        db.String(8),
        db.ForeignKey("students.student_number"),
        nullable=False
    )

    scholarship_id = db.Column(
        db.Integer,
        db.ForeignKey("scholarships.id"),
        nullable=False
    )

    scholarship = db.relationship("Scholarship")

    status = db.Column(
        db.String(20),
        default="submitted"
    )

    submitted_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    last_updated = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    accepted_at = db.Column(
        db.DateTime,
        nullable=True
    )

    accepted_by_name = db.Column(
        db.String(120),
        nullable=True
    )

    acceptance_confirmed = db.Column(
        db.Boolean,
        default=False
    )

    signature_file_path = db.Column(
        db.String(255),
        nullable=True
    )

    contract_text_snapshot = db.Column(
        db.Text,
        nullable=True
    )

    debt_before_award = db.Column(
        db.Float,
        nullable=True
    )

    award_amount_applied = db.Column(
        db.Float,
        nullable=True
    )

    debt_after_award = db.Column(
        db.Float,
        nullable=True
    )

    __table_args__ = (
        db.UniqueConstraint(
            "student_number",
            "scholarship_id",
            name="unique_student_application"
        ),
    )

    def __repr__(self):
        return f"<Application {self.id}>"