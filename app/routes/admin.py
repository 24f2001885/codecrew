import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.models.contact_message import ContactMessage
from app.models.project_request import ProjectRequest
from app.models.blog_post import BlogPost
from app.models.site_settings import SiteSettings
from app.forms.group_forms import GroupForm
from app.forms.member_forms import MemberForm
from app.forms.project_forms import ProjectForm
from app.forms.blog_forms import BlogPostForm
from app.forms.settings_forms import SettingsForm
from app.security.decorators import super_admin_required, apply_guard_to_blueprint
from app.services.slugs import unique_slug
from app.services.uploads import save_upload, delete_upload, replace_upload, UploadError
from app.services.private_files import send_private, delete_private

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Protect all current and future routes in admin_bp with super_admin_required
apply_guard_to_blueprint(admin_bp, super_admin_required)


@admin_bp.route("/dashboard")
def dashboard():
    group_count = Group.query.count()
    member_count = Member.query.count()
    project_count = Project.query.count()
    unread_messages_count = ContactMessage.query.filter_by(is_read=False).count()
    new_requests_count = ProjectRequest.query.filter_by(status="new").count()
    draft_posts_count = BlogPost.query.filter(BlogPost.published_at.is_(None)).count()
    published_posts_count = BlogPost.query.filter(BlogPost.published_at.is_not(None)).count()
    return render_template(
        "admin/dashboard.html",
        group_count=group_count,
        member_count=member_count,
        project_count=project_count,
        unread_messages_count=unread_messages_count,
        new_requests_count=new_requests_count,
        draft_posts_count=draft_posts_count,
        published_posts_count=published_posts_count,
    )


# -----------------------------------------------------------------------------
# Groups CRUD
# -----------------------------------------------------------------------------
@admin_bp.route("/groups")
def groups():
    page = request.args.get("page", 1, type=int)
    pick = request.args.get("pick")  # 'members' or 'projects'
    pagination = Group.query.order_by(Group.name.asc()).paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/groups_list.html", pagination=pagination, pick=pick)


@admin_bp.route("/groups/new", methods=["GET", "POST"])
def group_create():
    form = GroupForm()
    if form.validate_on_submit():
        try:
            slug = unique_slug(Group, form.name.data)
            logo_path = save_upload(form.logo.data, "logos", "image") if form.logo.data else None
            cover_path = save_upload(form.cover_image.data, "covers", "image") if form.cover_image.data else None

            group = Group(
                name=form.name.data.strip(),
                slug=slug,
                tagline=form.tagline.data.strip() if form.tagline.data else None,
                description=form.description.data.strip() if form.description.data else None,
                founded_year=form.founded_year.data,
                tech_tags=form.parse_tags(),
                featured=form.featured.data,
                logo=logo_path,
                cover_image=cover_path,
            )
            db.session.add(group)
            db.session.commit()
            flash(f"Group '{group.name}' created successfully.", "success")
            return redirect(url_for("admin.groups"))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create group: {e}", "danger")

    return render_template("admin/group_form.html", form=form, title="New Group")


@admin_bp.route("/groups/<id>/edit", methods=["GET", "POST"])
def group_edit(id):
    group = db.session.get(Group, id) or abort(404)
    form = GroupForm(obj=group)

    if request.method == "GET":
        if group.tech_tags:
            form.tech_tags.data = ", ".join(group.tech_tags)

    if form.validate_on_submit():
        try:
            group.name = form.name.data.strip()
            # Slug update
            group.slug = unique_slug(Group, form.name.data, exclude_id=group.id)
            group.tagline = form.tagline.data.strip() if form.tagline.data else None
            group.description = form.description.data.strip() if form.description.data else None
            group.founded_year = form.founded_year.data
            group.tech_tags = form.parse_tags()
            group.featured = form.featured.data

            if form.logo.data and hasattr(form.logo.data, "filename") and form.logo.data.filename:
                group.logo = replace_upload(group.logo, form.logo.data, "logos", "image")
            if form.cover_image.data and hasattr(form.cover_image.data, "filename") and form.cover_image.data.filename:
                group.cover_image = replace_upload(group.cover_image, form.cover_image.data, "covers", "image")

            group.updated_at = datetime.utcnow()
            db.session.commit()
            flash(f"Group '{group.name}' updated successfully.", "success")
            return redirect(url_for("admin.groups"))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update group: {e}", "danger")

    return render_template("admin/group_form.html", form=form, group=group, title=f"Edit {group.name}")


