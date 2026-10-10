from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort, current_app
from app.extensions import db, limiter
from app.models.coder_application import CoderApplication
from app.models.domain_alert_delivery import DomainAlertDelivery
from app.models.site_settings import SiteSettings
from app.forms.join_forms import JoinApplicationForm
from app.services.tokens import make_token, read_token, max_age_for
from app.services.mailer import send_application_verify, send_application_new_admin
from app.services.private_files import save_private, RESUME_EXTENSIONS, UploadError
from app.services.audit import record_audit

join_bp = Blueprint("join", __name__, url_prefix="/join")


@join_bp.route("", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def join():
    settings = SiteSettings.get_settings()
    if not settings.coder_applications_open:
        return render_template("public/join_closed.html"), 404

    form = JoinApplicationForm()
    if request.method == "POST":
        # Honeypot spam trap
        if form.honeypot.data:
            flash("Thank you for your application!", "success")
            return redirect(url_for("join.thanks"))

        if form.validate_on_submit():
            email = form.email.data.strip().lower()
            resume_path = None
            if form.resume_pdf.data and getattr(form.resume_pdf.data, "filename", None):
                try:
                    resume_path = save_private(form.resume_pdf.data, "applications", RESUME_EXTENSIONS)
                except UploadError as ue:
                    flash(f"Resume upload error: {ue}", "danger")
                    return render_template("public/join.html", form=form)

            app_record = CoderApplication.query.filter_by(email=email).first()
            if app_record:
                app_record.name = form.name.data.strip()
                app_record.project_types = list(form.project_types.data or [])
                app_record.domain_tags = form.parse_tags()
                app_record.headline = form.headline.data.strip() if form.headline.data else None
                app_record.portfolio_url = form.portfolio_url.data.strip() if form.portfolio_url.data else None
                app_record.message = form.message.data.strip() if form.message.data else None
                if resume_path:
                    app_record.resume_pdf = resume_path
                app_record.alerts_consent = True
                app_record.consent_at = datetime.utcnow()

                if not app_record.email_verified_at:
                    token = make_token("app-verify", {"id": app_record.id})
                    verify_url = url_for("join.verify", token=token, _external=True)
                    send_application_verify(app_record, verify_url)

                record_audit("public", None, "application.updated", "coder_application", str(app_record.id))
                db.session.commit()
                flash("Your application has been updated.", "info")
            else:
                app_record = CoderApplication(
                    name=form.name.data.strip(),
                    email=email,
                    project_types=list(form.project_types.data or []),
                    domain_tags=form.parse_tags(),
                    headline=form.headline.data.strip() if form.headline.data else None,
                    portfolio_url=form.portfolio_url.data.strip() if form.portfolio_url.data else None,
                    message=form.message.data.strip() if form.message.data else None,
                    resume_pdf=resume_path,
                    alerts_consent=True,
                    consent_at=datetime.utcnow(),
                    status="pending",
                )
                db.session.add(app_record)
                db.session.flush()

                token = make_token("app-verify", {"id": app_record.id})
                verify_url = url_for("join.verify", token=token, _external=True)
                send_application_verify(app_record, verify_url)

                record_audit("public", None, "application.created", "coder_application", str(app_record.id))
                db.session.commit()

            return redirect(url_for("join.thanks"))

    return render_template("public/join.html", form=form)


@join_bp.route("/thanks")
def thanks():
    return render_template("public/join_thanks.html")


@join_bp.route("/verify/<token>")
@limiter.limit("30 per minute")
def verify(token):
    max_age = max_age_for("app-verify")
    payload = read_token("app-verify", token, max_age=max_age)
    if not payload or not isinstance(payload, dict) or "id" not in payload:
        return render_template("public/join_verify_error.html", message="The verification link is invalid or has expired."), 400

    app_record = db.session.get(CoderApplication, payload["id"])
    if not app_record:
        return render_template("public/join_verify_error.html", message="The requested application could not be found."), 404

    if not app_record.email_verified_at:
        app_record.email_verified_at = datetime.utcnow()
        record_audit("public", None, "application.verified", "coder_application", str(app_record.id))
        db.session.commit()
        send_application_new_admin(app_record)

    return render_template("public/join_verified.html", application=app_record)


@join_bp.route("/unsubscribe/<token>", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def unsubscribe(token):
    payload = read_token("app-unsub", token)
    if not payload or not isinstance(payload, dict) or "id" not in payload and "application_id" not in payload:
        return render_template("public/join_verify_error.html", message="The unsubscribe link is invalid or corrupted."), 400

    app_id = payload.get("id") or payload.get("application_id")
    app_record = db.session.get(CoderApplication, app_id)
    if not app_record:
        return render_template("public/join_verify_error.html", message="Application record not found."), 404

    if not app_record.unsubscribed_at:
        app_record.unsubscribed_at = datetime.utcnow()
        record_audit("public", None, "application.unsubscribed", "coder_application", str(app_record.id))
        db.session.commit()

    return render_template("public/join_unsubscribed.html", application=app_record)


@join_bp.route("/interested/<token>", methods=["GET", "POST"])
@limiter.limit("30 per minute")
def interested(token):
    max_age = max_age_for("alert-interest")
    payload = read_token("alert-interest", token, max_age=max_age)
    if not payload or not isinstance(payload, dict) or "id" not in payload and "delivery_id" not in payload:
        return render_template("public/join_verify_error.html", message="The opportunity link is invalid or has expired."), 400

    del_id = payload.get("id") or payload.get("delivery_id")
    delivery = db.session.get(DomainAlertDelivery, del_id)
    if not delivery:
        return render_template("public/join_verify_error.html", message="Opportunity record not found."), 404

    if request.method == "POST":
        if not delivery.interested_at:
            delivery.interested_at = datetime.utcnow()
            record_audit("public", None, "alert.interested", "domain_alert_delivery", str(delivery.id))
            db.session.commit()
        return render_template("public/join_interested_thanks.html")

    return render_template("public/join_interested_confirm.html", delivery=delivery, token=token)
