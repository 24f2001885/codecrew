import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import current_user
from app.extensions import db
from app.models.project import Project
from app.models.member import Member
from app.security.decorators import coder_required, apply_guard_to_blueprint
from app.services.slugs import unique_slug
from app.services.uploads import save_upload, delete_upload, replace_upload, UploadError
from app.services.private_files import send_private
from app.services.access import (
    granted_requests_for,
    get_granted_request_or_404,
    serialize_request_for_coder,
    active_grants_query,
)
from app.services.audit import record_audit
from app.forms.coder_forms import CoderProfileForm, CoderProjectForm

coder_bp = Blueprint("coder", __name__, url_prefix="/coder")

# Guard every route in this blueprint with coder_required
apply_guard_to_blueprint(coder_bp, coder_required)


@coder_bp.route("/dashboard")
def dashboard():
    coder = current_user
    member = coder.member
    group = member.group if member else None

    # Counts
    project_count = Project.query.filter_by(group_id=group.id).count() if group else 0
    active_grants_count = active_grants_query(coder.id).count()

    return render_template(
        "coder/dashboard.html",
        coder=coder,
        member=member,
        group=group,
        project_count=project_count,
        active_grants_count=active_grants_count,
    )


@coder_bp.route("/profile", methods=["GET", "POST"])
def profile():
    member = current_user.member
    if not member:
        abort(404)

    form = CoderProfileForm(obj=member)
    if request.method == "GET":
        if member.skill_tags:
            form.skill_tags.data = ", ".join(member.skill_tags)

    if form.validate_on_submit():
        member.role = form.role.data.strip() if form.role.data else None
        member.bio = form.bio.data.strip() if form.bio.data else None
        member.skill_tags = form.parse_tags()
        member.github_url = form.github_url.data.strip() if form.github_url.data else None
        member.linkedin_url = form.linkedin_url.data.strip() if form.linkedin_url.data else None
        member.twitter_url = form.twitter_url.data.strip() if form.twitter_url.data else None

        if form.photo.data and getattr(form.photo.data, "filename", None):
            try:
                member.photo_path = replace_upload(form.photo.data, old_path=member.photo_path, subfolder="photos")
            except UploadError as ue:
                flash(f"Photo upload error: {ue}", "danger")
                return render_template("coder/profile.html", form=form, member=member)

        if form.resume_pdf.data and getattr(form.resume_pdf.data, "filename", None):
            try:
                member.resume_pdf = replace_upload(form.resume_pdf.data, old_path=member.resume_pdf, subfolder="resumes", kind="pdf")
            except UploadError as ue:
                flash(f"Resume upload error: {ue}", "danger")
                return render_template("coder/profile.html", form=form, member=member)

        record_audit("coder", current_user.id, "member.coder_edited", "member", str(member.id))
        db.session.commit()
        flash("Your profile has been updated.", "success")
        return redirect(url_for("coder.profile"))

    return render_template("coder/profile.html", form=form, member=member)


@coder_bp.route("/projects")
def projects():
    member = current_user.member
    if not member or not member.group_id:
        return render_template("coder/projects_list.html", pagination=None, projects=[])

    page = request.args.get("page", 1, type=int)
    pagination = (
        Project.query.filter_by(group_id=member.group_id)
        .order_by(Project.created_at.desc())
        .paginate(page=page, per_page=12, error_out=False)
    )
    return render_template("coder/projects_list.html", pagination=pagination)


