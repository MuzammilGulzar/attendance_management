import os
from dotenv import load_dotenv

load_dotenv()

class ProductionConfig:
    # ------------------------------------------------------------------ #
    #  SECURITY
    # ------------------------------------------------------------------ #
    # SECRET_KEY comes from environment. Validation happens at runtime
    # via validate(), not at import time — so dev imports don't fail.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'CHANGE-ME-IN-PRODUCTION')

    # ------------------------------------------------------------------ #
    #  DATABASE
    # ------------------------------------------------------------------ #
    # Use PostgreSQL in production. Falls back to a prod SQLite file
    # only so imports don't crash — validate() will reject SQLite.
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, '..', 'attendance_prod.db')
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ------------------------------------------------------------------ #
    #  FLASK SETTINGS
    # ------------------------------------------------------------------ #
    DEBUG   = False    # NEVER show debug pages to real users
    TESTING = False

    # ------------------------------------------------------------------ #
    #  SECURITY HEADERS
    # ------------------------------------------------------------------ #
    SESSION_COOKIE_SECURE   = True   # Only send cookie over HTTPS
    SESSION_COOKIE_HTTPONLY  = True   # JS cannot read the cookie
    SESSION_COOKIE_SAMESITE  = 'Lax' # Basic CSRF protection
    WTF_CSRF_ENABLED         = True

    @classmethod
    def validate(cls):
        """
        Call this in production before serving any requests.
        Ensures no dangerous defaults are left in place.
        """
        if cls.SECRET_KEY == 'CHANGE-ME-IN-PRODUCTION':
            raise ValueError("Set a real SECRET_KEY in your environment!")
        if 'sqlite' in cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("Do not use SQLite in production — set DATABASE_URL!")