import os
from datetime import datetime, timezone
from flask import Flask, redirect, request, flash, url_for
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
        if flask_app.config.get("UPLOAD_FOLDER"):
            os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
        if flask_app.config.get("PRIVATE_UPLOAD_FOLDER"):
            os.makedirs(flask_app.config["PRIVATE_UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Context processors
    @flask_app.context_processor
    def inject_context():
        return {
            "now": datetime.now(timezone.utc)
        }

    # Error handler for 413 (Request too large)
    @flask_app.errorhandler(413)
    def request_entity_too_large(error):
        flash("That file is larger than 5 MB.", "danger")
        referrer = request.referrer
        if referrer and referrer != request.url:
            return redirect(referrer)
        return redirect(url_for("public.index"))

    # Register blueprints
    # P1/P2/P3 blueprints:
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    # P4 blueprints (lead-capture):
    from app.routes.contact import contact_bp
    from app.routes.requests import requests_bp
    # Remaining blueprints to add: api_bp (P5), join_bp/coder_bp (P7, P8)

    flask_app.register_blueprint(public_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(contact_bp)
    flask_app.register_blueprint(requests_bp)

    # Ensure models are loaded for SQLAlchemy & Flask-Migrate
    with flask_app.app_context():
        from app import models as _models  # noqa: F401

    return flask_app
