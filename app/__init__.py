import os
import logging
from datetime import datetime, timezone
from flask import Flask, redirect, request, flash, url_for, render_template
from werkzeug.exceptions import HTTPException
from app.config import get_config
from app.extensions import db, migrate, login_manager, mail, csrf, limiter
from app.services.site_context import get_site_settings, platform_stats, seo_for


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

    # Production ProxyFix support
    trusted_proxies = flask_app.config.get("TRUSTED_PROXY_COUNT", os.environ.get("TRUSTED_PROXY_COUNT", 0))
    try:
        trusted_proxies = int(trusted_proxies)
    except (ValueError, TypeError):
        trusted_proxies = 0

    if trusted_proxies > 0:
        from werkzeug.middleware.proxy_fix import ProxyFix
        flask_app.wsgi_app = ProxyFix(
            flask_app.wsgi_app,
            x_for=trusted_proxies,
            x_proto=trusted_proxies,
            x_host=trusted_proxies,
            x_port=trusted_proxies,
            x_prefix=trusted_proxies,
        )

    # Ensure upload folders exist
    try:
        if flask_app.config.get("UPLOAD_FOLDER"):
            os.makedirs(flask_app.config["UPLOAD_FOLDER"], exist_ok=True)
        if flask_app.config.get("PRIVATE_UPLOAD_FOLDER"):
            os.makedirs(flask_app.config["PRIVATE_UPLOAD_FOLDER"], exist_ok=True)
    except OSError:
        pass

    # Context processors (P6)
    @flask_app.context_processor
    def inject_context():
        return {
            "now": datetime.now(timezone.utc),
            "site_settings": get_site_settings(),
            "platform_stats": platform_stats,
            "seo_for": seo_for,
        }

    # After-request security headers (P6)
    @flask_app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "SAMEORIGIN"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Content-Security-Policy allow-list:
        # self + CDNs used by base.html (Bootstrap, jQuery, Popper, AOS, OwlCarousel, FontAwesome/Fonts)
        # Note: unsafe-inline is kept for styles only
        cdn_hosts = "https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net https://code.jquery.com https://fonts.googleapis.com https://fonts.gstatic.com"
        csp_policy = (
            f"default-src 'self' {cdn_hosts}; "
            f"style-src 'self' 'unsafe-inline' https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            f"script-src 'self' https://code.jquery.com https://cdn.jsdelivr.net https://stackpath.bootstrapcdn.com https://cdnjs.cloudflare.com; "
            f"font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:;"
        )
        response.headers["Content-Security-Policy"] = csp_policy
        return response

    # Error handler for 413 (Request too large)
    @flask_app.errorhandler(413)
    def request_entity_too_large(error):
        flash("That file is larger than 5 MB.", "danger")
        referrer = request.referrer
        if referrer and referrer != request.url:
            return redirect(referrer)
        return redirect(url_for("public.index"))

    # Themed Error Handlers (P6)
    @flask_app.errorhandler(404)
    def page_not_found(error):
        return render_template("errors/404.html"), 404

    @flask_app.errorhandler(429)
    def ratelimit_handler(error):
        return render_template("errors/429.html"), 429

    @flask_app.errorhandler(500)
    def internal_server_error(error):
        flask_app.logger.error("Internal Server Error: %s", error, exc_info=True)
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template("errors/500.html"), 500

    @flask_app.errorhandler(Exception)
    def handle_unhandled_exception(error):
        if isinstance(error, HTTPException):
            if error.code == 404:
                return render_template("errors/404.html"), 404
            if error.code == 429:
                return render_template("errors/429.html"), 429
            if error.code == 413:
                return request_entity_too_large(error)
            return error

        flask_app.logger.error("Unhandled Exception: %s", error, exc_info=True)
        try:
            db.session.rollback()
        except Exception:
            pass
        return render_template("errors/500.html"), 500

    # Register blueprints
    # P1/P2/P3 blueprints:
    from app.routes.public import public_bp
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    # P4 blueprints (lead-capture):
    from app.routes.contact import contact_bp
    from app.routes.requests import requests_bp
    # P5 blueprint:
    from app.routes.api import api_bp
    # P7 blueprints:
    from app.routes.coder_auth import coder_auth_bp
    from app.routes.coder import coder_bp

    flask_app.register_blueprint(public_bp)
    flask_app.register_blueprint(auth_bp)
    flask_app.register_blueprint(admin_bp)
    flask_app.register_blueprint(contact_bp)
    flask_app.register_blueprint(requests_bp)
    limiter.limit("120 per minute")(api_bp)
    flask_app.register_blueprint(api_bp)
    flask_app.register_blueprint(coder_auth_bp)
    flask_app.register_blueprint(coder_bp)

    # Ensure models are loaded for SQLAlchemy & Flask-Migrate
    with flask_app.app_context():
        from app import models as _models  # noqa: F401

    return flask_app
