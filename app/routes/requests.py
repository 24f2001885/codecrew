import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request
from app.extensions import db, limiter
from app.models.project_request import ProjectRequest
from app.forms.request_forms import RequestForm
from app.services.private_files import save_private
from app.services.uploads import UploadError
from app.services.mailer import send_project_request_notification

logger = logging.getLogger(__name__)

requests_bp = Blueprint("requests", __name__)


@requests_bp.route("/request-project", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def request_project():
    form = RequestForm()

    if request.method == "POST":
        # Honeypot spam defense: if filled, act like success without saving
        if form.website.data and form.website.data.strip():
            logger.info("[HONEYPOT SPAM] Blocked spam project request.")
            flash("Thanks — we received your request.", "success")
            return redirect(url_for("requests.request_project"))

        if form.validate_on_submit():
            stored_attachment_name = None
            if form.attachment.data and getattr(form.attachment.data, "filename", None):
                try:
                    stored_attachment_name = save_private(
                        form.attachment.data,
                        "requests",
                        {".pdf", ".docx"},
                    )
                except UploadError as ue:
                    form.attachment.errors.append(str(ue))
                    return render_template("public/request_project.html", form=form), 200
                except Exception as e:
                    logger.error(f"Failed to save private attachment: {e}")
                    form.attachment.errors.append("Could not process attachment.")
                    return render_template("public/request_project.html", form=form), 200

            project_req = ProjectRequest(
                name=form.name.data.strip(),
                email=form.email.data.strip(),
                company=form.company.data.strip() if form.company.data else None,
                project_type=form.project_type.data,
                budget_range=form.budget_range.data.strip() if form.budget_range.data else None,
                timeline=form.timeline.data.strip() if form.timeline.data else None,
                description=form.description.data.strip(),
                attachment_path=stored_attachment_name,
                status="new",
            )
            db.session.add(project_req)
            db.session.commit()

            # Best effort email notification
            try:
                send_project_request_notification(project_req)
            except Exception as e:
                logger.warning(f"Mail notification failed for project request {project_req.id}: {e}")

            # Auto domain alert if enabled in site settings
            try:
                from app.models.site_settings import SiteSettings
                from app.services.alerts import send_alert_batch, format_default_summary
                settings = SiteSettings.get_settings()
                if getattr(settings, "auto_send_domain_alerts", False):
                    summary = format_default_summary(project_req)
                    send_alert_batch(project_req, summary=summary, admin_id=None, is_auto=True)
            except Exception as e:
                logger.warning(f"Auto domain alert failed for project request {project_req.id}: {e}")

            flash("Thanks — we received your request.", "success")
            return redirect(url_for("requests.request_project"))

    return render_template("public/request_project.html", form=form)
