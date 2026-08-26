"""
FILE PURPOSE: Flask application factory — builds and configures the app,
binds extensions, wires the model registry, registers blueprints.

PROMPT FOR LLM IMPLEMENTATION:
1. Define create_app(config_name=None): build Flask(__name__), load config
   via app.config.from_object(get_config(config_name)) from app/config.py.
2. _init_extensions(app): call .init_app(app) on every extension from
   app/extensions.py — db, migrate (needs db too), login_manager, mail,
   csrf, limiter. Inside an app.app_context(), import every model module
   from app/models/ (admin_user, group, member, project, blog_post,
   contact_message, project_request, site_settings) so Flask-Migrate sees
   every table before the first `flask db migrate` (TDR §4). NOTE: these
   model files are seeded by Piyush on task-piyush-data-models — this
   import will only resolve once that branch is merged into phase0, so
   test this file's own logic against stub models locally if needed.
3. _init_logging(app): implement TDR §12 — a StreamHandler formatted as
   "%(asctime)s %(levelname)s %(name)s %(message)s", only attached if
   app.logger has no handlers yet; level DEBUG if app.debug else INFO.
4. _register_blueprints(app): import and register only `public_bp` from
   app/routes/public.py this milestone. Leave a comment noting
   auth_bp (P1), admin_bp (P3), contact_bp/requests_bp (P4), api_bp (P5).
5. Register a context processor injecting `now` (datetime.now(timezone.utc))
   for templates.
6. Return the built app.

DEBUGGING:
# print(f"[DEBUG] App created with config={config_name}")

OFFLINE DOCKER TEST CASES:
- create_app("testing") returns a Flask instance with app.testing is True.
- After create_app(), db.metadata.tables contains all 8 expected table
  names (admin_users, groups, members, projects, blog_posts,
  contact_messages, project_requests, site_settings) — verify once
  Piyush's model branch is merged in.
- GET "/" on the test client returns HTTP 200.
"""