@coder_bp.route("/projects/new", methods=["GET", "POST"])
def project_new():
    member = current_user.member
    if not member or not member.group_id:
        flash("You are not associated with a group.", "danger")
        return redirect(url_for("coder.dashboard"))

    form = CoderProjectForm()
    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = unique_slug(Project, title, scope={"group_id": member.group_id})
        screenshot_path = None
        if form.screenshot.data and getattr(form.screenshot.data, "filename", None):
            try:
                screenshot_path = save_upload(form.screenshot.data, subfolder="screenshots")
            except UploadError as ue:
                flash(f"Screenshot error: {ue}", "danger")
                return render_template("coder/project_form.html", form=form, title="New Project")

        # Handle gallery images
        gallery_images = []
        new_files = [f for f in (form.gallery_images.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (form.gallery_alts.data or "").splitlines() if line.strip()]
        for idx, file_storage in enumerate(new_files):
            try:
                saved_path = save_upload(file_storage, subfolder="screenshots")
                alt_text = alts[idx] if idx < len(alts) else f"Screenshot {idx+1}"
                gallery_images.append({"path": saved_path, "alt": alt_text})
            except UploadError as ue:
                flash(f"Gallery upload error: {ue}", "danger")
                return render_template("coder/project_form.html", form=form, title="New Project")

        project = Project(
            group_id=member.group_id,
            title=title,
            slug=slug,
            summary=form.summary.data.strip() if form.summary.data else None,
            description=form.description.data.strip() if form.description.data else None,
            tech_tags=form.parse_tags(),
            demo_url=form.demo_url.data.strip() if form.demo_url.data else None,
            live_url=form.live_url.data.strip() if form.live_url.data else None,
            github_url=form.github_url.data.strip() if form.github_url.data else None,
            screenshot=screenshot_path,
            gallery_images=gallery_images,
            featured=False,  # Coders cannot mark projects as featured
            created_by_coder_id=current_user.id,
        )
        db.session.add(project)
        record_audit("coder", current_user.id, "project.created", "project", str(project.id), {"title": title})
        db.session.commit()
        flash(f"Project '{project.title}' created successfully.", "success")
        return redirect(url_for("coder.projects"))

    return render_template("coder/project_form.html", form=form, title="New Project")


@coder_bp.route("/projects/<id>/edit", methods=["GET", "POST"])
def project_edit(id):
    member = current_user.member
    project = db.session.get(Project, id) or abort(404)
    if not member or project.group_id != member.group_id:
        abort(404)

    form = CoderProjectForm(obj=project)
    if request.method == "GET":
        if project.tech_tags:
            form.tech_tags.data = ", ".join(project.tech_tags)

    if form.validate_on_submit():
        project.title = form.title.data.strip()
        project.slug = unique_slug(Project, project.title, scope={"group_id": member.group_id}, exclude_id=project.id)
        project.summary = form.summary.data.strip() if form.summary.data else None
        project.description = form.description.data.strip() if form.description.data else None
        project.tech_tags = form.parse_tags()
        project.demo_url = form.demo_url.data.strip() if form.demo_url.data else None
        project.live_url = form.live_url.data.strip() if form.live_url.data else None
        project.github_url = form.github_url.data.strip() if form.github_url.data else None

        if form.screenshot.data and getattr(form.screenshot.data, "filename", None):
            try:
                project.screenshot = replace_upload(form.screenshot.data, old_path=project.screenshot, subfolder="screenshots")
            except UploadError as ue:
                flash(f"Screenshot error: {ue}", "danger")
                return render_template("coder/project_form.html", form=form, project=project, title="Edit Project")

        # Handle removals
        remove_paths = request.form.getlist("remove_gallery_images")
        current_gallery = [img for img in (project.gallery_images or []) if img.get("path") not in remove_paths]
        for p in remove_paths:
            try:
                delete_upload(p)
            except Exception:
                pass

        # Handle new uploads
        new_files = [f for f in (form.gallery_images.data or []) if getattr(f, "filename", None)]
        alts = [line.strip() for line in (form.gallery_alts.data or "").splitlines() if line.strip()]
        for idx, file_storage in enumerate(new_files):
            try:
                saved_path = save_upload(file_storage, subfolder="screenshots")
                alt_text = alts[idx] if idx < len(alts) else f"Screenshot {idx+1}"
                current_gallery.append({"path": saved_path, "alt": alt_text})
            except UploadError as ue:
                flash(f"Gallery upload error: {ue}", "danger")
                return render_template("coder/project_form.html", form=form, project=project, title="Edit Project")

        project.gallery_images = current_gallery
        project.last_edited_by_coder_id = current_user.id
        record_audit("coder", current_user.id, "project.edited", "project", str(project.id), {"title": project.title})
        db.session.commit()
        flash(f"Project '{project.title}' updated successfully.", "success")
        return redirect(url_for("coder.projects"))

    return render_template("coder/project_form.html", form=form, project=project, title="Edit Project")


@coder_bp.route("/opportunities")
def opportunities():
    page = request.args.get("page", 1, type=int)
    pagination = granted_requests_for(current_user, page=page, per_page=10)
    
    serialized_items = []
    if pagination:
        for req_obj, grant_obj in pagination.items:
            serialized_items.append(serialize_request_for_coder(req_obj, grant_obj))

    return render_template(
        "coder/opportunities_list.html",
        pagination=pagination,
        opportunities=serialized_items,
    )


@coder_bp.route("/opportunities/<request_id>")
def opportunity_detail(request_id):
    req_obj, grant_obj = get_granted_request_or_404(current_user, request_id)
    serialized = serialize_request_for_coder(req_obj, grant_obj)
    return render_template(
        "coder/opportunity_detail.html",
        opportunity=serialized,
        grant=grant_obj,
    )


@coder_bp.route("/opportunities/<request_id>/attachment")
def opportunity_attachment(request_id):
    req_obj, _ = get_granted_request_or_404(current_user, request_id)
    ext = os.path.splitext(req_obj.attachment_path)[1]
    download_name = f"request_{req_obj.id}{ext}"
    return send_private("requests", req_obj.attachment_path, download_name=download_name)
