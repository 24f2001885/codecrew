from datetime import datetime
from flask import Blueprint, render_template, request, abort
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project

public_bp = Blueprint("public", __name__)


@public_bp.route("/")
def index():
    featured_groups = (
        Group.query.filter_by(featured=True)
        .order_by(Group.created_at.desc())
        .limit(6)
        .all()
    )
    teaser_groups = (
        Group.query.order_by(Group.name.asc())
        .limit(6)
        .all()
    )

    # Count platform stats (SiteSettings.stats_override is honored in P6)
    stats = {
        "groups": Group.query.count(),
        "members": Member.query.count(),
        "projects": Project.query.count(),
    }

    return render_template(
        "public/home.html",
        featured_groups=featured_groups,
        teaser_groups=teaser_groups,
        stats=stats,
    )


@public_bp.route("/groups")
def groups():
    page = request.args.get("page", 1, type=int)
    if page < 1:
        page = 1

    # Paginate groups (q/tag filter arrives in P5)
    pagination = (
        Group.query.order_by(Group.name.asc())
        .paginate(page=page, per_page=12, error_out=False)
    )

    return render_template("public/groups_directory.html", pagination=pagination)


@public_bp.route("/group/<slug>")
def group_detail(slug):
    group = Group.query.filter_by(slug=slug).first_or_404()

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

    return render_template(
        "public/group_detail.html",
        group=group,
        members=members,
        projects=projects,
        stats=stats,
    )
