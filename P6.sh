#!/usr/bin/env bash
# P6.sh
# CodeCrews — Milestone P6: Settings, Polish, Hardening & Deploy
#
# Developer: Abhishek (Team Lead and sole developer)
#
# Goal (Master Project Blueprint v2): the core platform (everything before
# the Version 2 coder features) is production-ready: editable site
# settings, per-page SEO, themed error pages, an accessibility pass,
# upload/rate-limit hardening, and a PostgreSQL + Gunicorn deployment
# recipe. P7 and P8 then add coder accounts and the Join/alerts features on
# top of this stable base.
#
# This script contains zero application logic; every file is a heredoc
# holding a PROMPT for an LLM (code-implementer), on ONE task branch.
# requirements.txt is a static manifest and is written with its final
# contents.
#
# Source docs: master-project-blueprint-v2.md §3 (P6), PDR v2 §5.8/§6,
# TDR v2 §6/§9/§12, Design Plan v2 §8.

set -e

echo "====================================================="
echo "CodeCrews — P6: Settings, Polish, Hardening & Deploy"
echo "Developer: Abhishek"
echo "====================================================="

echo ""
echo "--- Phase 6 initialization ---"
git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline — continuing)."

if git show-ref --quiet refs/heads/phase6-seed; then
    echo "phase6-seed already exists — skipping."
else
    git checkout -b phase6-seed MAIN
fi
if git show-ref --quiet refs/heads/phase6; then
    echo "phase6 already exists — skipping."
else
    git checkout -b phase6 phase6-seed
fi
git push -u origin phase6-seed || echo "WARNING: could not push phase6-seed."
git push -u origin phase6 || echo "WARNING: could not push phase6."

git checkout phase6
mkdir -p app/forms app/services app/routes app/templates/admin app/templates/errors
mkdir -p app/templates/partials deploy docs tests
git add -A
git commit -q -m "P6: skeleton verification" || echo "Nothing to commit."
git push origin phase6 || echo "WARNING: could not push phase6."

echo ""
echo "--- Creating task-abhishek-phase6-settings-hardening ---"
git checkout -b task-abhishek-phase6-settings-hardening phase6

cat << 'EOF' > requirements.txt
Flask==3.0.3
Flask-SQLAlchemy==3.1.1
Flask-Migrate==4.0.7
Flask-Login==0.6.3
Flask-WTF==1.2.1
Flask-Mail==0.9.1
Flask-Limiter==3.8.0
Werkzeug==3.0.4
itsdangerous==2.2.0
python-dotenv==1.0.1
gunicorn==22.0.0
psycopg2-binary==2.9.9
email-validator==2.2.0
pytest==8.3.2
pytest-flask==1.3.0
black==24.8.0
flake8==7.1.1
EOF

cat << 'EOF' > app/forms/settings_forms.py
"""
FILE PURPOSE: Admin Site Settings form (PDR §5.8).

PROMPT FOR LLM IMPLEMENTATION:
1. class SettingsForm(FlaskForm): hero_headline (Optional, max 200);
   hero_subheadline (Optional, max 300); hero_cta_text (Optional, max 80);
   hero_images (MultipleFileField, Optional, image extensions);
   github_url, twitter_url, linkedin_url, instagram_url (URLField,
   Optional) for footer_social_links; seo_default_title (max 200);
   seo_default_description (max 300); seo_default_og_image (FileField,
   Optional); override_stats (BooleanField); stats_groups, stats_members,
   stats_projects (IntegerField, Optional, NumberRange min 0); submit.
2. Custom validate(): when override_stats is checked all three numbers are
   required; when unchecked the numbers are ignored and stats_override is
   stored as NULL.
3. P7/P8 add two more fields later (coder_applications_open,
   auto_send_domain_alerts) — leave a comment, do not add them now.

DEBUGGING:
# print(f"[DEBUG] SettingsForm override_stats={self.override_stats.data}")

OFFLINE DOCKER TEST CASES:
- Checking override_stats with a missing number fails validation.
- Unchecking it clears the stored override.
- A bad URL in a social field fails validation.
"""
EOF

