#!/usr/bin/env bash
# P0.sh
# CodeCrews — Milestone P0: Project Setup & Scaffolding
#
# Team for this milestone:
#   Abhishek  — Team Lead (phase init, base skeleton, PR review/integration,
#               test-phase decision per team_lead_workflow_guide.pdf)
#   Abhinav   — App Core & Wiring
#   Piyush    — Data Models
#   Harshlata — Themed Shell (Frontend)
#   Tripti    — Docker & Testing Infra
#
# This script contains zero application logic. Every .py/.html/.css/.js
# file below is a heredoc holding a PROMPT for an LLM (code-implementer)
# to fill in later, split across four task branches so each developer's
# PR only touches the files they own. Static, non-logic manifests
# (.env.example, requirements.txt, .gitignore, .dockerignore) are written
# with their real final contents directly — there's nothing to
# "implement" in a pinned dependency list or an ignore-pattern file.
#
# Source docs: master-project-blueprint.md §1 (dir tree) + §3 (P0 map),
# project-definition-report.md, technical-design-report.md §4/§9,
# developer_workflow_guide.pdf, team_lead_workflow_guide.pdf.

set -e

# --- SAFETY CHECK FOR EMPTY REPOSITORY ---
# This fixes the "pathspec 'MAIN' did not match any file(s)" error.
if ! git log -1 &>/dev/null; then
    echo "No commits found. Creating the initial commit to establish MAIN..."
    git add P0.sh >/dev/null 2>&1 || true
    git commit --allow-empty -m "Initial commit: Establish MAIN branch"
fi
# -----------------------------------------

echo "====================================================="
echo "CodeCrews — P0: Project Setup & Scaffolding"
echo "Team: Abhishek (Lead), Abhinav, Piyush, Harshlata, Tripti"
echo "====================================================="

# -----------------------------------------------------------------------
# 1. TEAM LEAD (ABHISHEK) — PHASE INITIALIZATION
# -----------------------------------------------------------------------
# team_lead_workflow_guide.pdf §1: the Team Lead establishes the
# structural branches before any developer starts work. Mapped onto our
# P0-P6 milestone numbering as phase0-seed / phase0 for milestone P0
# (phase1-seed / phase1 for P1, and so on). Idempotent — safe to re-run.

echo ""
echo "--- [Abhishek | Team Lead] Phase 0 initialization ---"

if git show-ref --quiet refs/heads/phase0-seed; then
    echo "phase0-seed already exists locally — skipping creation."
else
    echo "Creating phase0-seed from MAIN..."
    git checkout MAIN
    git checkout -b phase0-seed MAIN
fi

if git show-ref --quiet refs/heads/phase0; then
    echo "phase0 already exists locally — skipping creation."
else
    echo "Creating phase0 from phase0-seed..."
    git checkout -b phase0 phase0-seed
fi

echo "Pushing structural branches to origin..."
git push -u origin phase0-seed || echo "WARNING: could not push phase0-seed (check remote access)."
git push -u origin phase0 || echo "WARNING: could not push phase0 (check remote access)."

# -----------------------------------------------------------------------
# 2. TEAM LEAD (ABHISHEK) — BASE SKELETON ON phase0
# -----------------------------------------------------------------------
# Directory tree only (Blueprint §1) — no files with real content yet.
# Committed directly to phase0 so every developer's task branch starts
# from the same skeleton.

echo ""
echo "--- [Abhishek | Team Lead] Seeding base directory skeleton on phase0 ---"
git checkout phase0

mkdir -p app/models
mkdir -p app/routes
mkdir -p app/forms
mkdir -p app/services
mkdir -p app/templates/partials
mkdir -p app/templates/admin
mkdir -p app/templates/public
mkdir -p app/templates/errors
mkdir -p app/static/css
mkdir -p app/static/js
mkdir -p app/static/images
mkdir -p app/static/uploads/logos
mkdir -p app/static/uploads/covers
mkdir -p app/static/uploads/photos
mkdir -p app/static/uploads/screenshots
mkdir -p app/static/uploads/resumes
mkdir -p app/static/uploads/requests
mkdir -p migrations
mkdir -p tests

touch app/templates/admin/.gitkeep app/templates/public/.gitkeep app/templates/errors/.gitkeep
touch app/static/images/.gitkeep
touch app/static/uploads/logos/.gitkeep app/static/uploads/covers/.gitkeep app/static/uploads/photos/.gitkeep
touch app/static/uploads/screenshots/.gitkeep app/static/uploads/resumes/.gitkeep app/static/uploads/requests/.gitkeep
touch migrations/.gitkeep

git add -A
git commit -q -m "P0: base directory skeleton (Abhishek)" || echo "Nothing to commit for skeleton."
git push origin phase0 || echo "WARNING: could not push phase0 (check remote access)."

# =========================================================================
# 3. DEVELOPER TASK BRANCHES (each synced from phase0, per
#    developer_workflow_guide.pdf "Core Development Workflow")
# =========================================================================