@admin_bp.route("/groups/<id>/delete", methods=["POST"])
def group_delete(id):
    group = db.session.get(Group, id) or abort(404)
    group_name = group.name

    try:
        # Best effort cleanup of images
        if group.logo:
            delete_upload(group.logo)
        if group.cover_image:
            delete_upload(group.cover_image)

        db.session.delete(group)
        db.session.commit()
        flash(f"Group '{group_name}' and all associated members and projects have been deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete group: {e}", "danger")

    return redirect(url_for("admin.groups"))


# -----------------------------------------------------------------------------
# Members CRUD (Scoped to Group)
# -----------------------------------------------------------------------------
@admin_bp.route("/groups/<id>/members")
def group_members(id):
    group = db.session.get(Group, id) or abort(404)
    members = group.members.order_by(Member.display_order.asc()).all()
    return render_template("admin/members_list.html", group=group, members=members)


@admin_bp.route("/groups/<id>/members/new", methods=["GET", "POST"])
def member_create(id):
    group = db.session.get(Group, id) or abort(404)
    form = MemberForm()

    if form.validate_on_submit():
        try:
            photo_path = save_upload(form.photo.data, "photos", "image") if form.photo.data else None
            resume_path = save_upload(form.resume_pdf.data, "resumes", "pdf") if form.resume_pdf.data else None

            member = Member(
                group_id=group.id,
                name=form.name.data.strip(),
                role=form.role.data.strip() if form.role.data else None,
                bio=form.bio.data.strip() if form.bio.data else None,
                skill_tags=form.parse_tags(),
                github_url=form.github_url.data.strip() if form.github_url.data else None,
                linkedin_url=form.linkedin_url.data.strip() if form.linkedin_url.data else None,
                twitter_url=form.twitter_url.data.strip() if form.twitter_url.data else None,
                display_order=form.display_order.data or 0,
                photo=photo_path,
                resume_pdf=resume_path,
            )
            db.session.add(member)
            db.session.commit()
            flash(f"Member '{member.name}' added to {group.name}.", "success")
            return redirect(url_for("admin.group_members", id=group.id))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to add member: {e}", "danger")

    return render_template("admin/member_form.html", form=form, group=group, title=f"Add Member to {group.name}")


@admin_bp.route("/groups/<id>/members/<member_id>/edit", methods=["GET", "POST"])
def member_edit(id, member_id):
    group = db.session.get(Group, id) or abort(404)
    member = db.session.get(Member, member_id) or abort(404)
    if member.group_id != group.id:
        abort(404)

    form = MemberForm(obj=member)
    if request.method == "GET" and member.skill_tags:
        form.skill_tags.data = ", ".join(member.skill_tags)

    if form.validate_on_submit():
        try:
            member.name = form.name.data.strip()
            member.role = form.role.data.strip() if form.role.data else None
            member.bio = form.bio.data.strip() if form.bio.data else None
            member.skill_tags = form.parse_tags()
            member.github_url = form.github_url.data.strip() if form.github_url.data else None
            member.linkedin_url = form.linkedin_url.data.strip() if form.linkedin_url.data else None
            member.twitter_url = form.twitter_url.data.strip() if form.twitter_url.data else None
            member.display_order = form.display_order.data or 0

            # Remove checkboxes
            if form.remove_photo.data and member.photo:
                delete_upload(member.photo)
                member.photo = None
            elif form.photo.data and hasattr(form.photo.data, "filename") and form.photo.data.filename:
                member.photo = replace_upload(member.photo, form.photo.data, "photos", "image")

            if form.remove_resume.data and member.resume_pdf:
                delete_upload(member.resume_pdf)
                member.resume_pdf = None
            elif form.resume_pdf.data and hasattr(form.resume_pdf.data, "filename") and form.resume_pdf.data.filename:
                member.resume_pdf = replace_upload(member.resume_pdf, form.resume_pdf.data, "resumes", "pdf")

            db.session.commit()
            flash(f"Member '{member.name}' updated successfully.", "success")
            return redirect(url_for("admin.group_members", id=group.id))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update member: {e}", "danger")

    return render_template("admin/member_form.html", form=form, group=group, member=member, title=f"Edit {member.name}")