cat << 'EOF' > app/routes/admin.py
"""
FILE PURPOSE: Admin blueprint — P6 adds the Settings screen (TDR v2 §5).

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from P3-P5 and the guard.
2. GET/POST /admin/settings: load SiteSettings.get_singleton(); pre-fill
   SettingsForm; on valid POST update the singleton: hero fields; new hero
   images saved with services.uploads (subfolder "covers") and appended to
   hero_images as {"path","alt"} objects (require alt text per image like
   project galleries — add an alt field list); footer_social_links dict
   from the four URL fields; seo defaults (og image via uploads);
   stats_override = {"total_groups", "total_members", "total_projects"} or
   None. Set updated_at, commit, flash "Settings saved.", redirect back.
3. Only one SiteSettings row ever exists — never create a second.
4. Do not add coder or application settings yet (P7/P8).

DEBUGGING:
# print(f"[DEBUG] settings saved override={bool(settings.stats_override)}")

OFFLINE DOCKER TEST CASES:
- Anonymous access redirects to login.
- Saving settings twice leaves exactly one site_settings row.
- Saving with override_stats makes the Home counters show the override.
- A hero image without alt text is rejected.
"""
EOF

cat << 'EOF' > app/templates/admin/settings.html
<!--
FILE PURPOSE: Site Settings page.

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "admin/admin_base.html" %}; title "Settings".
2. Multipart form with csrf and grouped fieldsets: Hero, Footer & Social,
   SEO Defaults, Home Stats Override (checkbox reveals three number
   inputs; works without JS by always showing them with help text).
3. Show current hero images with alt text inputs and remove checkboxes.
4. Leave a clearly marked empty fieldset "Coder & Alerts" with a comment
   (filled in P7/P8).