# -------------------------------------------------------------------
# 3a. ABHINAV — App Core & Wiring
# -------------------------------------------------------------------
echo ""
echo "--- [Abhinav] Syncing phase0 and creating task-abhinav-app-core ---"
git checkout phase0
git pull origin phase0 || echo "WARNING: could not pull phase0 (offline/new repo — continuing)."
git checkout -b task-abhinav-app-core phase0

cat << 'EOF' > wsgi.py
"""
FILE PURPOSE: WSGI / Flask CLI entrypoint (TDR §13 operational runbook).

PROMPT FOR LLM IMPLEMENTATION:
1. Call load_dotenv() from python-dotenv BEFORE importing the app factory,
   so config.py never has to guess whether dotenv has already run.
2. Import create_app from app and call app = create_app().
3. Add `if __name__ == "__main__": app.run()` for a direct
   `python wsgi.py` dev-run path.

DEBUGGING:
# print("[DEBUG] wsgi.py — app built for Gunicorn/flask run")

OFFLINE DOCKER TEST CASES:
- Importing wsgi does not raise, even with a mostly-empty .env (as long as
  DATABASE_URL / SECRET_KEY have safe defaults in config.py).
- `app` is a valid Flask instance (has .wsgi_app, .test_client()).
"""
EOF

cat << 'EOF' > seed.py
"""
FILE PURPOSE: Database seed CLI (full logic lands in P1 — this milestone
only wires up the entrypoint per TDR §13's operational runbook).

PROMPT FOR LLM IMPLEMENTATION:
1. Import create_app from app.
2. Define run(): builds the app via create_app(), enters an
   app.app_context(), and for P0 only prints a message confirming the app
   context loads (e.g. "Seed script scaffolded (P0). Super-admin + sample
   data land in P1.") — no AdminUser/Group creation yet, that's P1 scope
   (PDR §5.2: seeded from ADMIN_SEED_USERNAME/ADMIN_SEED_PASSWORD, never a
   UI form).
3. `if __name__ == "__main__": run()`.

DEBUGGING:
# print("[DEBUG] seed.py invoked — no-op until P1 implements AdminUser + sample data")

OFFLINE DOCKER TEST CASES:
- Running `python seed.py` exits 0 and prints a message, with no database
  writes attempted yet.
"""
EOF

cat << 'EOF' > app/__init__.py
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
EOF

cat << 'EOF' > app/config.py
"""
FILE PURPOSE: Environment-driven config classes (Dev/Testing/Production)
per TDR §9.

PROMPT FOR LLM IMPLEMENTATION:
1. BaseConfig reads from os.environ: SECRET_KEY, WTF_CSRF_SECRET_KEY
   (falls back to SECRET_KEY), SQLALCHEMY_DATABASE_URI (from DATABASE_URL,
   default "sqlite:///dev.db"), SQLALCHEMY_TRACK_MODIFICATIONS=False.
2. Add Flask-Mail settings: MAIL_SERVER, MAIL_PORT (int, default 587),
   MAIL_USE_TLS (bool), MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER,
   MAIL_SUPPRESS_SEND (bool, default False), ADMIN_NOTIFICATION_EMAIL.
3. Add upload settings: UPLOAD_FOLDER (default "app/static/uploads"),
   MAX_CONTENT_LENGTH (int, default 5*1024*1024) per PDR §12.
4. Add session/security settings: SESSION_COOKIE_HTTPONLY=True,
   SESSION_COOKIE_SAMESITE="Lax", SESSION_COOKIE_SECURE (bool, default
   False).
5. DevelopmentConfig(BaseConfig): DEBUG=True.
6. TestingConfig(BaseConfig): TESTING=True, SQLALCHEMY_DATABASE_URI
   default "sqlite:///test.db", MAIL_SUPPRESS_SEND=True,
   WTF_CSRF_ENABLED=False (so the test client can POST without a token),
   SESSION_COOKIE_SECURE=False.
7. ProductionConfig(BaseConfig): DEBUG=False, SESSION_COOKIE_SECURE=True.
8. config_by_name dict mapping "development"/"testing"/"production" to the
   three classes; get_config(config_name=None) falls back to
   os.environ.get("FLASK_ENV", "development") and defaults to
   DevelopmentConfig for an unknown name.

DEBUGGING:
# print(f"[DEBUG] Resolved config: {config_name}")

OFFLINE DOCKER TEST CASES:
- get_config("testing")().SQLALCHEMY_DATABASE_URI starts with "sqlite:///test".
- get_config("production")().SESSION_COOKIE_SECURE is True.
- get_config("nonexistent-env") falls back to DevelopmentConfig without
  raising.
"""
EOF

