import math
from datetime import datetime
from flask import Blueprint, render_template, request, abort, Response
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.models.blog_post import BlogPost
from app.forms.contact_forms import ContactForm
from app.services.search import search_groups, search_members, search_projects, search_blog_posts

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
@public_bp.route("/index.html")
@public_bp.route("/index")
def index():
    if request.path in ("/index.html", "/index"):
        from flask import redirect, url_for
        return redirect(url_for("public.index"), code=301)

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

    # Top & featured projects across all engineering collectives
    featured_projects = (
        Project.query.filter_by(featured=True)
        .order_by(Project.created_at.desc())
        .limit(6)
        .all()
    )
    if not featured_projects:
        featured_projects = (
            Project.query.order_by(Project.created_at.desc())
            .limit(6)
            .all()
        )

    # Latest engineering insights and blog posts
    now = datetime.utcnow()
    latest_posts = (
        BlogPost.query.filter(
            BlogPost.published_at.is_not(None),
            BlogPost.published_at <= now,
        )
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )

    from app.services.site_context import platform_stats
    stats = platform_stats()

    return render_template(
        "public/home.html",
        featured_groups=featured_groups,
        teaser_groups=teaser_groups,
        featured_projects=featured_projects,
        latest_posts=latest_posts,
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
        .all()
    )

    current_year = now.year
    years_active = max(1, current_year - group.founded_year) if group.founded_year else 1

    stats = {
        "completed_projects": sum(1 for p in projects_list if getattr(p, 'status', None) == 'completed') if any(getattr(p, 'status', None) == 'completed' for p in projects_list) else len(projects_list),
        "members": len(members_list),
        "years_active": years_active,
        "total_projects": len(projects_list),
        "total_posts": len(blog_posts),
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


@public_bp.route("/projects", endpoint="projects")
def projects():
    q = request.args.get("q", "")
    group_slug = request.args.get("group", "")
    tag = request.args.get("tag", "")
    page_arg = request.args.get("page", 1)

    try:
        page = int(page_arg)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    result = search_projects(q=q, group_slug=group_slug, tag=tag, page=page, per_page=12)
    pagination = SearchPagination(
        items=result["items"],
        page=result["page"],
        total_pages=result["total_pages"],
        total_count=result["total_count"],
    )

    all_groups = Group.query.order_by(Group.name.asc()).all()

    return render_template(
        "public/projects_directory.html",
        pagination=pagination,
        projects=result["items"],
        total_count=result["total_count"],
        all_groups=all_groups,
        q=q,
        group_slug=group_slug,
        tag=tag,
    )


@public_bp.route("/blogs")
@public_bp.route("/blog", endpoint="blog")
def blog():
    q = request.args.get("q", "")
    group_slug = request.args.get("group", "")
    tag = request.args.get("tag", "")
    page_arg = request.args.get("page", 1)

    try:
        page = int(page_arg)
        if page < 1:
            page = 1
    except (ValueError, TypeError):
        page = 1

    result = search_blog_posts(q=q, group_slug=group_slug, tag=tag, page=page, per_page=9)
    pagination = SearchPagination(
        items=result["items"],
        page=result["page"],
        total_pages=result["total_pages"],
        total_count=result["total_count"],
    )

    all_groups = Group.query.order_by(Group.name.asc()).all()

    return render_template(
        "public/blog_directory.html",
        pagination=pagination,
        posts=result["items"],
        total_count=result["total_count"],
        all_groups=all_groups,
        q=q,
        group_slug=group_slug,
        tag=tag,
    )


@public_bp.route("/group/<group_slug>/blog/<slug>")
@public_bp.route("/blog/<slug>", endpoint="blog_detail")
def blog_detail(slug, group_slug=None):
    now = datetime.utcnow()
    query = BlogPost.query.filter(
        BlogPost.slug == slug,
        BlogPost.published_at.is_not(None),
        BlogPost.published_at <= now,
    )
    if group_slug:
        query = query.join(Group).filter(Group.slug == group_slug)
    post = query.first_or_404()

    # Related articles
    related_posts = (
        BlogPost.query.filter(
            BlogPost.id != post.id,
            BlogPost.published_at.is_not(None),
            BlogPost.published_at <= now,
        )
        .order_by(BlogPost.published_at.desc())
        .limit(3)
        .all()
    )

    return render_template(
        "public/blog_detail.html",
        post=post,
        related_posts=related_posts,
    )


@public_bp.route("/sitemap.xml")
def sitemap():
    base = request.host_url.rstrip("/")
    now = datetime.utcnow()
    pages = [
        {"loc": f"{base}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{base}/groups", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{base}/members", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{base}/projects", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{base}/blog", "priority": "0.85", "changefreq": "daily"},
        {"loc": f"{base}/request-project", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{base}/join", "priority": "0.8", "changefreq": "weekly"},
    ]
    for g in Group.query.all():
        pages.append({
            "loc": f"{base}/group/{g.slug}",
            "priority": "0.85",
            "changefreq": "weekly"
        })
    for p in BlogPost.query.filter(BlogPost.published_at.is_not(None), BlogPost.published_at <= now).all():
        pages.append({
            "loc": f"{base}/blog/{p.slug}",
            "priority": "0.75",
            "changefreq": "monthly"
        })
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        xml.append('  <url>')
        xml.append(f'    <loc>{p["loc"]}</loc>')
        xml.append(f'    <changefreq>{p["changefreq"]}</changefreq>')
        xml.append(f'    <priority>{p["priority"]}</priority>')
        xml.append('  </url>')
    xml.append('</urlset>')
    return Response("\n".join(xml), mimetype="application/xml")


@public_bp.route("/robots.txt")
def robots():
    base = request.host_url.rstrip("/")
    content = f"""User-agent: *
Allow: /
Disallow: /admin/
Disallow: /coder/

Sitemap: {base}/sitemap.xml
"""
    return Response(content, mimetype="text/plain")