DEBUGGING:
<!-- <script>console.log("[DEBUG] settings.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The form is multipart with a csrf_token.
- Existing hero images render with their alt inputs.
-->
EOF

cat << 'EOF' > app/services/site_context.py
"""
FILE PURPOSE: Make site-wide settings and stats available to every public
template (footer socials, SEO defaults, Home counters).

PROMPT FOR LLM IMPLEMENTATION:
1. def get_site_settings(): return SiteSettings.query.get(1) or a transient
   (unsaved) SiteSettings with defaults — never create rows during a GET.
2. def platform_stats(): if settings.stats_override is set return those
   three numbers; else count Group, Member, Project rows.
3. def seo_for(page_title=None, description=None, og_image=None): returns a
   dict with title, description, og_image using page values first, then
   SiteSettings defaults, then hard-coded fallbacks ("CodeCrews",
   "A directory of coding teams").
4. Register a context processor in app/__init__.py exposing site_settings
   and seo_for to all templates (see __init__ seed).
5. Cache nothing; a single indexed primary-key lookup per request is fine.

DEBUGGING:
# print(f"[DEBUG] site_context stats override={bool(settings.stats_override)}")

OFFLINE DOCKER TEST CASES:
- With no settings row, get_site_settings() returns defaults and creates
  no database row.
- platform_stats() returns the override when present, else live counts.
- seo_for(page_title="X") prefers "X" over the default title.
"""
EOF

cat << 'EOF' > app/__init__.py
"""
FILE PURPOSE: Application factory — P6 adds the site-context processor,
security headers, and final error handlers.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from earlier milestones.
2. Register a context processor injecting site_settings, platform_stats
   and seo_for (from app/services/site_context.py).
3. After-request hook adding headers: X-Content-Type-Options nosniff,
   X-Frame-Options SAMEORIGIN, Referrer-Policy strict-origin-when-cross-
   origin, and a Content-Security-Policy that allows self plus the CDN
   hosts used by base.html (document the allow-list in a comment; keep
   'unsafe-inline' for styles only).
4. Error handlers: 404 -> errors/404.html (404), 500 -> errors/500.html
   (500, log the exception with traceback at ERROR, rollback the DB
   session), 429 -> a short themed "Too many requests" page. Admin and
   coder areas reuse the same templates.
5. Production only: honor X-Forwarded-* via werkzeug ProxyFix when
   config TRUSTED_PROXY_COUNT > 0 (new env var, default 0).
6. Ensure PRIVATE_UPLOAD_FOLDER exists (kept from P4).

DEBUGGING:
# print("[DEBUG] P6 hooks registered: context processor, headers, error handlers")

OFFLINE DOCKER TEST CASES:
- Every response includes the nosniff and frame headers.
- GET /does-not-exist returns the themed 404 with status 404 and no stack
  trace text.
- A view that raises returns the themed 500 without exposing the
  exception message.
"""
EOF

cat << 'EOF' > app/templates/errors/404.html
<!--
FILE PURPOSE: Themed "page not found".

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; centered large "404", heading "We can't find
   that page", a short sentence, and buttons "Back to Home" and "Browse
   Groups".
2. Same loader, fonts and colors as the public site; no technical detail.

DEBUGGING:
<!-- <script>console.log("[DEBUG] 404 rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The page returns status 404 and contains both buttons.
-->
EOF

cat << 'EOF' > app/templates/errors/500.html
<!--
FILE PURPOSE: Themed "something went wrong".

PROMPT FOR LLM IMPLEMENTATION:
1. Extend base.html if possible, but must not depend on database queries
   (the context processor may be failing): render the minimal layout when
   site settings cannot load.
2. Large "500", heading "Something went wrong on our side", a retry link
   to the Home page.
3. Never print exception text.

DEBUGGING:
<!-- <script>console.log("[DEBUG] 500 rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The page renders even when SiteSettings lookup raises (simulate with a
  monkeypatch).
- No traceback text appears.
-->
EOF

cat << 'EOF' > app/templates/base.html
<!--
FILE PURPOSE: Public base layout — P6 adds SEO meta, social footer data and
accessibility fixes.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the P0 structure and the vendor chain.
2. {% block title %} defaults to seo_for().title; add blocks
   meta_description, og_title, og_description, og_image and render
   <meta name="description">, og:title, og:description, og:image,
   og:type (website), twitter:card (summary_large_image) from them, with
   absolute og:image URLs.
3. Add <link rel="canonical"> using request.base_url.
4. Add a "Skip to main content" link as the first focusable element
   (visually hidden until focused) targeting <main id="main-content">.
5. Add lang="en" (kept) and a meta theme-color of #000000.
6. Make sure the loader has role="status" with a visually hidden "Loading".

DEBUGGING:
<!-- <script>console.log("[DEBUG] base.html P6 SEO/a11y");</script> -->

OFFLINE DOCKER TEST CASES:
- The rendered head contains description, og:title, og:image and
  canonical tags.
- The skip link is the first link in the body.
-->
EOF

cat << 'EOF' > app/templates/public/group_detail.html
<!--
FILE PURPOSE: Group detail — P6 adds dynamic SEO per group.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from P2-P5.
2. Override title, meta_description, og_title, og_description and og_image
   from the group: "{name} — CodeCrews", the tagline or first 150
   characters of the description, and the cover image (absolute URL),
   falling back to the site defaults.
3. Add JSON-LD (<script type="application/ld+json">) with an Organization
   object for the group (name, description, url, logo, sameAs from
   social_links); build it with Jinja's tojson filter, never string
   concatenation.

DEBUGGING:
<!-- <script>console.log("[DEBUG] group SEO for {{ group.slug }}");</script> -->

OFFLINE DOCKER TEST CASES:
- Two different groups produce different <title> and og:title values.
- A group with no cover image falls back to the site default og:image.
- The JSON-LD parses as valid JSON.
-->
EOF

cat << 'EOF' > app/templates/partials/footer.html
<!--
FILE PURPOSE: Footer — P6 reads social links from site settings.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the 4-column layout.
2. The "Follow" column renders one icon link per entry in
   site_settings.footer_social_links, each with an aria-label naming the
   network, target="_blank" and rel="noopener noreferrer".
3. Copyright year from the `now` context variable.

DEBUGGING:
<!-- <script>console.log("[DEBUG] footer P6");</script> -->

OFFLINE DOCKER TEST CASES:
- With settings containing github and twitter, exactly two social icons
  render with aria-labels.
- With no settings the Follow column renders no empty list.
-->
EOF

cat << 'EOF' > app/templates/public/home.html
<!--
FILE PURPOSE: Home — P6 reads hero text, hero images and stats from
settings.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep the P2/P4 structure.
2. Hero slides come from site_settings.hero_images when present (using
   each image's alt text), else the default slides; headline,
   subheadline and CTA text from settings with the P2 defaults as
   fallback.
3. The stat counters use platform_stats() (override-aware).
4. Make the "Request a Project" hero button link to
   url_for('requests.request_project').

DEBUGGING:
<!-- <script>console.log("[DEBUG] home P6 settings-driven");</script> -->

OFFLINE DOCKER TEST CASES:
- Custom headline from settings appears on the page.
- Counters show override values when set.
-->
EOF

cat << 'EOF' > app/static/css/style.css
/*
FILE PURPOSE: Base stylesheet — P6 accessibility and polish pass.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything from P0/P2.
2. Add .skip-link (visually hidden, visible on focus), .sr-only utilities
   if not present, a prefers-reduced-motion media query disabling parallax
   transitions and carousel fades, and consistent focus-visible outlines.
3. Check color contrast: body text #999 on #000 passes AA for normal
   text; raise any smaller or dimmer text to at least #b3b3b3 and note it
   in a comment.
4. Print styles are not required.

DEBUGGING:
/* console.log("[DEBUG] style.css P6"); */

OFFLINE DOCKER TEST CASES:
- .skip-link and prefers-reduced-motion rules exist.
- Valid CSS.
*/
EOF

cat << 'EOF' > wsgi.py
"""
FILE PURPOSE: Production entrypoint — P6 finalizes it for Gunicorn.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep load_dotenv() before importing the factory and the `app` object.
2. Default FLASK_ENV to "production" when unset in this file only (dev
   uses `flask run`).
3. Do not call app.run() unless __main__.

DEBUGGING:
# print("[DEBUG] wsgi.py loaded for Gunicorn")

OFFLINE DOCKER TEST CASES:
- `gunicorn -w 1 -b 127.0.0.1:8000 wsgi:app` starts and GET /health-less
  home returns 200 in an integration smoke test.
"""
EOF

cat << 'EOF' > Dockerfile
# FILE PURPOSE: Production-ready image — P6 finalization.
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. Keep the P0 base (python:3.12-slim, env vars, requirements first).
# 2. Create a non-root user "app" and run the container as that user;
#    chown the instance/ folder so private uploads are writable.
# 3. HEALTHCHECK using python -c to request http://127.0.0.1:5000/ and exit
#    non-zero on failure.
# 4. CMD stays: gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
#
# DEBUGGING:
# # RUN echo "[DEBUG] switching to non-root user"
#
# OFFLINE DOCKER TEST CASES:
# - The built image runs as a non-root user (`id -u` is not 0).
# - HEALTHCHECK reports healthy once the app is up.
EOF

cat << 'EOF' > docker-compose.prod.yml
# FILE PURPOSE: Production-style compose file: web (Gunicorn) + db
# (PostgreSQL) + reverse proxy.
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. Services: web (build ., env_file .env, no bind mount, volume for
#    instance/private_uploads, depends_on db with a healthcheck), db
#    (postgres:16-alpine with POSTGRES_* from env, named volume), proxy
#    (nginx:alpine mounting deploy/nginx.conf.example read-only, ports
#    80/443).
# 2. DATABASE_URL points at the db service; SESSION_COOKIE_SECURE=True;
#    FLASK_ENV=production.
# 3. The proxy serves /static/ from a read-only volume of app/static but
#    NEVER mounts instance/private_uploads.
#
# DEBUGGING:
# # command: sh -c "echo '[DEBUG] prod web starting' && gunicorn ..."
#
# OFFLINE DOCKER TEST CASES:
# - `docker-compose -f docker-compose.prod.yml config` parses.
# - A GET to /static/../instance/private_uploads is refused by the proxy.
EOF

cat << 'EOF' > deploy/nginx.conf.example
# FILE PURPOSE: Example reverse-proxy config for production.
#
# PROMPT FOR LLM IMPLEMENTATION:
# 1. server block listening on 80 redirecting to 443; TLS block with
#    placeholders for certificate paths.
# 2. location /static/ -> alias to the mounted app/static folder with
#    long cache headers (30d) but only for that folder.
# 3. location / -> proxy_pass http://web:5000 with X-Forwarded-For,
#    X-Forwarded-Proto and Host headers.
# 4. client_max_body_size 6m (slightly above the 5 MB app limit).
# 5. Explicit deny for any path containing "private_uploads".
#
# DEBUGGING:
# # add_header X-Debug-Upstream $upstream_addr;
#
# OFFLINE DOCKER TEST CASES:
# - `nginx -t` passes with real certificate paths substituted.
# - Requests above 6 MB are rejected by nginx before reaching Flask.
EOF

cat << 'EOF' > docs/DEPLOYMENT.md
<!--
FILE PURPOSE: Deployment notes for production.

PROMPT FOR LLM IMPLEMENTATION:
1. Sections: Prerequisites; First deploy (env file, build, `flask db
   upgrade`, `python seed.py`); Moving from SQLite to PostgreSQL (dump,
   new DATABASE_URL, run migrations on an empty Postgres, test with the
   Postgres container before go-live); Backups (database dump command and
   the two upload folders: public static/uploads and private_uploads);
   Rotating secrets (SECRET_KEY, SMTP password, and REMINDER that the
   legacy server.js Gmail credentials must be rotated); Scheduled tasks
   (host cron examples — the purge commands arrive in P8); Rollback.
2. Commands only in fenced blocks; no secrets.

DEBUGGING:
<!-- Note: keep a "Troubleshooting" section with log locations. -->

OFFLINE DOCKER TEST CASES:
- Following the document top to bottom on a fresh machine reaches a
  working site (manual checklist at the end of the file).
-->
EOF

cat << 'EOF' > tests/test_settings.py
"""
FILE PURPOSE: P6 tests — Site Settings.

PROMPT FOR LLM IMPLEMENTATION:
1. test_settings_requires_admin.
2. test_save_settings_updates_singleton_only_one_row.
3. test_stats_override_changes_home_counters_and_unset_restores_live.
4. test_hero_image_requires_alt.
5. test_footer_social_links_render_with_aria_labels.
6. test_seo_defaults_used_when_page_has_none.

DEBUGGING:
# print("[DEBUG] running settings tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

cat << 'EOF' > tests/test_errors_and_headers.py
"""
FILE PURPOSE: P6 tests — error pages and security headers.

PROMPT FOR LLM IMPLEMENTATION:
1. test_404_is_themed_and_has_no_traceback.
2. test_500_is_themed_and_hides_exception_text (register a test route that
   raises).
3. test_429_page_for_rate_limited_request.
4. test_security_headers_present_on_every_response.
5. test_group_page_has_unique_seo_tags_and_valid_jsonld.

DEBUGGING:
# print("[DEBUG] running error/header tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

cat << 'EOF' > tests/test_accessibility.py
"""
FILE PURPOSE: P6 tests — automated accessibility basics (PDR §6, Design
Plan §8).

PROMPT FOR LLM IMPLEMENTATION:
1. For Home, /groups, a group page, /members, /request-project, the admin
   login and the admin groups list: parse the HTML and assert every <img>
   has a non-empty alt (decorative images use alt="" explicitly and are
   whitelisted in the test).
2. Every button or link that contains only an icon has an aria-label.
3. Every form control has an associated label or aria-label.
4. A skip link exists on public pages; <main id="main-content"> exists.
5. The page <title> is unique per page type.

DEBUGGING:
# print("[DEBUG] running accessibility tests")

OFFLINE DOCKER TEST CASES:
- All pass offline using BeautifulSoup-free parsing (html.parser from the
  standard library) so no new dependency is needed.
"""
EOF

cat << 'EOF' > tests/test_hardening.py
"""
FILE PURPOSE: P6 tests — upload and rate-limit hardening across the app.

PROMPT FOR LLM IMPLEMENTATION:
1. test_login_rate_limit: the 11th admin login attempt in a minute returns
   429 (limiter enabled via test config).
2. test_public_form_rate_limits_hold (contact and request-project).
3. test_oversized_request_returns_friendly_redirect.
4. test_disguised_upload_rejected_on_every_upload_endpoint.
5. test_private_folder_not_served_by_static_route.
6. test_cookies_httponly_and_samesite_lax; Secure flag set under the
   production config.
7. test_csrf_required_when_enabled: with WTF_CSRF_ENABLED=True a POST
   without token is rejected on one public and one admin form.

DEBUGGING:
# print("[DEBUG] running hardening tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

git add -A
git commit -q -m "P6 seed: settings, polish, hardening and deploy placeholders (Abhishek)"
git push -u origin task-abhishek-phase6-settings-hardening || echo "WARNING: could not push task-abhishek-phase6-settings-hardening."

echo ""
echo "====================================================="
echo "Milestone P6 Seeded Successfully!"
echo "NEXT STEPS (Abhishek):"
echo "1. Feed the seeded files to your LLM (code-implementer) to generate the code."
echo "2. Run: docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "3. Verify the Postgres path: docker-compose -f docker-compose.prod.yml up -d db && run migrations against it."
echo "4. Commit in logical chunks, open a PR into 'phase6', review and merge."
echo "5. If tests pass: git checkout MAIN && git merge phase6, then tag the release (v1-core)."
echo "6. Execute P7.sh."
echo "====================================================="
