import logging
from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from app.extensions import db, limiter
from app.models.project_request import ProjectRequest
from app.models.project_offer import ProjectOffer
from app.models.project_discussion import ProjectDiscussionMessage
from app.models.project_milestone import ProjectMilestone
from app.models.group import Group
from app.models.coder_user import CoderUser
from app.models.member import Member
from app.models.request_access_grant import RequestAccessGrant
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
    milestones = req_item.milestones.all()

    return render_template(
        "public/request_hub.html",
        req_item=req_item,
        offers=offers,
        discussion_messages=discussion_messages,
        milestones=milestones,
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

    # Initialize delivery milestones from offer deliverables if none exist yet
    if req_item.milestones.count() == 0:
        if offer.deliverables and len(offer.deliverables) > 0:
            for item in offer.deliverables:
                ms = ProjectMilestone(
                    project_request_id=req_item.id,
                    created_by_coder_id=offer.coder_id,
                    title=str(item)[:150],
                    status="in_progress",
                )
                db.session.add(ms)
        else:
            starter_ms = ProjectMilestone(
                project_request_id=req_item.id,
                created_by_coder_id=offer.coder_id,
                title="Sprint 1: Architecture Alignment & Core Kickoff",
                status="in_progress",
            )
            db.session.add(starter_ms)

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


@requests_bp.route("/request/<id>/hub/milestone/<milestone_id>/approve", methods=["POST"])
def approve_milestone(id, milestone_id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    milestone = db.session.get(ProjectMilestone, milestone_id) or abort(404)
    if milestone.project_request_id != req_item.id:
        abort(400)

    milestone.status = "completed"
    milestone.completed_at = datetime.now(timezone.utc)

    disc_msg = ProjectDiscussionMessage(
        project_request_id=req_item.id,
        sender_type="system",
        sender_name="Platform System",
        content=f"✅ Client {req_item.name} approved milestone '{milestone.title}'! ({req_item.progress_percentage}% completed)",
    )
    db.session.add(disc_msg)

    # If all milestones are completed, update request status to completed
    if req_item.milestones.filter(ProjectMilestone.status != "completed").count() == 0:
        req_item.status = "completed"
        disc_complete = ProjectDiscussionMessage(
            project_request_id=req_item.id,
            sender_type="system",
            sender_name="Platform System",
            content="🏆 All project milestones have been completed and approved! Contract successfully delivered.",
        )
        db.session.add(disc_complete)

    db.session.commit()
    flash(f"Milestone '{milestone.title}' approved successfully!", "success")
    return redirect(url_for("requests.request_hub", id=id))


@requests_bp.route("/request/<id>/hub/complete", methods=["POST"])
def complete_project(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    req_item.status = "completed"
    disc_msg = ProjectDiscussionMessage(
        project_request_id=req_item.id,
        sender_type="system",
        sender_name="Platform System",
        content=f"🎉 Client {req_item.name} officially signed off and completed the project delivery!",
    )
    db.session.add(disc_msg)
    db.session.commit()
    flash("Project signed off and marked as completed. Thank you for building with CodeCrews squads!", "success")
    return redirect(url_for("requests.request_hub", id=id))


@requests_bp.route("/group/<slug>/chat-representative", methods=["POST"])
@limiter.limit("5 per hour")
def chat_representative(slug):
    group = Group.query.filter_by(slug=slug).first_or_404()
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    project_type = request.form.get("project_type", "Custom Squad Collaboration").strip()
    budget_range = request.form.get("budget_range", "To be discussed").strip()
    description = request.form.get("message", "").strip()

    if not name or not email or not description:
        flash("Please provide your name, email, and a message to connect with the squad.", "warning")
        return redirect(url_for("public.group_detail", slug=slug) + "#contact")

    project_req = ProjectRequest(
        name=name,
        email=email,
        project_type=project_type,
        budget_range=budget_range,
        description=description,
        assigned_group_id=group.id,
        status="in_review",
    )
    db.session.add(project_req)
    db.session.flush()

    # Automatically grant access to coders in this group so they can review and negotiate
    from app.models.admin_user import AdminUser
    admin = AdminUser.query.first()
    admin_id = admin.id if admin else None
    squad_coders = CoderUser.query.join(Member).filter(Member.group_id == group.id).all()
    for cu in squad_coders:
        grant = RequestAccessGrant(
            project_request_id=project_req.id,
            coder_id=cu.id,
            scope="brief_and_contact",
            granted_by_admin_id=admin_id,
        )
        db.session.add(grant)

    # Initial messages in thread
    init_msg = ProjectDiscussionMessage(
        project_request_id=project_req.id,
        sender_type="client",
        sender_name=f"{name} (Client)",
        content=description,
    )
    db.session.add(init_msg)

    sys_msg = ProjectDiscussionMessage(
        project_request_id=project_req.id,
        sender_type="system",
        sender_name="Platform System",
        content=f"💬 Direct chat initiated with '{group.name}' representative. Squad coders have been notified and granted project room access.",
    )
    db.session.add(sys_msg)
    db.session.commit()

    flash(f"Direct inquiry room created with {group.name}! Chat directly with the squad representative below.", "success")
    return redirect(url_for("requests.request_hub", id=project_req.id))

