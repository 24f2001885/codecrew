import os
from datetime import timedelta


class BaseConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-to-a-random-secret")
    WTF_CSRF_SECRET_KEY = os.environ.get("WTF_CSRF_SECRET_KEY", "change-me-too")
    WTF_CSRF_ENABLED = True

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.example.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "True").lower() in ("true", "1", "yes")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", None)
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", None)
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "noreply@codecrews.example")
    MAIL_SUPPRESS_SEND = os.environ.get("MAIL_SUPPRESS_SEND", "False").lower() in ("true", "1", "yes")
    ADMIN_NOTIFICATION_EMAIL = os.environ.get("ADMIN_NOTIFICATION_EMAIL", "admin@codecrews.example")

    # Uploads - UPLOAD_FOLDER is for PUBLIC media only (never store private attachments/resumes here)
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "app/static/uploads")
    # PRIVATE_UPLOAD_FOLDER: request attachments + applicant resumes (never served statically)
    PRIVATE_UPLOAD_FOLDER = os.environ.get("PRIVATE_UPLOAD_FOLDER", "instance/private_uploads")
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 5242880))  # 5MB

    # Session & Security
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False").lower() in ("true", "1", "yes")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    CODER_SESSION_HOURS = int(os.environ.get("CODER_SESSION_HOURS", 8))
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.environ.get("CODER_SESSION_HOURS", 8)))

    # Token lifetimes (seconds)
    RESET_TOKEN_MAX_AGE = int(os.environ.get("RESET_TOKEN_MAX_AGE", 3600))
    INVITE_TOKEN_MAX_AGE = int(os.environ.get("INVITE_TOKEN_MAX_AGE", 259200))
    APPLICATION_VERIFY_MAX_AGE = int(os.environ.get("APPLICATION_VERIFY_MAX_AGE", 604800))
    INTERESTED_TOKEN_MAX_AGE = int(os.environ.get("INTERESTED_TOKEN_MAX_AGE", 2592000))

    # Coder applications & alerts
    ALERT_BATCH_SIZE = int(os.environ.get("ALERT_BATCH_SIZE", 100))
    UNVERIFIED_APPLICATION_TTL_DAYS = int(os.environ.get("UNVERIFIED_APPLICATION_TTL_DAYS", 30))

    # Seed credentials
    ADMIN_SEED_USERNAME = os.environ.get("ADMIN_SEED_USERNAME", "admin")
    ADMIN_SEED_PASSWORD = os.environ.get("ADMIN_SEED_PASSWORD", "change-me-before-running-seed")


class DevConfig(BaseConfig):
    DEBUG = True
    FLASK_ENV = "development"


class TestingConfig(BaseConfig):
    TESTING = True
    DEBUG = True
    FLASK_ENV = "testing"
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    PRIVATE_UPLOAD_FOLDER = os.environ.get("PRIVATE_UPLOAD_FOLDER", "instance/test_private_uploads")


class ProdConfig(BaseConfig):
    DEBUG = False
    FLASK_ENV = "production"
    SESSION_COOKIE_SECURE = True


CONFIG_MAP = {
    "development": DevConfig,
    "testing": TestingConfig,
    "production": ProdConfig,
}


def get_config(name=None):
    if not name:
        name = os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(name.lower(), DevConfig)
