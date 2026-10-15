from flask import Blueprint, jsonify, request
from flask_login import current_user
from app.extensions import db
from app.models.app_notification import AppNotification
from app.models.admin_user import AdminUser
from app.models.coder_user import CoderUser
from app.services.notifications import (
    get_recent_notifications,
    get_unread_count,
    mark_notification_read,
    mark_all_read,
)

notifications_bp = Blueprint("notifications", __name__, url_prefix="/notifications")


def _get_current_recipient():
    if current_user.is_authenticated:
        if isinstance(current_user, AdminUser):
            return "admin", str(current_user.id)
        elif isinstance(current_user, CoderUser):
            return "coder", str(current_user.id)
    # Check client request param
    client_req_id = request.args.get("client_request_id") or request.form.get("client_request_id")
    if client_req_id:
        return "client", str(client_req_id)
    return None, None


@notifications_bp.route("/api/recent")
def recent_notifications():
    recipient_type, recipient_id = _get_current_recipient()
    if not recipient_type:
        return jsonify({"unread_count": 0, "notifications": []})

    unread_count = get_unread_count(recipient_type, recipient_id)
    notifications = get_recent_notifications(recipient_type, recipient_id, limit=8)

    return jsonify({
        "unread_count": unread_count,
        "notifications": [n.to_dict() for n in notifications],
    })


@notifications_bp.route("/api/<id>/read", methods=["POST"])
def read_notification(id):
    success = mark_notification_read(id)
    return jsonify({"success": success})


@notifications_bp.route("/api/read-all", methods=["POST"])
def read_all_notifications():
    recipient_type, recipient_id = _get_current_recipient()
    if recipient_type:
        mark_all_read(recipient_type, recipient_id)
        return jsonify({"success": True})
    return jsonify({"success": False}), 400