cat << 'EOF' > app/extensions.py
"""
FILE PURPOSE: Shared, unbound Flask extension instances.

PROMPT FOR LLM IMPLEMENTATION:
1. Instantiate: db = SQLAlchemy(), migrate = Migrate(),
   login_manager = LoginManager(), mail = Mail(), csrf = CSRFProtect(),
   limiter = Limiter(key_func=get_remote_address) (from
   flask_limiter.util).
2. Set login_manager.login_view = "auth.login" and
   login_manager.login_message_category = "warning" so an unauthenticated
   visitor hitting an @login_required admin route redirects correctly once
   the auth blueprint exists in P1.
3. Do NOT call .init_app() here — that happens in app/__init__.py's
   factory, to avoid circular imports between models/routes/forms.

DEBUGGING:
# print("[DEBUG] Extensions module imported")

OFFLINE DOCKER TEST CASES:
- Importing this module does not raise, even before any app exists.
- db.Model is usable as a base class immediately after import (Piyush's
  model stubs subclass this).
"""
EOF

cat << 'EOF' > app/routes/__init__.py
"""
FILE PURPOSE: Marks app/routes as a package; documents blueprint rollout
order across milestones.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring listing which blueprint lands in which
   milestone: public (P0), auth (P1), admin (P3), contact + requests
   (P4), api (P5).
2. No logic needed — app/__init__.py imports each blueprint module
   directly when it's registered.

DEBUGGING:
# print("[DEBUG] app.routes package imported")

OFFLINE DOCKER TEST CASES:
- `import app.routes` does not raise.
"""
EOF

cat << 'EOF' > app/routes/public.py
"""
FILE PURPOSE: Public blueprint — P0 scope is a single route proving the
themed shell renders end to end.

PROMPT FOR LLM IMPLEMENTATION:
1. public_bp = Blueprint("public", __name__).
2. @public_bp.route("/") def index(): renders "base.html" directly — no
   real Home page content yet (hero/stats/carousel/directory teaser is
   P2's job per the Master Project Blueprint). NOTE: "base.html" and its
   partials are seeded by Harshlata on task-harshlata-themed-shell.
3. Keep the route free of any database queries — P0 has no seeded data.

DEBUGGING:
# print("[DEBUG] GET / — rendering bare themed shell (P0)")

OFFLINE DOCKER TEST CASES:
- GET "/" returns HTTP 200.
- The response body contains 'id="ftco-loader"', 'id="ftco-navbar"', and
  "<footer" (proving the included partials actually rendered) — verify
  once Harshlata's template branch is merged in.
"""
EOF

cat << 'EOF' > app/forms/__init__.py
"""
FILE PURPOSE: Marks app/forms as a package; documents form rollout order.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring noting Flask-WTF, CSRF-protected forms are
   added starting P1 (auth_forms.py) and P3 onward (group/member/project/
   blog/contact/request/settings forms), per the Master Project
   Blueprint's directory structure.
2. No logic needed in P0.

DEBUGGING:
# print("[DEBUG] app.forms package imported")

OFFLINE DOCKER TEST CASES:
- `import app.forms` does not raise.
"""
EOF

cat << 'EOF' > app/services/__init__.py
"""
FILE PURPOSE: Marks app/services as a package; documents service rollout
order.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring noting business logic kept out of routes lands
   as: uploads.py (P3), mailer.py (P4), search.py (P5).
2. No logic needed in P0.

DEBUGGING:
# print("[DEBUG] app.services package imported")

OFFLINE DOCKER TEST CASES:
- `import app.services` does not raise.
"""
EOF

git add -A
git commit -q -m "P0 seed: app core & wiring placeholders (Abhinav)"
git push -u origin task-abhinav-app-core || echo "WARNING: could not push task-abhinav-app-core (check remote access)."

# -------------------------------------------------------------------
# 3b. PIYUSH — Data Models
# -------------------------------------------------------------------
echo ""
echo "--- [Piyush] Syncing phase0 and creating task-piyush-data-models ---"
git checkout phase0
git pull origin phase0 || echo "WARNING: could not pull phase0 (offline/new repo — continuing)."
git checkout -b task-piyush-data-models phase0

cat << 'EOF' > app/models/__init__.py
"""
FILE PURPOSE: Marks app/models as a package; documents the P0 stub
strategy.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring explaining that every sibling model in P0 is a
   bare stub (table name + primary key only) so Flask-Migrate's history
   starts clean, and that full columns per TDR §4 land in P1.
2. No imports or logic needed here — sibling modules are imported
   explicitly by app/__init__.py (Abhinav's task-abhinav-app-core).

DEBUGGING:
# print("[DEBUG] app.models package imported")

OFFLINE DOCKER TEST CASES:
- `import app.models` does not raise.
"""
EOF

cat << 'EOF' > app/models/admin_user.py
"""
FILE PURPOSE: AdminUser model stub (TDR §4 table: admin_users).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class AdminUser(db.Model) with __tablename__ = "admin_users".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   username/password_hash/created_at land in P1.
4. __repr__ returning "<AdminUser {id}>".

DEBUGGING:
# print(f"[DEBUG] AdminUser stub registered: {AdminUser.__tablename__}")

OFFLINE DOCKER TEST CASES:
- AdminUser.__tablename__ == "admin_users".
- "admin_users" is present in db.metadata.tables after the app is created.
"""
EOF

