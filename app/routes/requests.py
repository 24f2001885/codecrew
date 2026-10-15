import logging
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from app.extensions import db, limiter
from app.models.project_request import ProjectRequest
from app.models.project_offer import ProjectOffer
from app.models.project_discussion import ProjectDiscussionMessage
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


@requests_bp.route("/request/<id>/hub", methods=["GET"])
def request_hub(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    offers = req_item.offers.order_by(ProjectOffer.created_at.desc()).all()
    discussion_messages = req_item.discussion_messages.order_by(ProjectDiscussionMessage.created_at.asc()).all()

    return render_template(
        "public/request_hub.html",
        req_item=req_item,
        offers=offers,
        discussion_messages=discussion_messages,
    )


@requests_bp.route("/request/<id>/hub/accept-offer/<offer_id>", methods=["POST"])
def accept_offer(id, offer_id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    offer = db.session.get(ProjectOffer, offer_id) or abort(404)

    if offer.project_request_id != req_item.id:
        abort(400)

    # Accept this offer and decline others
    offer.status = "accepted"
    for other in req_item.offers:
        if other.id != offer.id:
            other.status = "declined"

    req_item.status = "assigned"
    req_item.assigned_group_id = offer.group_id

    disc_msg = ProjectDiscussionMessage(
        project_request_id=req_item.id,
        sender_type="system",
        sender_name="Platform System",
        content=f"🎉 Offer accepted! Customer has officially awarded the project to squad '{offer.group.name}' at {offer.proposed_budget} ({offer.proposed_timeline}).",
    )
    db.session.add(disc_msg)
    db.session.commit()

    flash(f"Congratulations! You accepted the offer from '{offer.group.name}'. You can now chat directly below to coordinate project milestones.", "success")
    return redirect(url_for("requests.request_hub", id=id))


@requests_bp.route("/request/<id>/hub/discuss", methods=["POST"])
def client_discuss(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    content = request.form.get("content", "").strip()
    sender_name = request.form.get("sender_name", "").strip() or req_item.name

    if content:
        msg = ProjectDiscussionMessage(
            project_request_id=req_item.id,
            sender_type="client",
            sender_name=f"{sender_name} (Client)",
            content=content,
        )
        db.session.add(msg)
        db.session.commit()
        flash("Message sent to the engineering squad.", "success")

    return redirect(url_for("requests.request_hub", id=id))


@requests_bp.route("/request/find", methods=["GET", "POST"])
def find_request():
    matched_requests = []
    searched_email = ""
    if request.method == "POST":
        searched_email = request.form.get("email", "").strip().lower()
        if searched_email:
            matched_requests = ProjectRequest.query.filter(
                db.func.lower(ProjectRequest.email) == searched_email
            ).order_by(ProjectRequest.created_at.desc()).all()

    return render_template(
        "public/find_request.html",
        matched_requests=matched_requests,
        searched_email=searched_email,
    )
