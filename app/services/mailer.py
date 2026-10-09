import logging
from flask import current_app, render_template, url_for
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def _send(subject, body, recipients):
    """
    Private helper: sends an email via Flask-Mail safely.
    Logs errors and returns True/False. Never re-raises exceptions.
    """
    try:
        sender = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@codecrews.example")
        msg = Message(subject=subject, sender=sender, recipients=recipients, body=body)
        mail.send(msg)
        logger.info(f"[MAIL SENT] Subject: {subject} to {recipients}")
        return True
    except Exception as e:
        logger.exception(f"[MAIL FAILED] Failed sending '{subject}' to {recipients}: {e}")
        return False


def send_email(subject, recipients, text_body, html_body=None):
    """
    Backwards-compatible wrapper around _send.
    """
    return _send(subject, text_body, recipients)


def send_password_reset_email(admin_user, reset_url):
    """
    Sends password reset instructions to admin notification email.
    """
    recipient = current_app.config.get("ADMIN_NOTIFICATION_EMAIL", "admin@codecrews.example")
    subject = "CodeCrews Admin Password Reset"
    text_body = f"""Hello {admin_user.username},

You requested a password reset for your CodeCrews super-admin account.
Please visit the following link to choose a new password:

{reset_url}

This link is valid for {current_app.config.get('RESET_TOKEN_MAX_AGE', 3600) // 60} minutes and can only be used once.

If you did not request this, you can safely ignore this email.
"""
    return _send(subject, text_body, [recipient])


def send_contact_notification(contact_message):
    """
    Notifies super-admin of a new inquiry submitted to a group's contact form.
    """
    recipient = current_app.config.get("ADMIN_NOTIFICATION_EMAIL", "admin@codecrews.example")
    group_name = contact_message.group.name if contact_message.group else "CodeCrews"
    subject = f"New Contact Message — {group_name}"

    try:
        inbox_url = url_for("admin.messages", _external=True)
    except Exception:
        inbox_url = "/admin/messages"

    body = render_template(
        "emails/new_contact.txt",
        group_name=group_name,
        sender_name=contact_message.name,
        sender_email=contact_message.email,
        subject=contact_message.subject,
        message=contact_message.message,
        inbox_url=inbox_url,
    )
    return _send(subject, body, [recipient])


def send_project_request_notification(project_request):
    """
    Notifies super-admin of a new platform-wide project request.
    (Note: Coder/applicant notifications arrive in P7/P8).
    """
    recipient = current_app.config.get("ADMIN_NOTIFICATION_EMAIL", "admin@codecrews.example")
    type_labels = {
        "web_app": "Web App",
        "mobile_app": "Mobile App",
        "desktop_software": "Desktop Software",
        "api_backend": "API / Backend",
        "other": "Other",
    }
    type_label = type_labels.get(project_request.project_type, project_request.project_type)
    subject = f"New Project Request — {type_label}"

    desc = project_request.description or ""
    excerpt = desc[:300] + ("..." if len(desc) > 300 else "")

    try:
        inbox_url = url_for("admin.project_requests", _external=True)
    except Exception:
        inbox_url = "/admin/project-requests"

    body = render_template(
        "emails/new_project_request.txt",
        requester_name=project_request.name,
        requester_email=project_request.email,
        company=project_request.company,
        project_type=type_label,
        budget=project_request.budget_range,
        timeline=project_request.timeline,
        has_attachment=bool(project_request.attachment_path),
        excerpt=excerpt,
        inbox_url=inbox_url,
    )
    return _send(subject, body, [recipient])


def send_coder_invite(coder, token):
    """
    Sends invite email with set-password link to a newly created coder.
    """
    try:
        invite_url = url_for("coder_auth.accept_invite", token=token, _external=True)
    except Exception:
        invite_url = f"/coder/accept-invite/{token}"

    subject = "Welcome to CodeCrews — Set Up Your Coder Account"
    body = render_template("emails/coder_invite.txt", coder=coder, invite_url=invite_url)
    return _send(subject, body, [coder.email])


def send_coder_password_reset(coder, token):
    """
    Sends password reset instructions to a coder.
    """
    try:
        reset_url = url_for("coder_auth.reset_password", token=token, _external=True)
    except Exception:
        reset_url = f"/coder/reset-password/{token}"

    max_age_min = current_app.config.get("RESET_TOKEN_MAX_AGE", 3600) // 60
    subject = "CodeCrews Coder Password Reset"
    body = render_template("emails/password_reset_coder.txt", coder=coder, reset_url=reset_url, max_age_minutes=max_age_min)
    return _send(subject, body, [coder.email])


def send_opportunity_assigned(coder, grant):
    """
    Notifies coder that a project request has been granted to them.
    Never includes confidential requester details in the email.
    """
    try:
        opp_url = url_for("coder.opportunity_detail", request_id=grant.request_id, _external=True)
    except Exception:
        opp_url = f"/coder/opportunities/{grant.request_id}"

    scope_label = "Brief Only" if grant.scope == "brief_only" else "Brief & Contact Details"
    subject = "New Project Opportunity Assigned — CodeCrews"
    body = render_template("emails/opportunity_assigned.txt", coder=coder, scope=scope_label, opportunity_url=opp_url)
    return _send(subject, body, [coder.email])

