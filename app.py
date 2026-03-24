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

with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))