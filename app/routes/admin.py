from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from app.extensions import db
from app.models.group import Group
from app.models.member import Member
from app.models.project import Project
from app.forms.group_forms import GroupForm
from app.forms.member_forms import MemberForm
from app.forms.project_forms import ProjectForm
from app.security.decorators import super_admin_required, apply_guard_to_blueprint
from app.services.slugs import unique_slug
from app.services.uploads import save_upload, delete_upload, replace_upload, UploadError

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Protect all current and future routes in admin_bp with super_admin_required
apply_guard_to_blueprint(admin_bp, super_admin_required)


@admin_bp.route("/dashboard")
def dashboard():
    group_count = Group.query.count()
    member_count = Member.query.count()
    project_count = Project.query.count()
    return render_template(
        "admin/dashboard.html",
        group_count=group_count,
        member_count=member_count,
        project_count=project_count,
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
