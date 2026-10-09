import math
from sqlalchemy import or_, func
from app.extensions import db
from app.models.group import Group
from app.models.member import Member


def escape_like(val: str) -> str:
    """Escapes LIKE/ILIKE wildcards (%, _, \\) in user query strings."""
    if not val:
        return ""
    return val.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def build_filtered_query(model, query_str=None, tag=None, extra_filters=None):
    """
    Builds a filtered query or list for Group or Member models.
    Supports free-text search, tag filtering (with Postgres dialect check vs SQLite Python filter),
    and extra filters such as group_slug.
    """
    query = model.query

    # 1. Free text filtering
    if query_str and query_str.strip():
        term = escape_like(query_str.strip())
        pattern = f"%{term}%"
        if model == Group:
            query = query.filter(
                or_(
                    Group.name.ilike(pattern, escape="\\"),
                    Group.tagline.ilike(pattern, escape="\\"),
                )
            )
        elif model == Member:
            query = query.filter(
                or_(
                    Member.name.ilike(pattern, escape="\\"),
                    Member.role.ilike(pattern, escape="\\"),
                )
            )

    # 2. Extra filters (e.g. group_slug, group_id)
    if extra_filters:
        if "group_slug" in extra_filters and extra_filters["group_slug"]:
            query = query.join(Group).filter(Group.slug == extra_filters["group_slug"])
        if "group_id" in extra_filters and extra_filters["group_id"]:
            query = query.filter(model.group_id == extra_filters["group_id"])

    # 3. Stable ordering
    if model == Group:
        query = query.order_by(Group.name.asc())
    elif model == Member:
        query = query.order_by(Member.name.asc())

    # 4. Tag filtering
    if tag and tag.strip():
        cleaned_tag = tag.strip().lower()
        dialect_name = getattr(db.engine, "dialect", None)
        dialect_str = dialect_name.name if dialect_name else "sqlite"

        if dialect_str == "postgresql":
            tag_col = Group.tech_tags if model == Group else Member.skill_tags
            # Lowercased text cast containment
            query = query.filter(func.lower(tag_col.cast(db.Text)).like(f'%"{cleaned_tag}"%'))
            return query
        else:
            # SQLite / other: bounded candidate rows filtered in Python
            candidates = query.limit(2000).all()

            def _match_tag(item):
                tag_list = item.tech_tags if model == Group else item.skill_tags
                if not tag_list or not isinstance(tag_list, list):
                    return False
                return any(str(t).strip().lower() == cleaned_tag for t in tag_list)

            return [item for item in candidates if _match_tag(item)]

    return query


def paginate(query_or_list, page=1, per_page=12):
    """
    Paginates either a SQLAlchemy query or a Python list.
    Returns: {"items": [...], "page": page, "total_pages": n, "total_count": c}
    """
    try:
        page = int(page)
    except (ValueError, TypeError):
        page = 1
    page = max(1, page)

    if isinstance(query_or_list, list):
        total_count = len(query_or_list)
        total_pages = max(1, math.ceil(total_count / per_page))
        if page > total_pages:
            items = []
        else:
            start = (page - 1) * per_page
            end = start + per_page
            items = query_or_list[start:end]
    else:
        total_count = query_or_list.count()
        total_pages = max(1, math.ceil(total_count / per_page))
        if page > total_pages:
            items = []
        else:
            items = query_or_list.offset((page - 1) * per_page).limit(per_page).all()

    return {
        "items": items,
        "page": page,
        "total_pages": total_pages,
        "total_count": total_count,
    }


def search_groups(q=None, tag=None, page=1):
    """Public helper for group searching and pagination."""
    query_or_list = build_filtered_query(Group, query_str=q, tag=tag)
    return paginate(query_or_list, page=page, per_page=12)


def search_members(q=None, group_slug=None, skill=None, page=1):
    """Public helper for member searching and pagination."""
    extra = {"group_slug": group_slug} if group_slug else None
    query_or_list = build_filtered_query(Member, query_str=q, tag=skill, extra_filters=extra)
    return paginate(query_or_list, page=page, per_page=12)