cat << 'EOF' > app/models/group.py
"""
FILE PURPOSE: Group model stub (TDR §4 table: groups) — the central
entity of the platform.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Group(db.Model) with __tablename__ = "groups".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0; name,
   slug, tagline, description, image paths, tech_tags, social_links,
   featured, and timestamps land in P1, along with relationships to
   Member/Project/BlogPost/ContactMessage.
4. __repr__ returning "<Group {id}>".

DEBUGGING:
# print(f"[DEBUG] Group stub registered: {Group.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Group.__tablename__ == "groups".
- "groups" is present in db.metadata.tables after the app is created.
"""
EOF

cat << 'EOF' > app/models/member.py
"""
FILE PURPOSE: Member model stub (TDR §4 table: members).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Member(db.Model) with __tablename__ = "members".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, name, role, photo_path, bio, skill_tags, social URLs,
   resume_pdf, display_order, and created_at land in P1.
4. __repr__ returning "<Member {id}>".

DEBUGGING:
# print(f"[DEBUG] Member stub registered: {Member.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Member.__tablename__ == "members".
- "members" is present in db.metadata.tables after the app is created.
"""
EOF

cat << 'EOF' > app/models/project.py
"""
FILE PURPOSE: Project model stub (TDR §4 table: projects).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class Project(db.Model) with __tablename__ = "projects".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, title, slug, description, gallery_images, tech_tags,
   URLs, status enum, featured, and created_at land in P1.
4. __repr__ returning "<Project {id}>".

DEBUGGING:
# print(f"[DEBUG] Project stub registered: {Project.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Project.__tablename__ == "projects".
- "projects" is present in db.metadata.tables after the app is created.
"""
EOF

cat << 'EOF' > app/models/blog_post.py
"""
FILE PURPOSE: BlogPost model stub (TDR §4 table: blog_posts) — per-group,
per the resolved PDR §12 / TDR §4 decision, not platform-wide.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class BlogPost(db.Model) with __tablename__ = "blog_posts".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK, title, slug, content, cover_image_path, published_at,
   tags, and created_at land in P1 (schema), with public rendering built
   out in P5.
4. __repr__ returning "<BlogPost {id}>".

DEBUGGING:
# print(f"[DEBUG] BlogPost stub registered: {BlogPost.__tablename__}")

OFFLINE DOCKER TEST CASES:
- BlogPost.__tablename__ == "blog_posts".
- "blog_posts" is present in db.metadata.tables after the app is created.
"""
EOF

cat << 'EOF' > app/models/contact_message.py
"""
FILE PURPOSE: ContactMessage model stub (TDR §4 table: contact_messages)
— group_id is NOT NULL as of v2, no more nullable "suggestion" case.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class ContactMessage(db.Model) with __tablename__ = "contact_messages".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0;
   group_id FK (NOT NULL), name, email, subject, message, is_read, and
   created_at land in P1, with the submit flow built out in P4.
4. __repr__ returning "<ContactMessage {id}>".

DEBUGGING:
# print(f"[DEBUG] ContactMessage stub registered: {ContactMessage.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ContactMessage.__tablename__ == "contact_messages".
- "contact_messages" is present in db.metadata.tables after the app is
  created.
"""
EOF

cat << 'EOF' > app/models/project_request.py
"""
FILE PURPOSE: ProjectRequest model stub (TDR §4 table: project_requests)
— platform-wide, new in v2.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid and db from app.extensions.
2. class ProjectRequest(db.Model) with __tablename__ = "project_requests".
3. id = db.Column(db.String(36), primary_key=True,
   default=lambda: str(uuid.uuid4())) — only the primary key in P0; name,
   email, company, project_type enum, budget_range, timeline, description,
   attachment_path, status enum, assigned_group_id FK, and timestamps land
   in P1, with the submit/inbox flow built out in P4.
4. __repr__ returning "<ProjectRequest {id}>".

DEBUGGING:
# print(f"[DEBUG] ProjectRequest stub registered: {ProjectRequest.__tablename__}")

OFFLINE DOCKER TEST CASES:
- ProjectRequest.__tablename__ == "project_requests".
- "project_requests" is present in db.metadata.tables after the app is
  created.
"""
EOF

cat << 'EOF' > app/models/site_settings.py
"""
FILE PURPOSE: SiteSettings model stub (TDR §4 table: site_settings) —
singleton row, Integer PK always 1 (NOT a UUID like the other models).

PROMPT FOR LLM IMPLEMENTATION:
1. Import db from app.extensions (no uuid needed here).
2. class SiteSettings(db.Model) with __tablename__ = "site_settings".
3. id = db.Column(db.Integer, primary_key=True, default=1) — only the
   primary key in P0; hero/footer/SEO fields and stats_override land in
   P1, with the /admin/settings screen built out in P6.
4. __repr__ returning "<SiteSettings {id}>".

DEBUGGING:
# print(f"[DEBUG] SiteSettings stub registered: {SiteSettings.__tablename__}")

OFFLINE DOCKER TEST CASES:
- SiteSettings.__tablename__ == "site_settings".
- "site_settings" is present in db.metadata.tables after the app is
  created.
"""
EOF

