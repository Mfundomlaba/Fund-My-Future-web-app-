import os


class Config:
    SECRET_KEY = "supersecretkey"

    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

    # ✅ FIXED DATABASE PATH (works on Render)
    DB_PATH = os.path.join(BASE_DIR, "database.db")

    SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # =========================
    # EMAIL CONFIGURATION
    # =========================
    MAIL_PROVIDER = os.environ.get("MAIL_PROVIDER", "")
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")

    # =========================
    # BREVO CONFIGURATION
    # =========================
    BREVO_API_KEY = os.environ.get("Brevo_API_Key", "")
    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"
    BREVO_SENDER_NAME = os.environ.get("BREVO_SENDER_NAME", "Fund My Future")