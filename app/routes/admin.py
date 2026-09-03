"""
FILE PURPOSE: Admin blueprint — P1 scope is exactly one route (the empty
Dashboard) proving the @login_required gate and admin_base.html shell
render end to end. Full CRUD screens are P3+ scope (Master Project
Blueprint §3).

PROMPT FOR LLM IMPLEMENTATION:
1. admin_bp = Blueprint("admin", __name__, url_prefix="/admin").
2. @admin_bp.route("/dashboard") def dashboard(): decorate with
   @login_required (from flask_login), render "admin/dashboard.html".
   NOTE: "admin/dashboard.html" and "admin/admin_base.html" are seeded by
   Harshlata on task-harshlata-phase1-admin-shell.
3. Do NOT add any Group/Member/Project/Message/Request summary-card
   queries yet — those models have no seeded rows until P2/P3, and the
   Dashboard is explicitly "empty" per the Blueprint's P1 goal. Pass no
   extra template context beyond what admin_base.html needs.
4. Keep this file free of any CRUD routes — Groups/Members/Projects/Blog/
   Messages/Project Requests/Settings routes all land on this same
   blueprint later (P3, P4, P6) per the Unified Directory Structure.

DEBUGGING:
# print("[DEBUG] GET /admin/dashboard — rendering empty admin shell (P1)")

OFFLINE DOCKER TEST CASES:
- GET "/admin/dashboard" with no session redirects to "/admin/login".
- GET "/admin/dashboard" with a logged-in test session (via Utkarsh's
  auth routes) returns HTTP 200 and includes the admin sidebar markup
  from admin_base.html.
"""