git add -A
git commit -q -m "P0 seed: data model placeholders (Piyush)"
git push -u origin task-piyush-data-models || echo "WARNING: could not push task-piyush-data-models (check remote access)."

# -------------------------------------------------------------------
# 3c. HARSHLATA — Themed Shell (Frontend)
# -------------------------------------------------------------------
echo ""
echo "--- [Harshlata] Syncing phase0 and creating task-harshlata-themed-shell ---"
git checkout phase0
git pull origin phase0 || echo "WARNING: could not pull phase0 (offline/new repo — continuing)."
git checkout -b task-harshlata-themed-shell phase0

cat << 'EOF' > app/templates/base.html
<!--
FILE PURPOSE: Base Jinja layout — loader, navbar, footer, and the full
CSS/JS vendor chain from the Style Guide (Design Plan §7).

PROMPT FOR LLM IMPLEMENTATION:
1. Standard HTML5 doctype, lang="en", responsive viewport meta.
2. {% block title %}CodeCrews{% endblock %} and a
   {% block meta_description %} block with a sensible default.
3. Load the Poppins Google Font (weights 100-900 per Style Guide §7).
4. Link Bootstrap 4.3.1, animate.css, AOS 2.3.4 css, Owl Carousel 2.3.4
   css + theme css, and Magnific Popup css from a CDN as placeholders for
   the original template's bundled vendor/ folder — comment that these
   should be swapped for local static/css/*.min.css files once the source
   "Creative Coder" template assets are dropped in unchanged (Blueprint
   §1).
5. Link the project's own static/css/style.css last, so it overrides
   vendor defaults.
6. In <body>: {% include "partials/loader.html" %}, then
   {% include "partials/navbar.html" %}, then
   {% include "partials/flash_messages.html" %}, then a <main> wrapping
   {% block content %}{% endblock %}, then
   {% include "partials/footer.html" %}.
7. Load jQuery, Popper, Bootstrap JS, AOS JS, Owl Carousel JS,
   jquery.stellar JS, Magnific Popup JS, and Waypoints JS from a CDN,
   followed by the project's own static/js/main.js, then a
   {% block extra_js %}{% endblock %}.
8. NOTE: url_for('public.index') is defined by Abinhav's
   task-abhinav-app-core branch — the brand link will only resolve once
   that branch is merged into phase0.

DEBUGGING:
<!-- <script>console.log("[DEBUG] base.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Rendering "base.html" via Flask's test client does not raise a Jinja
  TemplateNotFound or TemplateSyntaxError.
- The rendered HTML contains exactly one #ftco-loader, one #ftco-navbar,
  and one <footer> element.
-->
EOF

cat << 'EOF' > app/templates/partials/navbar.html
<!--
FILE PURPOSE: Sticky top navbar per Design Plan §2 — gains a `.scrolled`
state after 150px of scroll (handled by static/js/main.js).

PROMPT FOR LLM IMPLEMENTATION:
1. A Bootstrap 4 <nav class="navbar navbar-expand-lg navbar-dark
   ftco_navbar" id="ftco-navbar"> wrapping a .container.
2. A navbar-brand linking to url_for('public.index') reading "CodeCrews".
3. A Bootstrap navbar-toggler burger button (data-toggle="collapse",
   data-target="#ftco-nav") with an aria-label="Toggle navigation" per
   Design Plan §8's accessibility requirement for icon-only controls.
4. A collapsible <div id="ftco-nav"> containing nav items in this exact
   order per Design Plan §2: Home (url_for('public.index')), Groups, Our
   Members, Request a Project. Groups/Our Members/Request a Project are
   placeholder href="#" anchors until their routes exist (P2, P5, P4).

DEBUGGING:
<!-- <script>console.log("[DEBUG] navbar.html included");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered navbar contains all four link labels: "Home", "Groups",
  "Our Members", "Request a Project".
- The toggler button has a non-empty aria-label attribute.
-->
EOF

cat << 'EOF' > app/templates/partials/footer.html
<!--
FILE PURPOSE: 4-column footer widget block per Design Plan §2 wireframe
reference.

PROMPT FOR LLM IMPLEMENTATION:
1. A <footer class="ftco-footer"> with a .container > .row containing
   four .col-md-3 columns: "CodeCrews" (blurb), "Explore" (Home/Groups/
   Our Members links), "Get in Touch" (Request a Project link), and
   "Follow" (social icon placeholders — note these become dynamic from
   SiteSettings.footer_social_links in P6).
2. A closing full-width row with a copyright line using the `now`
   context variable's year (guard with `{{ now.year if now else "" }}`).

DEBUGGING:
<!-- <script>console.log("[DEBUG] footer.html included");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered footer contains a <footer> tag and exactly four
  .col-md-3 columns.
-->
EOF

cat << 'EOF' > app/templates/partials/loader.html
<!--
FILE PURPOSE: Full-screen loader spinner per Style Guide §7
(--cc-color-loader: #F96D00).

PROMPT FOR LLM IMPLEMENTATION:
1. A <div id="ftco-loader" class="show fullscreen"> containing an inline
   <svg class="circular"> with two <circle> elements: a background path
   (stroke="#eeeeee") and an animated path (stroke="#F96D00").
2. No JS here — static/js/main.js adds a "fadeOut" class to #ftco-loader
   on window load.

DEBUGGING:
<!-- <script>console.log("[DEBUG] loader.html included");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered HTML contains id="ftco-loader" and an inline <svg>.
-->
EOF

cat << 'EOF' > app/templates/partials/flash_messages.html
<!--
FILE PURPOSE: Shared Bootstrap alert pattern for flashed messages, reused
by every form in the project (PDR §5.1 — "auto-dismissing" flash alerts).

PROMPT FOR LLM IMPLEMENTATION:
1. {% with messages = get_flashed_messages(with_categories=true) %} then
   loop, rendering each as a Bootstrap
   <div class="alert alert-{category} alert-dismissible fade show
   js-flash-alert" role="alert"> with a dismiss button
   (data-dismiss="alert", aria-label="Close").
2. Map the flash category "error" to Bootstrap's "danger" class (Bootstrap
   has no built-in "error" alert class); pass every other category
   through unchanged (e.g. "success", "warning", "info").
3. Wrap the block in a .container with a top margin so it doesn't collide
   with the fixed navbar.

DEBUGGING:
<!-- <script>console.log("[DEBUG] flash_messages.html included");</script> -->

OFFLINE DOCKER TEST CASES:
- Flashing a message with category "error" before rendering produces an
  element with class "alert-danger" (not "alert-error").
- No messages flashed => the partial renders no .alert elements at all.
-->
EOF

cat << 'EOF' > app/static/css/style.css
/*
FILE PURPOSE: Base project stylesheet — CSS variables from the Style
Guide (Design Plan §7), plus loader/navbar/footer styling. Extended per
milestone, never replaced.

PROMPT FOR LLM IMPLEMENTATION:
1. Define :root CSS variables exactly matching the Style Guide:
   --cc-color-primary: #ffbd39; --cc-color-secondary: #a0f669;
   --cc-color-loader: #F96D00; --cc-color-bg: #000000;
   --cc-color-text: #999999; --cc-color-text-on-light: #212529;
   --cc-font-family: 'Poppins', Arial, sans-serif.
2. Apply --cc-color-bg/--cc-color-text/--cc-font-family to body; style
   links to use --cc-color-primary, hover/focus to --cc-color-secondary.
3. Style #ftco-loader as a fixed, full-viewport, centered flex container
   over --cc-color-bg with a `.fadeOut` class transitioning opacity/
   visibility to 0/hidden; add rotate + dash keyframe animations for the
   inline SVG spinner.
4. Style .ftco_navbar as transparent with padding, transitioning to a
   `.scrolled` state with a near-opaque dark background and reduced
   padding; nav-links white, hovering to --cc-color-primary.
5. Style .ftco-footer with a slightly-lighter-than-black background,
   heading/link colors matching the dark theme, and inline social icons.

DEBUGGING:
/* console.log("[DEBUG] style.css loaded"); */

