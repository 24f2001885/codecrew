import logging
from flask import current_app
from flask_mail import Message
from app.extensions import mail

logger = logging.getLogger(__name__)


def send_email(subject, recipients, text_body, html_body=None):
    """
    Sends an email via Flask-Mail in a safe, best-effort manner.
    Never raises an uncaught exception on SMTP failure.
    """
    if current_app.config.get("MAIL_SUPPRESS_SEND", False):
        logger.info(f"[MAIL SUPPRESSED] Subject: {subject} to {recipients}")
        return True

    try:
        sender = current_app.config.get("MAIL_DEFAULT_SENDER", "noreply@codecrews.example")
        msg = Message(subject=subject, sender=sender, recipients=recipients)
        msg.body = text_body
        if html_body:
            msg.html = html_body
        mail.send(msg)
        return True
    except Exception as e:
        logger.error(f"[MAIL ERROR] Failed sending email '{subject}' to {recipients}: {e}")
        return False


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
    return send_email(subject, [recipient], text_body)
