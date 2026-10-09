# MASTER PROJECT BLUEPRINT: CodeCrews (Docker + Git Milestone Workflow)

> Read alongside `ui-ux-design-plan.md` — the directory structure and milestones below map directly onto the screens and flows named there. Both are derived from `project-definition-report.md` (PDR) and `technical-design-report.md` (TDR); this is the finalized version, with every previously-flagged open item resolved.

---

## 1. Unified Directory Structure

```
codecrews/
├── app/
│   ├── __init__.py                  # app factory: registers blueprints + extensions
│   ├── config.py                    # Dev / Test / Prod config classes, reads .env
│   ├── extensions.py                # SQLAlchemy(), LoginManager(), Mail(), CSRFProtect(), Limiter()
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── admin_user.py            # single super-admin row
│   │   ├── group.py
│   │   ├── member.py                # includes resume_pdf (nullable path)
│   │   ├── project.py
│   │   ├── blog_post.py             # group_id NOT NULL — per-group, resolved
│   │   ├── contact_message.py       # group_id NOT NULL — inquiries only, resolved
│   │   ├── project_request.py       # platform-wide "request a project" submissions
│   │   └── site_settings.py         # singleton row: hero/footer/SEO/stat overrides
│   │
│   ├── routes/                      # Flask blueprints
│   │   ├── __init__.py
│   │   ├── public.py                # /, /groups, /group/<slug>, /members
│   │   ├── api.py                   # /api/groups, /api/members
│   │   ├── contact.py               # /group/<slug>/contact
│   │   ├── requests.py              # /request-project
│   │   ├── auth.py                  # /admin/login, /admin/logout, password reset
│   │   └── admin.py                 # /admin/dashboard + all CRUD routes + /admin/project-requests
│   │
│   ├── forms/                       # Flask-WTF, CSRF-protected
│   │   ├── __init__.py
│   │   ├── auth_forms.py            # login + forgot/reset password
│   │   ├── group_forms.py
│   │   ├── member_forms.py          # includes resume_pdf upload field
│   │   ├── project_forms.py
│   │   ├── blog_forms.py
│   │   ├── contact_forms.py
│   │   ├── request_forms.py         # Request-a-Project form
│   │   └── settings_forms.py
│   │
│   ├── services/                    # business logic kept out of routes
│   │   ├── uploads.py               # secure_filename, type/size validation, save path (images, resume PDFs, request attachments)
│   │   ├── mailer.py                # Flask-Mail wrapper for contact/request/password-reset notifications
│   │   └── search.py                # shared filter/query engine backing /api/groups and /api/members (see TDR §3)
│   │
│   ├── templates/
│   │   ├── base.html                # public base layout: nav/footer/loader blocks
│   │   ├── admin/
│   │   │   ├── admin_base.html      # sidebar layout, distinct from public base
│   │   │   ├── login.html
│   │   │   ├── forgot_password.html
│   │   │   ├── reset_password.html
│   │   │   ├── dashboard.html
│   │   │   ├── groups_list.html
│   │   │   ├── group_form.html
│   │   │   ├── members_list.html
│   │   │   ├── member_form.html     # includes resume PDF upload field
│   │   │   ├── projects_list.html
│   │   │   ├── project_form.html
│   │   │   ├── blog_list.html
│   │   │   ├── blog_form.html
│   │   │   ├── messages.html        # inquiries only, no suggestion filter
│   │   │   ├── project_requests.html
│   │   │   └── settings.html
│   │   ├── public/
│   │   │   ├── home.html            # hero + "Request a Project" CTA (no "Suggest your group")
│   │   │   ├── groups_directory.html
│   │   │   ├── group_detail.html    # no bookmark icons; Team cards get resume-download icon
│   │   │   ├── members_directory.html
│   │   │   └── request_project.html
│   │   ├── partials/
│   │   │   ├── navbar.html          # Home → Groups → Our Members → Request a Project
│   │   │   ├── footer.html
│   │   │   ├── loader.html
│   │   │   ├── flash_messages.html
│   │   │   └── _macros.html         # {% macro group_card() / member_card() / project_card() %}
│   │   └── errors/
│   │       ├── 404.html
│   │       └── 500.html
│   │
│   └── static/
│       ├── css/
│       │   ├── style.css            # original theme stylesheet — extended, not replaced
│       │   ├── admin.css            # sidebar/admin-only styles
│       │   ├── bootstrap.min.css
│       │   ├── animate.css
│       │   ├── aos.css
│       │   ├── owl.css / owl.theme.css
│       │   ├── magnific.css
│       │   └── ...                  # rest of the original css/ folder, unchanged
│       ├── js/
│       │   ├── main.js              # original effects init, extended for new sections
│       │   ├── directory-filter.js  # live AJAX search/filter, shared by /groups and /members
│       │   ├── admin.js             # confirm-delete modals, admin-only interactions
│       │   ├── jquery.min.js
│       │   ├── owl.carousel.min.js
│       │   ├── aos.js
│       │   ├── jquery.stellar.min.js
│       │   ├── jquery.magnific-popup.min.js
│       │   ├── jquery.waypoints.min.js
│       │   ├── jquery.animateNumber.min.js
│       │   └── scrollax.min.js      # all original, unchanged
│       ├── images/                  # seeded/placeholder logos, covers, screenshots
│       └── uploads/
│           ├── logos/, covers/, photos/, screenshots/
│           ├── resumes/             # member resume PDFs
│           └── requests/            # request-project attachments
│
├── migrations/                      # Flask-Migrate/Alembic versions
├── tests/
│   ├── conftest.py
│   ├── test_public_routes.py
│   ├── test_admin_auth.py
│   ├── test_group_crud.py
│   ├── test_member_crud.py
│   ├── test_project_crud.py
│   ├── test_blog_crud.py
│   ├── test_search_api.py           # /api/groups + /api/members, incl. SQLite/Postgres dialect branching
│   ├── test_contact_forms.py
│   └── test_project_requests.py
│
├── seed.py                          # creates the single super-admin + sample groups
├── wsgi.py                          # Gunicorn entrypoint
├── requirements.txt
├── .env.example
├── .dockerignore
├── Dockerfile
├── docker-compose.yml               # web + db services
└── docker-compose.test.yml          # offline-safe overlay: mail stubbed, disposable test DB
```

