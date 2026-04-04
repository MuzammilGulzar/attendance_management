import os
from dotenv import load_dotenv

# Load the .env file so os.environ can read our secret values
load_dotenv()

class DevelopmentConfig:
    # ------------------------------------------------------------------ #
    #  SECURITY
    # ------------------------------------------------------------------ #
    # SECRET_KEY signs session cookies.  If someone knows it, they can
    # forge a login session.  NEVER hardcode this — always load from .env.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-fallback-change-in-production')

    # ------------------------------------------------------------------ #
    #  DATABASE
    # ------------------------------------------------------------------ #
    # SQLite is a single file — perfect for local development.
    # No separate database server needed.
    # The file will be created at  attendance_system/attendance_dev.db
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, '..', 'attendance_dev.db')
    )

    # Disable change-tracking notifications (saves memory, not needed)
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------ #
    #  FLASK SETTINGS
    # ------------------------------------------------------------------ #
    DEBUG = True          # Show detailed error pages in browser
    TESTING = False

    # ------------------------------------------------------------------ #
    #  FLASK-WTF  (form protection)
    # ------------------------------------------------------------------ #
    # WTForms automatically adds a hidden CSRF token to every form.
    # This prevents Cross-Site Request Forgery attacks.
    WTF_CSRF_ENABLED = True