OFFLINE DOCKER TEST CASES:
- The compiled stylesheet defines all six --cc-* custom properties listed
  above at :root scope.
- The stylesheet is valid CSS (no unclosed braces).
*/
EOF

cat << 'EOF' > app/static/js/main.js
/*
FILE PURPOSE: Base project JS — hides the loader, toggles the navbar's
`.scrolled` state, auto-dismisses flash alerts. Extended per milestone,
never replaced.

PROMPT FOR LLM IMPLEMENTATION:
1. Wrap everything in an IIFE taking jQuery as $, "use strict".
2. On $(window).on("load", ...), add the "fadeOut" class to #ftco-loader.
3. Track $(window).scroll to add/remove a "scrolled" class on #ftco-navbar
   once scrollTop() exceeds 150px (Design Plan §2); call the check once
   immediately, in case the page loads already scrolled.
4. After 5 seconds (setTimeout), call .alert("close") on every
   .js-flash-alert element, per PDR §5.1's "auto-dismissing" flash alerts.
5. If window.AOS exists, call AOS.init({ duration: 800, once: true }) —
   guarded so this file doesn't error before AOS's script tag loads on
   templates that don't need it yet.

DEBUGGING:
// console.log("[DEBUG] window load — loader hidden");

OFFLINE DOCKER TEST CASES:
- Simulating a "load" event triggers #ftco-loader to gain the "fadeOut"
  class.
- Setting window scrollTop above 150 and firing "scroll" adds "scrolled"
  to #ftco-navbar; scrolling back to 0 removes it.
*/
EOF

git add -A
git commit -q -m "P0 seed: themed shell placeholders (Harshlata)"
git push -u origin task-harshlata-themed-shell || echo "WARNING: could not push task-harshlata-themed-shell (check remote access)."

# -------------------------------------------------------------------
# 3d. TRIPTI — Docker & Testing Infra
# -------------------------------------------------------------------
echo ""
echo "--- [Tripti] Syncing phase0 and creating task-tripti-docker-testing ---"
git checkout phase0
git pull origin phase0 || echo "WARNING: could not pull phase0 (offline/new repo — continuing)."
git checkout -b task-tripti-docker-testing phase0