---

## 2. Git + Docker Workflow

- **Branching:** `main` is protected. One branch per milestone, named after its tag below (e.g., `feature/P0-project-setup`, `feature/P3-admin-crud`). A branch merges to `main` only after its own Docker test suite passes — no exceptions for "small" milestones.
- **Offline Docker testing:** `docker-compose.test.yml` runs the `web` and `db` services with `MAIL_SUPPRESS_SEND=True` and a disposable test database, so the full suite runs with zero external network calls (TDR §10).
- **Commit discipline:** commits land only after the milestone's test script passes *inside the container*, not just on the host. Each milestone's final commit message references its tag, e.g. `P2: group directory + search API`.
- **No direct commits to `main`** — PR-style merge even when working solo, so the milestone history stays traceable back to the PDR/TDR.

---

## 3. Milestone → Feature → Commit Map

Ordered so each milestone depends only on what already exists — auth before anything write-protected, read-only browsing before admin write access, and interactive extras (search/filter, members directory) after there's real content to attach them to. These are the same seven milestones the PDR names as M0–M6 (PDR §10); the tag prefix here is `P` to match this document's Git-branch naming convention.

### P0 — Project Setup & Scaffolding
- Flask app factory, config classes, `.env.example`, the full directory tree above created, `Dockerfile` + `docker-compose.yml` + `docker-compose.test.yml`.
- Empty SQLAlchemy models registered (no data yet). `base.html` + partials (navbar/footer/loader) wired up with the original static assets copied in unchanged.
- **Goal:** `docker-compose up` serves a blank but fully-themed shell at `/` — loader spinner, nav, footer all present.

### P1 — Data Models & Admin Auth Shell
- Full SQLAlchemy models (AdminUser, Group, Member, Project, BlogPost, ContactMessage, ProjectRequest, SiteSettings) + first Flask-Migrate migration, matching TDR §4 column-for-column.
- `seed.py` creates the one super-admin account from env-provided credentials.
- `/admin/login`, `/admin/logout`, password-reset request/confirm routes, `@login_required` wiring, `admin_base.html` sidebar shell, empty Dashboard page.
- **Goal:** the admin can log in, out, and reset a forgotten password; no manageable content exists yet.

