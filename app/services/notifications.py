import logging
from datetime import datetime, timezone
from app.extensions import db
from app.models.app_notification import AppNotification

logger = logging.getLogger(__name__)


def create_notification(recipient_type, recipient_id, title, message, link_url=None, category="system"):
    """
    Creates and persists an in-app notification.
    recipient_type: 'coder', 'admin', 'client'
    recipient_id: string ID (coder.id, admin.id, or project_request.id)
    """
    try:
        notif = AppNotification(
            recipient_type=recipient_type,
            recipient_id=str(recipient_id) if recipient_id else None,
            title=title[:150],
            message=message,
            link_url=link_url,
            category=category,
            is_read=False,
        )
        db.session.add(notif)
        db.session.commit()
        return notif
    except Exception as e:
        logger.error(f"Failed to create notification: {e}")
        db.session.rollback()
        return None


def get_unread_notifications(recipient_type, recipient_id=None, limit=20):
    query = AppNotification.query.filter_by(recipient_type=recipient_type, is_read=False)
    if recipient_id:
        query = query.filter_by(recipient_id=str(recipient_id))
    return query.order_by(AppNotification.created_at.desc()).limit(limit).all()


def get_recent_notifications(recipient_type, recipient_id=None, limit=10):
    query = AppNotification.query.filter_by(recipient_type=recipient_type)
    if recipient_id:
        query = query.filter_by(recipient_id=str(recipient_id))
    return query.order_by(AppNotification.created_at.desc()).limit(limit).all()


def get_unread_count(recipient_type, recipient_id=None):
    query = AppNotification.query.filter_by(recipient_type=recipient_type, is_read=False)
    if recipient_id:
        query = query.filter_by(recipient_id=str(recipient_id))
    return query.count()


def mark_notification_read(notification_id):
    notif = db.session.get(AppNotification, notification_id)
    if notif:
        notif.is_read = True
        db.session.commit()
        return True
    return False


def mark_all_read(recipient_type, recipient_id=None):
    query = AppNotification.query.filter_by(recipient_type=recipient_type, is_read=False)
    if recipient_id:
        query = query.filter_by(recipient_id=str(recipient_id))
    query.update({"is_read": True})
    db.session.commit()
    return True