cat << 'EOF' > requirements.txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Mail==0.9.1
Flask-Limiter==3.8.0
Werkzeug==3.0.4
python-dotenv==1.0.1
gunicorn==22.0.0
psycopg2-binary==2.9.9
email-validator==2.2.0
pytest==8.3.2
pytest-flask==1.3.0
EOF

cat << 'EOF' > .env.example
# Core
SECRET_KEY=change-me-to-a-random-secret
FLASK_ENV=development            # development | testing | production
DATABASE_URL=sqlite:///dev.db    # or postgresql://user:pass@host:5432/codecrews

# Mail
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@codecrews.example
MAIL_SUPPRESS_SEND=False         # set True in docker-compose.test.yml
ADMIN_NOTIFICATION_EMAIL=admin@codecrews.example

# Uploads
UPLOAD_FOLDER=app/static/uploads
MAX_CONTENT_LENGTH=5242880       # 5MB

# Session / security
SESSION_COOKIE_SECURE=False      # True in production
WTF_CSRF_SECRET_KEY=change-me-too

# Seed (used only by seed.py, never read at runtime)
ADMIN_SEED_USERNAME=admin
ADMIN_SEED_PASSWORD=change-me-before-running-seed
EOF

cat << 'EOF' > .gitignore
__pycache__/
*.py[cod]
*.egg-info/
.env
*.db
instance/
.pytest_cache/
.vscode/
.idea/
node_modules/
EOF

cat << 'EOF' > .dockerignore
__pycache__/
*.pyc
*.pyo
.env
.git
.gitignore
.pytest_cache/
*.db
instance/
.vscode/
.idea/
node_modules/
EOF

cat << 'EOF' > Dockerfile
# FILE PURPOSE: Container image for the Flask app (TDR §9).
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. FROM python:3.12-slim.
# 2. Set ENV PYTHONUNBUFFERED=1, PYTHONDONTWRITEBYTECODE=1,
#    PIP_NO_CACHE_DIR=1 so logs stream immediately and pip doesn't cache
#    wheels inside the image layer.
# 3. WORKDIR /code.
# 4. COPY requirements.txt first and RUN pip install -r requirements.txt
#    BEFORE copying the rest of the source, so dependency installs are
#    Docker-layer-cached across rebuilds.
# 5. COPY . . after the pip install step.
# 6. EXPOSE 5000.
# 7. CMD should run Gunicorn in production form:
#    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app — docker-compose.yml overrides
#    this with the Flask dev server for local dev with live reload.
#
# DEBUGGING:
# # RUN echo "[DEBUG] image build reached this layer"
#
# OFFLINE DOCKER TEST CASES:
# - `docker build .` succeeds with zero network access beyond the pip
#   install step.
# - The built image's CMD starts Gunicorn bound to 0.0.0.0:5000.
EOF

cat << 'EOF' > docker-compose.yml
# FILE PURPOSE: Local dev orchestration — web + db services (TDR §2, §9).
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. version: "3.9".
# 2. `web` service: build: . ; command overrides the Dockerfile CMD to run
#    `flask --app wsgi:app run --host=0.0.0.0 --port=5000 --debug` for
#    live reload; bind-mount the repo (`.:/code`); expose port 5000;
#    env_file: .env; environment FLASK_ENV=development; depends_on db.
# 3. `db` service: postgres:16-alpine, present from P0 onward so the
#    M6/P6 swap to Postgres is just a DATABASE_URL change rather than a
#    compose rewrite (TDR §2) — NOT used by default in dev, since
#    DATABASE_URL defaults to a SQLite file per .env.example. Set
#    POSTGRES_USER/PASSWORD/DB to "codecrews", mount a named volume, and
#    expose 5432.
# 4. Declare the named volume used by `db` under a top-level `volumes:` key.
#
# DEBUGGING:
# # command: sh -c "echo '[DEBUG] web service starting' && flask run ..."
#
# OFFLINE DOCKER TEST CASES:
# - `docker-compose config` parses this file without error.
# - `docker-compose up` serves the app at localhost:5000 without the `db`
#   service being reachable (proving the app doesn't hard-require
#   Postgres in dev).
EOF

cat << 'EOF' > docker-compose.test.yml
# FILE PURPOSE: Offline test overlay — mail suppressed, disposable SQLite
# test DB, zero external network calls (TDR §10, Blueprint §2).
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. version: "3.9".
# 2. A single `web` service — deliberately NOT the `db` service from
#    docker-compose.yml, since the suite must run fully offline against a
#    disposable SQLite file, not Postgres.
# 3. build: . ; command: pytest ; bind-mount the repo.
# 4. environment: FLASK_ENV=testing, DATABASE_URL=sqlite:///test.db,
#    MAIL_SUPPRESS_SEND=True, SECRET_KEY and WTF_CSRF_SECRET_KEY test
#    values, SESSION_COOKIE_SECURE=False.
# 5. Add a one-line comment above `services:` documenting the invocation:
#    docker-compose -f docker-compose.test.yml run --rm web pytest
#
# DEBUGGING:
# # environment: - DEBUG_SEED_STAGE=P0
#
# OFFLINE DOCKER TEST CASES:
# - Running the documented invocation exits 0 once tests/test_app_factory.py
#   passes, with no external network access attempted at any point.
EOF

