from database.db_setup import db
from datetime import datetime


class StaffAdmin(db.Model):
    __tablename__ = "staff_admin"

    staff_id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    phone_number = db.Column(db.String(15), nullable=False)

    role = db.Column(db.String(20), nullable=False)  
    # role can be: "admin" or "staff"

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<StaffAdmin {self.staff_id} - {self.role}>"