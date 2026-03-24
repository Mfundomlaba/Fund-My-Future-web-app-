from database.db_setup import db
from datetime import datetime


class Student(db.Model):
    __tablename__ = "students"

    student_number = db.Column(db.String(8), primary_key=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone_number = db.Column(db.String(15), nullable=False)
    institution = db.Column(db.String(120), nullable=False)

    current_debt = db.Column(db.Float, default=0.0)

    profile_picture = db.Column(db.String(255), nullable=True)
    id_document_path = db.Column(db.String(255), nullable=True)
    academic_record_path = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Student {self.student_number}>"