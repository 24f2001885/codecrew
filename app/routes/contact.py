import logging
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, abort, request
from app.extensions import db, limiter
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.models.contact_message import ContactMessage
from app.forms.contact_forms import ContactForm
from app.services.mailer import send_contact_notification

logger = logging.getLogger(__name__)

contact_bp = Blueprint("contact", __name__)


def _build_group_detail_context(group, form):
    members = group.members.order_by(Member.display_order.asc()).all()
    projects = group.projects.order_by(Project.featured.desc(), Project.created_at.desc()).all()

    current_year = datetime.utcnow().year
    years_active = max(1, current_year - group.founded_year) if group.founded_year else 1

    stats = {
        "completed_projects": len(projects),
        "members": len(members),
        "years_active": years_active,
        "total_projects": len(projects),
    }
    return {
        "group": group,
        "members": members,
        "projects": projects,
        "stats": stats,
        "form": form,
    }


@contact_bp.route("/group/<slug>/contact", methods=["POST"])
@limiter.limit("5 per hour")
@limiter.limit("30 per day")
def contact(slug):
    group = Group.query.filter_by(slug=slug).first_or_404()
    form = ContactForm()

    # Honeypot spam defense: if filled, act like success without storing
    if form.website.data and form.website.data.strip():
        logger.info(f"[HONEYPOT SPAM] Blocked spam submission on group '{group.name}'")
        flash(f"Thanks — your message was sent to {group.name}.", "success")
        return redirect(url_for("public.group_detail", slug=slug) + "#contact")

    if form.validate_on_submit():
        msg = ContactMessage(
            group_id=group.id,
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            subject=form.subject.data.strip() if form.subject.data else None,
            message=form.message.data.strip(),
        )
        db.session.add(msg)
        db.session.commit()

        # Best effort email notification (SMTP errors never rollback row)
        try:
            send_contact_notification(msg)
        except Exception as e:
            logger.warning(f"Mail notification failed for message {msg.id}: {e}")

        flash(f"Thanks — your message was sent to {group.name}.", "success")
        return redirect(url_for("public.group_detail", slug=slug) + "#contact")

    # On validation errors, re-render group_detail.html with inline errors (HTTP 200)
    ctx = _build_group_detail_context(group, form)
    return render_template("public/group_detail.html", **ctx), 200
