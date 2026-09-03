"""
FILE PURPOSE: Flask application factory — extends the P0 skeleton to
register the new auth blueprint, gate the first admin route, and confirm
every full model (Piyush's task-piyush-phase1-data-models branch) is
visible to Flask-Migrate.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything create_app() already does in P0 (config load, extension
   init, model imports inside an app context, logging setup, `now`
   context processor).
2. _register_blueprints(app): now also import and register `auth_bp` from
   app/routes/auth.py and a new `admin_bp` from app/routes/admin.py,
   alongside the existing `public_bp`. Leave a comment noting the
   remaining admin CRUD blueprints (contact_bp/requests_bp in P4,
   api_bp in P5) still aren't registered yet.
3. Confirm login_manager.init_app(app) is called (it already is, from
   app/extensions.py) and that AdminUser is importable at the point
   login_manager's user_loader callback (defined in app/routes/auth.py)
   needs it — this only works once Piyush's branch is merged into
   phase1, note that as a comment.
4. No other changes to the factory's shape from P0.

DEBUGGING:
# print(f"[DEBUG] App created with config={config_name}; blueprints=public,auth,admin")

OFFLINE DOCKER TEST CASES:
- create_app("testing") still returns a Flask instance with app.testing
  is True.
- GET "/admin/dashboard" without a session redirects (302) to
  "/admin/login" (proves @login_required + login_manager.login_view
  wiring from app/extensions.py actually took effect).
- GET "/admin/login" returns HTTP 200 once Harshlata's login.html and
  Utkarsh's auth routes are merged in.
"""
