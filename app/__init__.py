import os
from datetime import datetime
from flask import Flask
from app.config import get_config
from app.extensions import db, migrate, login_manager, mail, csrf, limiter


def create_app(config_name=None):
    flask_app = Flask(__name__)
    config_class = get_config(config_name)
    flask_app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(flask_app)
    migrate.init_app(flask_app, db)
    login_manager.init_app(flask_app)
    mail.init_app(flask_app)
    csrf.init_app(flask_app)
    limiter.init_app(flask_app)

    # Ensure upload folders exist
    try:
        os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
        os.makedirs(flask_app.config["PRIVATE_UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Context processors
    @flask_app.context_processor
    def inject_context():
        return {
            "now": datetime.utcnow()
        }

    # Register blueprints
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp

    flask_app.register_blueprint(public_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)

    # Ensure models are loaded for SQLAlchemy & Flask-Migrate
    with flask_app.app_context():
        from app import models as _models  # noqa: F401

    return flask_app
