from functools import wraps
from flask import redirect, url_for, abort, request, flash
from flask_login import current_user
from werkzeug.routing import BuildError


def _check_super_admin():
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))
    if getattr(current_user, "role", None) != "super_admin":
        abort(403)
    return None


def _check_coder():
    if not current_user.is_authenticated:
        try:
            return redirect(url_for("coder_auth.login", next=request.path))
        except BuildError:
            return redirect(url_for("auth.login", next=request.path))
    if getattr(current_user, "role", None) != "coder":
        abort(403)
    if getattr(current_user, "status", None) != "active":
        try:
            return redirect(url_for("coder_auth.login", next=request.path))
        except BuildError:
            return redirect(url_for("auth.login", next=request.path))
    return None


def super_admin_required(view):
    """
    Ensures current_user is authenticated and has role 'super_admin'.
    Redirects unauthenticated users to auth.login with next parameter.
    Aborts with HTTP 403 if authenticated but not super_admin.
    """
    @wraps(view)
    def decorated_view(*args, **kwargs):
        check = _check_super_admin()
        if check is not None:
            return check
        return view(*args, **kwargs)
    return decorated_view


def coder_required(view):
    """
    Ensures current_user is authenticated and has role 'coder'.
    Redirects unauthenticated users to coder_auth.login (or auth.login).
    Aborts with HTTP 403 if authenticated but not coder.
    """
    @wraps(view)
    def decorated_view(*args, **kwargs):
        check = _check_coder()
        if check is not None:
            return check
        return view(*args, **kwargs)
    return decorated_view


def apply_guard_to_blueprint(blueprint, guard, allow_endpoints=()):
    """
    Registers a blueprint.before_request hook that enforces the specified guard
    on every route unless the endpoint is listed in allow_endpoints.
    Matches either full endpoint name (e.g. 'auth.login') or short name (e.g. 'login').
    """
    @blueprint.before_request
    def blueprint_guard():
        endpoint = request.endpoint
        short_endpoint = endpoint.split(".", 1)[-1] if endpoint and "." in endpoint else endpoint
        if endpoint in allow_endpoints or short_endpoint in allow_endpoints:
            return None

        @guard
        def _guarded():
            return None

        return _guarded()