cat << 'EOF' > tests/conftest.py
"""
FILE PURPOSE: Shared pytest fixtures — app/client bound to TestingConfig.

PROMPT FOR LLM IMPLEMENTATION:
1. Before importing the app, set os.environ defaults (via
   os.environ.setdefault) for FLASK_ENV=testing,
   DATABASE_URL=sqlite:///test.db, MAIL_SUPPRESS_SEND=True, SECRET_KEY and
   WTF_CSRF_SECRET_KEY test values — matching docker-compose.test.yml so
   `pytest` behaves identically in and out of Docker.
2. pytest.fixture() named `app`: create_app("testing"), then inside an
   app.app_context() call db.create_all() before yielding the app, and
   db.session.remove() + db.drop_all() after, so every test gets a clean
   database.
3. pytest.fixture() named `client` depending on `app`: returns
   app.test_client().

DEBUGGING:
# print("[DEBUG] conftest — app fixture created")

OFFLINE DOCKER TEST CASES:
- Using the `app` fixture in a trivial test confirms app.testing is True.
- Two tests that each use the `client` fixture don't leak database state
  between each other.
"""
EOF

cat << 'EOF' > tests/test_app_factory.py
"""
FILE PURPOSE: P0 acceptance tests — matches the Master Project
Blueprint's P0 Goal verbatim. Depends on Abhinav's app factory, Piyush's
model stubs, and Harshlata's templates all being merged into the branch
under test.

PROMPT FOR LLM IMPLEMENTATION:
1. test_app_factory_creates_app_in_testing_mode(app): assert app.testing
   is True and app.config["SQLALCHEMY_DATABASE_URI"] starts with
   "sqlite:///test".
2. test_index_returns_200(client): GET "/" returns status_code 200.
3. test_index_contains_loader_navbar_and_footer(client): GET "/" body
   contains 'id="ftco-loader"', 'id="ftco-navbar"', "<footer", and all
   four nav labels ("Home", "Groups", "Our Members", "Request a Project").
4. test_all_stub_models_are_registered(app): within an app context,
   assert {"admin_users","groups","members","projects","blog_posts",
   "contact_messages","project_requests","site_settings"} is a subset of
   db.metadata.tables.keys().

DEBUGGING:
# print("[DEBUG] running P0 acceptance tests")

OFFLINE DOCKER TEST CASES:
- All four tests above pass with zero network access, entirely against
  the SQLite test database created by conftest.py, once all four task
  branches are integrated into phase0.
"""
EOF

git add -A
git commit -q -m "P0 seed: Docker & testing infra placeholders (Tripti)"
git push -u origin task-tripti-docker-testing || echo "WARNING: could not push task-tripti-docker-testing (check remote access)."

# -----------------------------------------------------------------------
# 4. PHASE COMPLETION ECHO
# -----------------------------------------------------------------------

echo ""
echo "====================================================="
echo "Milestone P0 seeded across 4 task branches off phase0:"
echo "  - task-abhinav-app-core          (Abhinav)"
echo "  - task-piyush-data-models        (Piyush)"
echo "  - task-harshlata-themed-shell    (Harshlata)"
echo "  - task-tripti-docker-testing     (Tripti)"
echo ""
echo "NEXT STEPS (each developer — developer_workflow_guide.pdf):"
echo "1. Check out your own branch and feed its seeded files to your LLM"
echo "   (code-implementer skill) to generate the real code."
echo "2. Test locally against phase0's shared skeleton."
echo "3. Commit your implementation in logical chunks on top of the seed commit."
echo "4. Push your branch (already pushed once by this script) with your new commits."
echo "5. Open a PR/MR targeting 'phase0' (NEVER MAIN) and notify Abhishek."
echo ""
echo "NEXT STEPS (Abhishek — Team Lead — team_lead_workflow_guide.pdf):"
echo "- Review each of the four PRs; merge approved branches into phase0 in dependency"
echo "  order (Abhinav's app core and Piyush's models before Harshlata's templates are"
echo "  exercised end-to-end, Tripti's infra last so the full test suite has something"
echo "  complete to run against)."
echo "- Once all four are merged, deploy/test the integrated phase0 branch:"
echo "    docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "- If testing PASSES: git checkout MAIN && git merge phase0, then tag the release."
echo "- If testing FAILS: git branch -D phase0 (and on remote), recreate phase0 from"
echo "  phase0-seed, and have the relevant developer(s) fix + re-PR their task branch"
echo "  (git fetch --prune; git checkout phase0; git pull; git checkout task-...;"
echo "  git rebase phase0 — per developer_workflow_guide.pdf Scenario B)."
echo "- Once phase0 is merged to MAIN: initialize phase1-seed/phase1 and execute P1.sh."
echo "====================================================="