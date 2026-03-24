from app import app
from database.db_setup import db
from models.staff_model import StaffAdmin
from werkzeug.security import generate_password_hash

with app.app_context():
    existing_staff = StaffAdmin.query.filter_by(email="admin@fundmyfuture.com").first()

    if not existing_staff:
        staff = StaffAdmin(
            first_name="System",
            last_name="Admin",
            email="admin@fundmyfuture.com",
            password_hash=generate_password_hash("Admin123"),
            phone_number="0123456789",
            role="admin"
        )

        db.session.add(staff)
        db.session.commit()

        print("Admin account created successfully.")
        print("Email: admin@fundmyfuture.com")
        print("Password: Admin123")
    else:
        print("Admin account already exists.")