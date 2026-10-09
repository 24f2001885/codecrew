from flask import Blueprint, request, jsonify, render_template
from app.services.search import search_groups, search_members

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/groups", methods=["GET"], endpoint="groups")
def get_groups():
    q = request.args.get("q", "")
    tag = request.args.get("tag", "")
    page_arg = request.args.get("page", 1)

    try:
        page = int(page_arg)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    result = search_groups(q=q, tag=tag, page=page)

    items = []
    for g in result["items"]:
        items.append({
            "slug": g.slug,
            "name": g.name,
            "tagline": g.tagline or "",
            "logo_path": g.logo_path,
            "cover_image_path": g.cover_image_path,
            "tech_tags": g.tech_tags or [],
            "featured": bool(g.featured),
            "member_count": g.members.count() if hasattr(g.members, "count") else len(g.members or []),
            "project_count": g.projects.count() if hasattr(g.projects, "count") else len(g.projects or []),
        })

    html = render_template("partials/_group_cards.html", groups=result["items"])

    return jsonify({
        "items": items,
        "page": result["page"],
        "total_pages": result["total_pages"],
        "total_count": result["total_count"],
        "html": html,
    })


@api_bp.route("/members", methods=["GET"], endpoint="members")
def get_members():
    q = request.args.get("q", "")
    group = request.args.get("group", "")
    skill = request.args.get("skill", "")
    page_arg = request.args.get("page", 1)

    try:
        page = int(page_arg)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    result = search_members(q=q, group_slug=group, skill=skill, page=page)

    items = []
    for m in result["items"]:
        # Projects credited to the member's group (per schema design)
        projects_data = []
        if m.group and hasattr(m.group, "projects"):
            for p in m.group.projects:
                projects_data.append({"title": p.title, "slug": p.slug})

        items.append({
            "id": m.id,
            "name": m.name,
            "role": m.role or "",
            "photo_path": m.photo_path,
            "bio": m.bio or "",
            "skill_tags": m.skill_tags or [],
            "github_url": m.github_url or "",
            "linkedin_url": m.linkedin_url or "",
            "twitter_url": m.twitter_url or "",
            "has_resume": bool(m.resume_pdf_path),
            "resume_pdf": m.resume_pdf_path,
            "group_name": m.group.name if m.group else "",
            "group_slug": m.group.slug if m.group else "",
            "projects": projects_data,
        })

    html = render_template("partials/_member_cards.html", members=result["items"])

    return jsonify({
        "items": items,
        "page": result["page"],
        "total_pages": result["total_pages"],
        "total_count": result["total_count"],
        "html": html,
    })
