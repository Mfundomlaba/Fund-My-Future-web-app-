from flask import Flask
from config import Config
from database.db_setup import db
import os

app = Flask(__name__)
app.config.from_object(Config)

# connect database to app
db.init_app(app)

# import routes
from routes import *

# import models
from models.student_model import Student
from models.staff_model import StaffAdmin
from models.scholarship_model import Scholarship
from models.documents_model import Document
from models.application_model import Application
from models.uploaded_documents_model import UploadedDocument
from models.application_review_model import ApplicationReview
from werkzeug.security import generate_password_hash
from models.staff_model import StaffAdmin
from database.db_setup import db

with app.app_context():
    db.create_all()
    create_default_admin()

def create_default_admin():
    admin_email = os.environ.get("ADMIN_EMAIL", "admin@fundmyfuture.com")
    admin_password = os.environ.get("ADMIN_PASSWORD", "Admin123!")

    existing_admin = StaffAdmin.query.filter_by(email=admin_email).first()

    if not existing_admin:
        admin = StaffAdmin(
            first_name="System",
            last_name="Admin",
            email=admin_email,
            password_hash=generate_password_hash(admin_password),
            phone_number="0000000000",
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Default admin created successfully.")
    else:
        print("Default admin already exists.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))