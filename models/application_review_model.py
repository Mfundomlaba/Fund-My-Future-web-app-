from database.db_setup import db
from datetime import datetime


class ApplicationReview(db.Model):
    __tablename__ = "application_reviews"

    id = db.Column(db.Integer, primary_key=True)

    application_id = db.Column(
        db.Integer,
        db.ForeignKey("applications.id"),
        nullable=False
    )

    staff_id = db.Column(
        db.Integer,
        db.ForeignKey("staff_admin.staff_id"),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False
    )

    comment = db.Column(
        db.Text,
        nullable=True
    )

    reviewed_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f"<ApplicationReview {self.id}>"