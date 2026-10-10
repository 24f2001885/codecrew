import re
from datetime import datetime
from flask import current_app, url_for
from app.extensions import db
from app.models.coder_application import CoderApplication
from app.models.domain_alert import DomainAlert
from app.models.domain_alert_delivery import DomainAlertDelivery
from app.services.tokens import make_token
from app.services.mailer import send_domain_alert
from app.services.audit import record_audit

PROJECT_TYPE_LABELS = {
    "web_app": "Web Application",
    "mobile_app": "Mobile App",
    "desktop_software": "Desktop Software",
    "api_backend": "API / Backend",
    "other": "Software",
}


def normalize_tags(tags):
    """
    Normalizes a list or comma-separated string of tags:
    lower-cases, strips whitespace, collapses multiple internal spaces, drops empties.
    """
    if not tags:
        return []
    if isinstance(tags, str):
        raw_list = tags.split(",")
    elif isinstance(tags, (list, tuple, set)):
        raw_list = tags
    else:
        return []

    normalized = []
    for t in raw_list:
        if not t:
            continue
        cleaned = re.sub(r"\s+", " ", str(t).strip().lower())
        if cleaned and cleaned not in normalized:
            normalized.append(cleaned)
    return normalized


def get_request_tokens(project_request):
    """
    Computes request token set:
    normalize(request.domain_tags) U {normalize(request.project_type)}
    """
    tags = set(normalize_tags(getattr(project_request, "domain_tags", None) or []))
    p_type = getattr(project_request, "project_type", "")
    if p_type:
        tags.add(re.sub(r"\s+", " ", str(p_type).strip().lower()))
    return tags


def get_application_tokens(application):
    """
    Computes applicant token set:
    normalize(application.domain_tags) U normalize(application.project_types)
    """
    tags = set(normalize_tags(getattr(application, "domain_tags", None) or []))
    p_types = set(normalize_tags(getattr(application, "project_types", None) or []))
    return tags | p_types


def is_application_eligible(application, project_request_id):
    """
    An application is eligible iff:
    email_verified_at IS NOT NULL
    AND alerts_consent == True
    AND unsubscribed_at IS NULL
    AND status IN ('pending', 'approved')
    AND no delivery recorded for this project_request.
    """
    if not application or not application.email_verified_at:
        return False
    if not application.alerts_consent:
        return False
    if application.unsubscribed_at is not None:
        return False
    if application.status not in ("pending", "approved"):
        return False

    already_delivered = (
        db.session.query(DomainAlertDelivery.id)
        .join(DomainAlert, DomainAlertDelivery.alert_id == DomainAlert.id)
        .filter(
            DomainAlert.project_request_id == project_request_id,
            DomainAlertDelivery.application_id == application.id,
        )
        .first()
    )
    return already_delivered is None


def find_matching_applications(project_request, limit=5000):
    """
    Finds eligible applicants whose token set intersects the request's token set.
    Done in Python after one bounded query (<= limit eligible rows).
    """
    if not project_request:
        return []

    req_tokens = get_request_tokens(project_request)
    if not req_tokens:
        return []

    # Exclude applications that already received an alert for this request
    delivered_app_subquery = (
        db.session.query(DomainAlertDelivery.application_id)
        .join(DomainAlert, DomainAlertDelivery.alert_id == DomainAlert.id)
        .filter(DomainAlert.project_request_id == project_request.id)
        .subquery()
    )

    eligible_applications = (
        CoderApplication.query.filter(
            CoderApplication.email_verified_at.isnot(None),
            CoderApplication.alerts_consent.is_(True),
            CoderApplication.unsubscribed_at.is_(None),
            CoderApplication.status.in_(["pending", "approved"]),
            ~CoderApplication.id.in_(db.select(delivered_app_subquery.c.application_id)),
        )
        .order_by(CoderApplication.created_at.asc())
        .limit(limit)
        .all()
    )

    matches = []
    for app in eligible_applications:
        app_tokens = get_application_tokens(app)
        if app_tokens & req_tokens:
            matches.append(app)

    return matches


def format_default_summary(project_request):
    """
    Generates anonymized prefilled summary:
    'New {project_type label} project — domains: {tags}.' (max 600 chars)
    """
    type_label = PROJECT_TYPE_LABELS.get(project_request.project_type, project_request.project_type or "Software")
    tags = ", ".join(project_request.domain_tags) if project_request.domain_tags else "general"
    summary = f"New {type_label} project — domains: {tags}."
    return summary[:600]


def send_alert_batch(project_request, summary, admin_id=None, is_auto=False, batch_size=None):
    """
    Sends one batch of domain alert emails for the project request.
    Creates DomainAlert and DomainAlertDelivery rows, sends emails, records audit log.
    Returns: {"sent": int, "failed": int, "remaining": int, "alert_id": str}
    """
    if batch_size is None:
        batch_size = current_app.config.get("ALERT_BATCH_SIZE", 100)

    matches = find_matching_applications(project_request)
    batch = matches[:batch_size]

    if not batch:
        return {
            "sent": 0,
            "failed": 0,
            "remaining": 0,
            "alert_id": None,
        }

    alert = DomainAlert(
        project_request_id=project_request.id,
        summary=summary.strip(),
        project_type_snapshot=str(project_request.project_type),
        domain_tags_snapshot=project_request.domain_tags or [],
        is_auto=is_auto,
        sent_by_admin_id=admin_id,
        recipient_count=len(batch),
    )
    db.session.add(alert)
    db.session.flush()

    sent_count = 0
    failed_count = 0

    for app in batch:
        delivery = DomainAlertDelivery(
            alert_id=alert.id,
            application_id=app.id,
            status="sent",
        )
        db.session.add(delivery)
        db.session.flush()

        interested_token = make_token("alert-interest", {"delivery_id": delivery.id})
        unsub_token = make_token("app-unsub", {"application_id": app.id})

        interested_url = url_for("join.interested", token=interested_token, _external=True)
        unsubscribe_url = url_for("join.unsubscribe", token=unsub_token, _external=True)

        try:
            send_domain_alert(
                recipient_email=app.email,
                summary=summary.strip(),
                interested_url=interested_url,
                unsubscribe_url=unsubscribe_url,
            )
            sent_count += 1
        except Exception as e:
            failed_count += 1
            delivery.status = "failed"
            delivery.error = str(e)[:255]
            current_app.logger.error("Failed to send domain alert to %s: %s", app.email, e)

    actor_type = "system" if is_auto else "admin"
    actor_id = str(admin_id) if admin_id else None
    record_audit(
        actor_type=actor_type,
        actor_id=actor_id,
        action="alert.sent",
        target_type="project_request",
        target_id=str(project_request.id),
        summary=f"Sent domain alert batch to {sent_count} applicants ({failed_count} failed)",
        details={
            "alert_id": alert.id,
            "sent": sent_count,
            "failed": failed_count,
            "is_auto": is_auto,
        },
    )

    db.session.commit()

    remaining_count = max(0, len(matches) - len(batch))
    return {
        "sent": sent_count,
        "failed": failed_count,
        "remaining": remaining_count,
        "alert_id": alert.id,
    }