@admin_bp.route("/groups/<id>/members/<member_id>/delete", methods=["POST"])
def member_delete(id, member_id):
    group = db.session.get(Group, id) or abort(404)
    member = db.session.get(Member, member_id) or abort(404)
    if member.group_id != group.id:
        abort(404)

    member_name = member.name
    try:
        if member.photo:
            delete_upload(member.photo)
        if member.resume_pdf:
            delete_upload(member.resume_pdf)

        db.session.delete(member)
        db.session.commit()
        flash(f"Member '{member_name}' deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete member: {e}", "danger")

    return redirect(url_for("admin.group_members", id=group.id))


# -----------------------------------------------------------------------------
# Projects CRUD (Scoped to Group)
# -----------------------------------------------------------------------------
@admin_bp.route("/groups/<id>/projects")
def group_projects(id):
    group = db.session.get(Group, id) or abort(404)
    projects = group.projects.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects_list.html", group=group, projects=projects)


@admin_bp.route("/groups/<id>/projects/new", methods=["GET", "POST"])
def project_create(id):
    group = db.session.get(Group, id) or abort(404)
    form = ProjectForm()

    if form.validate_on_submit():
        try:
            slug = unique_slug(Project, form.title.data, scope={"group_id": group.id})
            
            # Handle gallery/screenshot uploads
            files = [f for f in (form.gallery_files.data or []) if getattr(f, "filename", None)]
            alts = [line.strip() for line in (form.gallery_alts.data or "").splitlines() if line.strip()]
            gallery = []
            for idx, file in enumerate(files):
                img_path = save_upload(file, "screenshots", "image")
                alt_text = alts[idx] if idx < len(alts) else form.title.data.strip()
                gallery.append({"path": img_path, "alt": alt_text})

            screenshot_path = gallery[0]["path"] if gallery else None
            live_url_val = form.live_url.data.strip() if form.live_url.data else None

            project = Project(
                group_id=group.id,
                title=form.title.data.strip(),
                slug=slug,
                summary=form.summary.data.strip() if form.summary.data else None,
                description=form.description.data.strip() if form.description.data else None,
                status=form.status.data,
                tech_tags=form.parse_tags(),
                github_url=form.github_url.data.strip() if form.github_url.data else None,
                live_url=live_url_val,
                demo_url=live_url_val,
                featured=form.featured.data,
                screenshot=screenshot_path,
                gallery_images=gallery,
            )
            db.session.add(project)
            db.session.commit()
            flash(f"Project '{project.title}' added to {group.name}.", "success")
            return redirect(url_for("admin.group_projects", id=group.id))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to create project: {e}", "danger")

    return render_template("admin/project_form.html", form=form, group=group, title=f"New Project for {group.name}")


