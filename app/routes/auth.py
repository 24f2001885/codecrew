from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.extensions import db, login_manager, limiter
from app.models.admin_user import AdminUser
from app.forms.auth_forms import LoginForm, ForgotPasswordForm, ResetPasswordForm
from app.services.tokens import make_token, read_token, fingerprint, max_age_for
from app.services.mailer import send_password_reset_email

auth_bp = Blueprint("auth", __name__, url_prefix="/admin")


@login_manager.user_loader
def load_user(user_id):
    """
    Namespaced user loader: splits user_id on ':'.
    'admin:<id>' -> AdminUser.query.get(id)
    'coder:<id>' -> CoderUser.query.get(id) if active (once CoderUser exists in P7)
    Unknown prefix or missing user returns None.
    """
    if not user_id or ":" not in user_id:
        return None

    prefix, actual_id = user_id.split(":", 1)
    if prefix == "admin":
        return db.session.get(AdminUser, actual_id)
    elif prefix == "coder":
        try:
            from app.models.coder_user import CoderUser
            coder = db.session.get(CoderUser, actual_id)
            if coder and getattr(coder, "status", None) == "active":
                return coder
            return None
        except (ImportError, Exception):
            return None
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == "super_admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("public.index"))

    form = LoginForm()
    if form.validate_on_submit():
        user = AdminUser.query.filter_by(username=form.username.data.strip()).first()
        if user and user.check_password(form.password.data):
            # Log out first so browser holds only one identity
            logout_user()
            login_user(user)
            flash("Welcome back!", "success")
            next_page = request.args.get("next")
            if next_page and next_page.startswith("/"):
                return redirect(next_page)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid username or password.", "danger")

    return render_template("admin/login.html", form=form)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        admin = AdminUser.query.filter_by(username=form.username.data.strip()).first()
        if admin:
            token = make_token("admin_reset", {"id": admin.id, "fp": fingerprint(admin.password_hash)})
            reset_url = url_for("auth.reset_password", token=token, _external=True)
            send_password_reset_email(admin, reset_url)

        # Generic flash message regardless of whether user exists
        flash("If that account exists, a reset link has been sent to the administrator email.", "info")
        return redirect(url_for("auth.login"))

    return render_template("admin/forgot_password.html", form=form)


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    max_age = max_age_for("admin_reset")
    payload = read_token("admin_reset", token, max_age=max_age)

    if not payload or not isinstance(payload, dict) or "id" not in payload or "fp" not in payload:
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for("auth.forgot_password"))

    admin = db.session.get(AdminUser, payload["id"])
    if not admin:
        flash("The account associated with this reset link no longer exists.", "danger")
        return redirect(url_for("auth.forgot_password"))

    # Single-use enforcement: verify fingerprint matches current password hash
    if fingerprint(admin.password_hash) != payload["fp"]:
        flash("This reset link has already been used. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        admin.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been successfully reset. Please log in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("admin/reset_password.html", form=form, token=token)
