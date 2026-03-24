from flask import render_template
from app import app

@app.route("/")
def home():
    return render_template("index.html")

# import authentication routes
from routes.auth_routes import *
from routes.student_routes import *
from routes.staff_routes import *