@admin_bp.route("/groups/<id>/projects/<project_id>/edit", methods=["GET", "POST"])
def project_edit(id, project_id):
    group = db.session.get(Group, id) or abort(404)
    project = db.session.get(Project, project_id) or abort(404)
    if project.group_id != group.id:
        abort(404)

    form = ProjectForm(obj=project)
    if request.method == "GET":
        if project.tech_tags:
            form.tech_tags.data = ", ".join(project.tech_tags)
        if project.live_url or project.demo_url:
            form.live_url.data = project.live_url or project.demo_url
        if project.status:
            form.status.data = project.status

    if form.validate_on_submit():
        try:
            project.title = form.title.data.strip()
            project.slug = unique_slug(Project, form.title.data, scope={"group_id": group.id}, exclude_id=project.id)
            project.summary = form.summary.data.strip() if form.summary.data else None
            project.description = form.description.data.strip() if form.description.data else None
            project.status = form.status.data
            project.tech_tags = form.parse_tags()
            project.github_url = form.github_url.data.strip() if form.github_url.data else None
            live_url_val = form.live_url.data.strip() if form.live_url.data else None
            project.live_url = live_url_val
            project.demo_url = live_url_val
            project.featured = form.featured.data

            # Check remove_image list
            remove_images = set(request.form.getlist("remove_image"))
            curr_gallery = []
            for item in (project.gallery_images or []):
                if isinstance(item, dict):
                    if item.get("path") in remove_images:
                        delete_upload(item.get("path"))
                    else:
                        curr_gallery.append(item)

            # Handle new gallery uploads
            files = [f for f in (form.gallery_files.data or []) if getattr(f, "filename", None)]
            alts = [line.strip() for line in (form.gallery_alts.data or "").splitlines() if line.strip()]
            for idx, file in enumerate(files):
                img_path = save_upload(file, "screenshots", "image")
                alt_text = alts[idx] if idx < len(alts) else project.title
                curr_gallery.append({"path": img_path, "alt": alt_text})

            project.gallery_images = curr_gallery
            project.screenshot = curr_gallery[0]["path"] if curr_gallery else None

            db.session.commit()
            flash(f"Project '{project.title}' updated successfully.", "success")
            return redirect(url_for("admin.group_projects", id=group.id))
        except UploadError as ue:
            db.session.rollback()
            flash(str(ue), "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update project: {e}", "danger")

    return render_template("admin/project_form.html", form=form, group=group, project=project, title=f"Edit {project.title}")


@admin_bp.route("/groups/<id>/projects/<project_id>/delete", methods=["POST"])
def project_delete(id, project_id):
    group = db.session.get(Group, id) or abort(404)
    project = db.session.get(Project, project_id) or abort(404)
    if project.group_id != group.id:
        abort(404)

    project_title = project.title
    try:
        for img in (project.gallery_images or []):
            if isinstance(img, dict) and img.get("path"):
                delete_upload(img["path"])
        if project.screenshot:
            delete_upload(project.screenshot)

        db.session.delete(project)
        db.session.commit()
        flash(f"Project '{project_title}' deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete project: {e}", "danger")

    return redirect(url_for("admin.group_projects", id=group.id))


