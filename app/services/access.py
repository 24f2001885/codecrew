from datetime import datetime, timezone
from flask import abort
from sqlalchemy import or_
from app.extensions import db
from app.models.request_access_grant import RequestAccessGrant
from app.models.project_request import ProjectRequest
from app.models.coder_user import CoderUser


def active_grants_query(coder_id):
    """
    Returns query for active, non-revoked, non-expired grants for an active coder.
    """
    now = datetime.now(timezone.utc)
    return (
        RequestAccessGrant.query
        .join(CoderUser, RequestAccessGrant.coder_id == CoderUser.id)
        .filter(
            RequestAccessGrant.coder_id == coder_id,
            RequestAccessGrant.revoked_at.is_(None),
            or_(
                RequestAccessGrant.expires_at.is_(None),
                RequestAccessGrant.expires_at > now,
            ),
            CoderUser.status == "active",
        )
    )


def granted_requests_for(coder, page=1, per_page=15):
    """
    Returns paginated (request, grant) pairs for an active coder.
    """
    if getattr(coder, "status", None) != "active":
        return None

    query = (
        db.session.query(ProjectRequest, RequestAccessGrant)
        .join(RequestAccessGrant, ProjectRequest.id == RequestAccessGrant.request_id)
        .join(CoderUser, RequestAccessGrant.coder_id == CoderUser.id)
        .filter(
            RequestAccessGrant.coder_id == coder.id,
            RequestAccessGrant.revoked_at.is_(None),
            or_(
                RequestAccessGrant.expires_at.is_(None),
                RequestAccessGrant.expires_at > datetime.now(timezone.utc),
            ),
            CoderUser.status == "active",
        )
        .order_by(RequestAccessGrant.created_at.desc())
    )
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_granted_request_or_404(coder, request_id):
    """
    Returns (ProjectRequest, RequestAccessGrant) or aborts 404 (never 403, preventing probing).
    """
    if not coder or getattr(coder, "status", None) != "active":
        abort(404)

    now = datetime.now(timezone.utc)
    result = (
        db.session.query(ProjectRequest, RequestAccessGrant)
        .join(RequestAccessGrant, ProjectRequest.id == RequestAccessGrant.request_id)
        .join(CoderUser, RequestAccessGrant.coder_id == CoderUser.id)
        .filter(
            ProjectRequest.id == request_id,
            RequestAccessGrant.coder_id == coder.id,
            RequestAccessGrant.revoked_at.is_(None),
            or_(
                RequestAccessGrant.expires_at.is_(None),
                RequestAccessGrant.expires_at > now,
            ),
            CoderUser.status == "active",
        )
        .first()
    )

    if not result:
        abort(404)

    return result


def serialize_request_for_coder(request_obj, grant_obj):
    """
    Allow-list dictionary serializer for coder views.
    Ensures internal_notes and ungranted contact details are never exposed.
    """
    data = {
        "id": request_obj.id,
        "project_type": request_obj.project_type,
        "budget_range": request_obj.budget_range,
        "timeline": request_obj.timeline,
        "description": request_obj.description,
        "domain_tags": request_obj.domain_tags or [],
        "has_attachment": bool(request_obj.attachment_path),
        "created_at": request_obj.created_at,
        "scope": grant_obj.scope,
        "grant_id": grant_obj.id,
        "grant_created_at": grant_obj.created_at,
        "grant_expires_at": grant_obj.expires_at,
    }

    if grant_obj.scope == "brief_and_contact":
        data["name"] = request_obj.name
        data["email"] = request_obj.email
        data["company"] = request_obj.company
    else:
        data["name"] = None
        data["email"] = None
        data["company"] = None

    return data