### P2 — Group Directory (Public, Read-Only)
- Group model wired to `/`, `/groups`, `/group/<slug>` using seeded sample data (no admin write access yet).
- Home hero (Owl Carousel fade + Stellar parallax), platform-wide animated stat counters, directory grid, and full Group Detail page sections (About, Team, Tech Stack, Projects placeholder, Contact form UI — not yet actually sending).
- AOS reveals, sticky-nav-on-scroll, and the burger menu verified working across every new template.
- **Goal:** a visitor can browse seeded groups end-to-end with the original template's full visual effect set intact.

### P3 — Admin CRUD for Groups, Members, Projects
- Full CRUD screens + Flask-WTF/CSRF forms for Groups, Members, and Projects; image upload service (`services/uploads.py`) wired in, including `.pdf`-only validation for the Member resume field; confirm-before-delete modals.
- Public pages now read live database content instead of the P2 seed fixtures.
- **Goal:** the admin can fully manage a group's content and see changes reflected immediately on the public site.

### P4 — Contact, Request-a-Project & Messaging
- `/group/<slug>/contact` POST route; Flask-Mail integration (stubbed in Docker tests per §2); `ContactMessage` persistence (`group_id` NOT NULL); `/admin/messages` inbox with read/delete — inquiries only, no suggestion filter.
- `/request-project` POST route; `ProjectRequest` model + persistence, optional attachment upload, honeypot spam protection; `/admin/project-requests` inbox with status pill (New/In Review/Contacted/Closed) and optional group assignment (no automatic email on assignment — resolved decision, PDR §12).
- **Goal:** the two ways data enters the system without direct admin action — group inquiries and platform-wide project requests — are fully functional.

### P5 — Members Directory, Search/Filter & Blog
- `members_directory.html` + `/members` route + `/api/members`, pulling every member across all groups into one browsable grid; resume-download icon rendered when `resume_pdf` is set; member cards open a Magnific Popup with full bio + resume link + credited projects.
- `directory-filter.js` + `/api/groups` for live search/filter on `/groups`, reused identically on `/members`; `AOS.refresh()` re-triggered on injected results in both cases; `services/search.py` implements the shared filter engine per TDR §3.
- Blog model CRUD (admin) + public per-group blog section on Group Detail pages — confirmed per-group scope, not platform-wide (resolved, PDR §5.7).
- **Goal:** every interactive feature named in the PDR is live.

### P6 — Settings, Polish, Hardening & Deploy
- `/admin/settings` (hero content, footer social links, SEO defaults, optional stats override), dynamic per-group SEO meta tags, themed 404/500 error pages.
- Accessibility pass (aria-labels on icon-only controls, enforced alt-text fields — see Design Plan §8), upload validation/size limits, rate-limiting (Flask-Limiter) and honeypot fields on the public Contact/Request-a-Project forms.
- `requirements.txt` finalized, Gunicorn + WSGI production config, PostgreSQL migration verified against a Postgres container, deployment notes.
- **Goal:** a production-ready build matching every effect and feature named in the PDR/TDR.

---

## Resolved Items (previously flagged as gaps in earlier drafts)

- **Password reset flow** — standard signed email-token reset (request → emailed link → reset form), built in P1. *(Was flagged as unconfirmed; resolved in PDR §12 / TDR §5.)*
- **Blog scope** — per-group, built in P5. *(Was flagged as unconfirmed; resolved in PDR §5.7.)*
- **Project-request assignment notifications** — no automatic email fires when the admin assigns a request to a Group; the admin follows up manually, since Groups have no monitored inbox in the data model. *(Was flagged as unconfirmed; resolved in PDR §12 / TDR §8.1.)*
- **Tag/category taxonomy** — free-form JSON arrays (`tech_tags`, `skill_tags`) at the schema level, forward-compatible with a curated vocabulary later without a migration. The exact curated tag list remains a content decision, not an engineering blocker (TDR §15).
- ~~"Most-saved" analytics~~ — moot; the Saved/Bookmarks feature was removed entirely and is out of scope (PDR §3.2).
