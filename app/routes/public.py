import math
from datetime import datetime
from flask import Blueprint, render_template, request, abort
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.models.blog_post import BlogPost
from app.forms.contact_forms import ContactForm
from app.services.search import search_groups, search_members

public_bp = Blueprint("public", __name__)


class SearchPagination:
    """Helper class providing pagination interface matching Jinja templates."""
    def __init__(self, items, page, total_pages, total_count):
        self.items = items
        self.page = page
        self.pages = total_pages
        self.total = total_count
        self.has_prev = page > 1
        self.prev_num = page - 1
        self.has_next = page < total_pages
        self.next_num = page + 1

    def iter_pages(self, left_edge=2, left_current=2, right_current=2, right_edge=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (
                num <= left_edge
                or (self.page - left_current <= num <= self.page + right_current)
                or num > self.pages - right_edge
            ):
                if last + 1 != num:
                    yield None
                yield num
                last = num


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

    from app.services.site_context import platform_stats
    stats = platform_stats()

    return render_template(
        "public/home.html",
        featured_groups=featured_groups,
        teaser_groups=teaser_groups,
        stats=stats,
    )



@public_bp.route("/groups")
def groups():
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
    pagination = SearchPagination(
        items=result["items"],
        page=result["page"],
        total_pages=result["total_pages"],
        total_count=result["total_count"],
    )

    return render_template(
        "public/groups_directory.html",
        pagination=pagination,
        total_count=result["total_count"],
        q=q,
        tag=tag,
    )


@public_bp.route("/members", endpoint="members")
def members():
    q = request.args.get("q", "")
    group_slug = request.args.get("group", "")
    skill = request.args.get("skill", "")
    page_arg = request.args.get("page", 1)

    try:
        page = int(page_arg)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    result = search_members(q=q, group_slug=group_slug, skill=skill, page=page)
    pagination = SearchPagination(
        items=result["items"],
        page=result["page"],
        total_pages=result["total_pages"],
        total_count=result["total_count"],
    )

    all_groups = Group.query.order_by(Group.name.asc()).all()

    return render_template(
        "public/members_directory.html",
        pagination=pagination,
        members=result["items"],
        total_count=result["total_count"],
        all_groups=all_groups,
        q=q,
        group_slug=group_slug,
        skill=skill,
    )


@public_bp.route("/group/<slug>")
def group_detail(slug):
    group = Group.query.filter_by(slug=slug).first_or_404()

    members_list = group.members.order_by(Member.display_order.asc()).all()
    projects_list = group.projects.order_by(Project.featured.desc(), Project.created_at.desc()).all()

    now = datetime.utcnow()
    blog_posts = (
        group.blog_posts.filter(
            BlogPost.published_at.is_not(None),
            BlogPost.published_at <= now,
        )
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )

    current_year = now.year
    years_active = max(1, current_year - group.founded_year) if group.founded_year else 1

    stats = {
        "completed_projects": len(projects_list),
        "members": len(members_list),
        "years_active": years_active,
        "total_projects": len(projects_list),
    }

    form = ContactForm()
    return render_template(
        "public/group_detail.html",
        group=group,
        members=members_list,
        projects=projects_list,
        blog_posts=blog_posts,
        stats=stats,
        form=form,
    )
