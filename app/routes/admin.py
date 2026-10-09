from flask import Blueprint, render_template
from app.security.decorators import super_admin_required, apply_guard_to_blueprint

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Automatically protect all current and future routes in admin_bp with super_admin_required
apply_guard_to_blueprint(admin_bp, super_admin_required)


@admin_bp.route("/dashboard")
@super_admin_required
def dashboard():
    return render_template("admin/dashboard.html")