# -----------------------------------------------------------------------------
# Messages Inbox (Contact Inquiries)
# -----------------------------------------------------------------------------
@admin_bp.route("/messages", endpoint="messages")
def messages():
    page = request.args.get("page", 1, type=int)
    unread_only = request.args.get("unread") == "1"

    query = ContactMessage.query
    if unread_only:
        query = query.filter_by(is_read=False)
    query = query.order_by(ContactMessage.created_at.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    unread_count = ContactMessage.query.filter_by(is_read=False).count()
    total_count = ContactMessage.query.count()
    return render_template(
        "admin/messages.html",
        pagination=pagination,
        unread_only=unread_only,
        unread_count=unread_count,
        total_count=total_count,
    )


@admin_bp.route("/messages/<id>/read", methods=["POST"])
def message_toggle_read(id):
    msg = db.session.get(ContactMessage, id) or abort(404)
    msg.is_read = not msg.is_read
    db.session.commit()
    status_label = "read" if msg.is_read else "unread"
    flash(f"Message marked as {status_label}.", "success")
    return redirect(url_for("admin.messages"))


@admin_bp.route("/messages/<id>/delete", methods=["POST"])
def message_delete(id):
    msg = db.session.get(ContactMessage, id) or abort(404)
    sender = msg.name
    db.session.delete(msg)
    db.session.commit()
    flash(f"Message from '{sender}' deleted.", "success")
    return redirect(url_for("admin.messages"))


# -----------------------------------------------------------------------------
# Project Requests Inbox
# -----------------------------------------------------------------------------
VALID_REQUEST_STATUSES = ["new", "in_review", "contacted", "closed"]


@admin_bp.route("/project-requests", endpoint="project_requests")
def project_requests():
    page = request.args.get("page", 1, type=int)
    status_filter = request.args.get("status")

    query = ProjectRequest.query
    if status_filter in VALID_REQUEST_STATUSES:
        query = query.filter_by(status=status_filter)
    query = query.order_by(ProjectRequest.created_at.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    groups = Group.query.order_by(Group.name.asc()).all()

    counts = {
        "all": ProjectRequest.query.count(),
        "new": ProjectRequest.query.filter_by(status="new").count(),
        "in_review": ProjectRequest.query.filter_by(status="in_review").count(),
        "contacted": ProjectRequest.query.filter_by(status="contacted").count(),
        "closed": ProjectRequest.query.filter_by(status="closed").count(),
    }

    return render_template(
        "admin/project_requests.html",
        pagination=pagination,
        status_filter=status_filter,
        groups=groups,
        counts=counts,
    )


@admin_bp.route("/project-requests/<id>/status", methods=["POST"])
def project_request_status(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    new_status = request.form.get("status", "").strip().lower()

    if new_status not in VALID_REQUEST_STATUSES:
        flash(f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_REQUEST_STATUSES)}", "danger")
        return redirect(url_for("admin.project_requests"))

    req_item.status = new_status
    db.session.commit()
    flash(f"Status for request from '{req_item.name}' updated to '{new_status}'.", "success")
    return redirect(url_for("admin.project_requests"))


@admin_bp.route("/project-requests/<id>/assign", methods=["POST"])
def project_request_assign(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    assigned_group_id = request.form.get("assigned_group_id", "").strip()

    if not assigned_group_id:
        req_item.assigned_group_id = None
        db.session.commit()
        flash(f"Unassigned group from request '{req_item.name}'.", "success")
        return redirect(url_for("admin.project_requests"))

    group = db.session.get(Group, assigned_group_id)
    if not group:
        flash("Group not found.", "danger")
        return redirect(url_for("admin.project_requests"))

    req_item.assigned_group_id = group.id
    db.session.commit()
    flash(f"Assigned request from '{req_item.name}' to group '{group.name}'.", "success")
    return redirect(url_for("admin.project_requests"))


@admin_bp.route("/project-requests/<id>/delete", methods=["POST"])
def project_request_delete(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    name = req_item.name
    try:
        if req_item.attachment_path:
            delete_private("requests", req_item.attachment_path)

        db.session.delete(req_item)
        db.session.commit()
        flash(f"Project request from '{name}' deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete request: {e}", "danger")

    return redirect(url_for("admin.project_requests"))


@admin_bp.route("/project-requests/<id>/attachment")
def project_request_attachment(id):
    req_item = db.session.get(ProjectRequest, id) or abort(404)
    if not req_item.attachment_path:
        abort(404)

    ext = os.path.splitext(req_item.attachment_path)[1]
    download_name = f"request_{req_item.id}{ext}"
    return send_private("requests", req_item.attachment_path, download_name=download_name)


# -----------------------------------------------------------------------------
# Blog CRUD
# -----------------------------------------------------------------------------
@admin_bp.route("/blog", endpoint="blog")
def blog():
    page = request.args.get("page", 1, type=int)
    group_id = request.args.get("group_id")

    query = BlogPost.query
    if group_id:
        query = query.filter_by(group_id=group_id)
    query = query.order_by(BlogPost.created_at.desc())

    pagination = query.paginate(page=page, per_page=15, error_out=False)
    groups = Group.query.order_by(Group.name.asc()).all()

    return render_template(
        "admin/blog_list.html",
        pagination=pagination,
        groups=groups,
        selected_group_id=group_id,
    )


@admin_bp.route("/blog/new", methods=["GET", "POST"], endpoint="blog_new")
def blog_new():
    form = BlogPostForm()
    groups = Group.query.order_by(Group.name.asc()).all()
    form.group_id.choices = [(g.id, g.name) for g in groups]

    if form.validate_on_submit():
        group = db.session.get(Group, form.group_id.data)
        if not group:
            flash("Selected group not found.", "danger")
            return render_template("admin/blog_form.html", form=form, post=None)

        slug = unique_slug(BlogPost, form.title.data, scope={"group_id": form.group_id.data})
        cover_image_path = None
        if form.cover_image.data:
            try:
                cover_image_path = save_upload(form.cover_image.data, subfolder="covers")
            except UploadError as e:
                flash(f"Cover image error: {e}", "danger")
                return render_template("admin/blog_form.html", form=form, post=None)

        tags = form.parse_tags()
        published_at = datetime.utcnow() if form.published.data else None

        post = BlogPost(
            group_id=form.group_id.data,
            title=form.title.data.strip(),
            slug=slug,
            content=form.content.data,
            cover_image_path=cover_image_path,
            tags=tags,
            published_at=published_at,
        )
        db.session.add(post)
        db.session.commit()
        flash(f"Blog post '{post.title}' created successfully.", "success")
        return redirect(url_for("admin.blog"))

    return render_template("admin/blog_form.html", form=form, post=None)


@admin_bp.route("/blog/<id>/edit", methods=["GET", "POST"], endpoint="blog_edit")
def blog_edit(id):
    post = db.session.get(BlogPost, id) or abort(404)
    form = BlogPostForm(obj=post)
    groups = Group.query.order_by(Group.name.asc()).all()
    form.group_id.choices = [(g.id, g.name) for g in groups]

    if request.method == "GET":
        form.group_id.data = post.group_id
        form.tags.data = ", ".join(post.tags or [])
        form.published.data = post.published_at is not None

    if form.validate_on_submit():
        if form.title.data.strip() != post.title or form.group_id.data != post.group_id:
            post.slug = unique_slug(BlogPost, form.title.data, scope={"group_id": form.group_id.data}, exclude_id=post.id)

        post.title = form.title.data.strip()
        post.group_id = form.group_id.data
        post.content = form.content.data
        post.tags = form.parse_tags()

        if form.cover_image.data:
            try:
                post.cover_image_path = replace_upload(form.cover_image.data, old_path=post.cover_image_path, subfolder="covers")
            except UploadError as e:
                flash(f"Cover image error: {e}", "danger")
                return render_template("admin/blog_form.html", form=form, post=post)

        if form.published.data:
            if not post.published_at:
                post.published_at = datetime.utcnow()
        else:
            post.published_at = None

        db.session.commit()
        flash(f"Blog post '{post.title}' updated successfully.", "success")
        return redirect(url_for("admin.blog"))

    return render_template("admin/blog_form.html", form=form, post=post)


@admin_bp.route("/blog/<id>/delete", methods=["POST"], endpoint="blog_delete")
def blog_delete(id):
    post = db.session.get(BlogPost, id) or abort(404)
    title = post.title
    try:
        if post.cover_image_path:
            delete_upload(post.cover_image_path)
        db.session.delete(post)
        db.session.commit()
        flash(f"Blog post '{title}' deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete blog post: {e}", "danger")

    return redirect(url_for("admin.blog"))


# -----------------------------------------------------------------------------
# Site Settings (P6)
# -----------------------------------------------------------------------------
@admin_bp.route("/settings", methods=["GET", "POST"], endpoint="settings")
def settings():
    settings_obj = SiteSettings.get_singleton()
    form = SettingsForm()

    if request.method == "GET":
        form.hero_headline.data = settings_obj.hero_headline
        form.hero_subheadline.data = settings_obj.hero_subheadline
        form.hero_cta_text.data = settings_obj.hero_cta_text

        # Social links
        socials = settings_obj.footer_social_links or {}
        form.github_url.data = socials.get("github")
        form.twitter_url.data = socials.get("twitter")
        form.linkedin_url.data = socials.get("linkedin")
        form.instagram_url.data = socials.get("instagram")

        # SEO defaults
        form.seo_default_title.data = settings_obj.seo_default_title
        form.seo_default_description.data = settings_obj.seo_default_description

        # Stats override
        stats = settings_obj.stats_override
        if stats:
            form.override_stats.data = True
            form.stats_groups.data = stats.get("total_groups")
            form.stats_members.data = stats.get("total_members")
            form.stats_projects.data = stats.get("total_projects")
        else:
            form.override_stats.data = False

    if form.validate_on_submit():
        settings_obj.hero_headline = form.hero_headline.data.strip() if form.hero_headline.data else None
        settings_obj.hero_subheadline = form.hero_subheadline.data.strip() if form.hero_subheadline.data else None
        settings_obj.hero_cta_text = form.hero_cta_text.data.strip() if form.hero_cta_text.data else None

        # Handle removals
        remove_paths = request.form.getlist("remove_hero_images")
        current_images = [img for img in (settings_obj.hero_images or []) if img.get("path") not in remove_paths]
        for p in remove_paths:
            try:
                delete_upload(p)
            except Exception:
                pass

        # Handle new hero uploads
        new_files = [f for f in (form.hero_images.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (form.hero_image_alts.data or "").splitlines() if line.strip()]
        for idx, file_storage in enumerate(new_files):
            try:
                saved_path = save_upload(file_storage, subfolder="covers")
                alt_text = alts[idx] if idx < len(alts) else "Hero image"
                current_images.append({"path": saved_path, "alt": alt_text})
            except UploadError as e:
                flash(f"Error uploading hero image: {e}", "danger")
                return render_template("admin/settings.html", form=form, settings=settings_obj)

        settings_obj.hero_images = current_images

        # Footer social links
        socials = {}
        if form.github_url.data and form.github_url.data.strip():
            socials["github"] = form.github_url.data.strip()
        if form.twitter_url.data and form.twitter_url.data.strip():
            socials["twitter"] = form.twitter_url.data.strip()
        if form.linkedin_url.data and form.linkedin_url.data.strip():
            socials["linkedin"] = form.linkedin_url.data.strip()
        if form.instagram_url.data and form.instagram_url.data.strip():
            socials["instagram"] = form.instagram_url.data.strip()
        settings_obj.footer_social_links = socials

        # SEO defaults
        settings_obj.seo_default_title = form.seo_default_title.data.strip() if form.seo_default_title.data else None
        settings_obj.seo_default_description = form.seo_default_description.data.strip() if form.seo_default_description.data else None
        if form.seo_default_og_image.data and getattr(form.seo_default_og_image.data, "filename", None):
            try:
                settings_obj.seo_default_og_image = replace_upload(form.seo_default_og_image.data, old_path=settings_obj.seo_default_og_image, subfolder="covers")
            except UploadError as e:
                flash(f"Error uploading OG image: {e}", "danger")
                return render_template("admin/settings.html", form=form, settings=settings_obj)

        # Stats override
        if form.override_stats.data:
            settings_obj.stats_override = {
                "total_groups": form.stats_groups.data,
                "total_members": form.stats_members.data,
                "total_projects": form.stats_projects.data,
            }
        else:
            settings_obj.stats_override = None

        settings_obj.updated_at = datetime.utcnow()
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))

    return render_template("admin/settings.html", form=form, settings=settings_obj)

