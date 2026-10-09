from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app.extensions import db, limiter
from app.models.coder_user import CoderUser
from app.forms.coder_forms import (
    CoderLoginForm,
    CoderInviteAcceptForm,
    CoderForgotPasswordForm,
    CoderResetPasswordForm,
)
from app.services.tokens import make_token, read_token, fingerprint, max_age_for
from app.services.mailer import send_coder_password_reset
from app.services.audit import record_audit

coder_auth_bp = Blueprint("coder_auth", __name__, url_prefix="/coder")


@coder_auth_bp.route("/accept-invite/<token>", methods=["GET", "POST"])
def accept_invite(token):
    max_age = max_age_for("coder_invite")
    payload = read_token("coder_invite", token, max_age=max_age)
    if not payload or "id" not in payload:
        flash("Invalid or expired invitation link. Please request a new invite from your administrator.", "danger")
        return redirect(url_for("coder_auth.login"))

    coder = db.session.get(CoderUser, payload["id"])
    if not coder or coder.status == "revoked":
        flash("This invitation is no longer valid.", "danger")
        return redirect(url_for("coder_auth.login"))

    form = CoderInviteAcceptForm()
    if form.validate_on_submit():
        coder.set_password(form.password.data)
        coder.status = "active"
        coder.activated_at = datetime.now(timezone.utc)
        record_audit("coder", coder.id, "coder.invite_accepted", "coder_user", coder.id)
        db.session.commit()
        flash("Your account has been activated! Please log in with your new password.", "success")
        return redirect(url_for("coder_auth.login"))

    return render_template("coder/accept_invite.html", form=form, coder=coder)


@coder_auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute", methods=["POST"])
def login():
    if current_user.is_authenticated:
        if getattr(current_user, "role", None) == "coder":
            return redirect(url_for("coder.dashboard"))
        elif getattr(current_user, "role", None) == "super_admin":
            logout_user()

    form = CoderLoginForm()
    if form.validate_on_submit():
        username_or_email = form.username.data.strip()
        coder = CoderUser.query.filter(
            (CoderUser.username == username_or_email) | (CoderUser.email == username_or_email)
        ).first()

        if not coder or not coder.check_password(form.password.data):
            flash("Invalid username or password.", "danger")
            return render_template("coder/login.html", form=form)

        if coder.status == "revoked":
            flash("Your coder account has been revoked. Please contact an administrator.", "danger")
            return render_template("coder/login.html", form=form)

        if coder.status != "active":
            flash("Your account is not yet active. Please check your invitation email.", "warning")
            return render_template("coder/login.html", form=form)

        # Clear any prior session
        logout_user()
        login_user(coder)
        coder.last_login_at = datetime.now(timezone.utc)
        db.session.commit()
        flash(f"Welcome back, {coder.username}!", "success")
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/coder") and not next_page.startswith("/coder/login"):
            return redirect(next_page)
        return redirect(url_for("coder.dashboard"))

    return render_template("coder/login.html", form=form)


@coder_auth_bp.route("/logout", methods=["POST"])
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("coder_auth.login"))


@coder_auth_bp.route("/forgot-password", methods=["GET", "POST"])
@limiter.limit("5 per hour", methods=["POST"])
def forgot_password():
    form = CoderForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        coder = CoderUser.query.filter_by(email=email).first()
        if coder and coder.status == "active":
            token = make_token("coder_reset", {"id": coder.id, "fp": fingerprint(coder.password_hash)})
            send_coder_password_reset(coder, token)

        flash("If an account with that email exists, password reset instructions have been sent.", "info")
        return redirect(url_for("coder_auth.login"))

    return render_template("coder/forgot_password.html", form=form)


@coder_auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    max_age = max_age_for("coder_reset")
    payload = read_token("coder_reset", token, max_age=max_age)
    if not payload or "id" not in payload:
        flash("Invalid or expired password reset link. Please request a new one.", "danger")
        return redirect(url_for("coder_auth.forgot_password"))

    coder = db.session.get(CoderUser, payload["id"])
    if not coder or coder.status != "active":
        flash("Invalid password reset request.", "danger")
        return redirect(url_for("coder_auth.login"))

    # Single-use check: fingerprint must match current hash
    expected_fp = fingerprint(coder.password_hash)
    if payload.get("fp") != expected_fp:
        flash("This reset link has already been used. Please request a new one.", "danger")
        return redirect(url_for("coder_auth.forgot_password"))

    form = CoderResetPasswordForm()
    if form.validate_on_submit():
        coder.set_password(form.password.data)
        record_audit("coder", coder.id, "coder.password_reset", "coder_user", coder.id)
        db.session.commit()
        flash("Your password has been reset successfully. Please log in.", "success")
        return redirect(url_for("coder_auth.login"))

    return render_template("coder/reset_password.html", form=form, coder=coder)
