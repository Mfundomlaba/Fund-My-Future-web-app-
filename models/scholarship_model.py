from database.db_setup import db
from datetime import datetime


class Scholarship(db.Model):
    __tablename__ = "scholarships"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    title = db.Column(db.String(150), nullable=False)
    provider = db.Column(db.String(150), nullable=False)

    amount = db.Column(db.String(50), nullable=True)
    max_applicants = db.Column(db.Integer, nullable=True)

    deadline = db.Column(db.Date, nullable=False)

    description = db.Column(db.Text, nullable=True)

    status = db.Column(db.String(20), default="open")

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Scholarship {self.title}>"