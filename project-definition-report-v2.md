# PROJECT DEFINITION REPORT: CodeCrews — Version 2

*(CodeCrews is a placeholder project name carried over from the source planning docs — swap in real branding before build.)*

> **Version 2 change summary.** This revision supersedes the earlier PDR. It adds two capabilities and leaves everything else (Groups, Members directory, Contact, Request-a-Project, Blog, Settings) intact:
> 1. **Coder accounts** — the super-admin can create login accounts for the coders who belong to a group. Coders manage their own profile and their group's projects, but are walled off from every visitor conversation and lead. The super-admin alone decides which coder may see which project request, and can revoke that access, or the account itself, at any time (§5.9, §5.10, §11).
> 2. **"Join as a Coder" applications** — a visitor can apply to join the platform's coder pool as a perk; if a project in their domain arrives, they are told (§5.11, §5.12), via dedicated pages.
>
> The earlier "v2" label inside the previous PDR referred to a pre-release spec revision (bookmarks and "Suggest a Group" removal). Those removals stay in force. Assumptions made while writing this version are listed in §12 under *Resolved decisions for Version 2* so they can be corrected.

## 1. Executive Summary

CodeCrews is a public directory platform for coding teams — a "Product Hunt for dev teams." Instead of one person's portfolio, the platform hosts many coding groups, each with its own themed profile page showing their members, tech stack, and project portfolio, all rendered from a shared database instead of hand-edited HTML. Visitors browse anonymously and have exactly two ways to convert into a lead: contacting a specific group directly, or submitting a platform-wide "Request a Project" brief when they want custom work built but don't know which group to ask. A platform-wide Members directory lets visitors browse individual contributors across every group and download a member's resume/CV when one is on file.

**Version 2 introduces a three-tier trust model.** One **super-admin** still controls every piece of content and is the only person who ever sees visitor conversations — contact messages, project requests, who asked for a call, and who discussed what. Registered **coders** (members of a group) now receive logins, created only by the super-admin, so they can keep their own profile and their group's projects current without going through the admin. Coders see *nothing* about visitor communication unless the super-admin deliberately grants them access to one specific project request, and that grant can be revoked at any moment. Separately, any visitor can **apply to join as a coder** from a dedicated page; applicants are not given accounts, but are told when a project in their chosen domain arrives, as a perk of being on the platform's radar.

There is still no public sign-up that creates a login: accounts of every kind are created by the super-admin. The product's visual identity — full-screen loader, parallax hero, Owl Carousel sliders, AOS scroll reveals, animated counters, Magnific Popup galleries — is inherited from an existing single-person "Creative Coder" portfolio template and extended to every new public screen. The admin and coder areas are deliberately plain, dense utility shells.

## 2. Project Objectives

### Primary Objectives
- Give every coding group a consistent, animated, on-brand profile page without any group needing to touch code or design.
- Let one super-admin manage the entire platform — groups, rosters, projects, blog posts, inbound leads, coder accounts, and coder access — from a single control panel.
- Convert anonymous visitor traffic into qualified leads through two zero-friction channels: a per-group contact form and a platform-wide Request-a-Project form.
- **(New)** Let coders keep their own profile and their group's projects up to date themselves, via a separate coder portal, without ever exposing visitor communication to them.
- **(New)** Keep a strict confidentiality wall: only the super-admin sees who contacted whom, who requested a call, and what was discussed. Coders see a project request only when the super-admin grants it, and only the fields the grant allows. Access is revocable instantly.
- **(New)** Grow a pool of interested coders by letting visitors apply to join, and alert them (without revealing any visitor identity) when a project matching their domain arrives.
- Make individual contributors discoverable platform-wide via a searchable Members directory, including resume/CV downloads.
- Preserve the original template's full animation/interaction language across every public screen.

### Secondary Objectives
- Optional per-group blog/dev-log (confirmed in-scope; §5.7).
- Dynamic, per-group SEO metadata so group pages are independently discoverable/shareable.
- Forward-compatible tag/category data model so filtering can evolve from free-form tags into a curated taxonomy without a schema change (§12). The same tags drive coder-application domain matching.
- Not built in this phase but designed for: swapping SQLite for PostgreSQL in production; per-coder granular permissions beyond the fixed coder role; coder-to-super-admin in-app messaging.

## 3. Scope of Work

### In-Scope
- **Public site:** Landing page; Groups directory with live search/tag filtering and pagination; Group Detail pages; platform-wide Members directory (`/members`); Request-a-Project form (`/request-project`); **new:** "Join as a Coder" application page (`/join`), email-verification and thank-you pages, and one-click alert unsubscribe page.
- **Lead capture:** Per-group Contact form (`ContactMessage`) and platform-wide Request-a-Project form (`ProjectRequest`), both emailed to the admin, with the admin-side status workflow (New/In Review/Contacted/Closed) and optional assignment to a Group.
- **Admin control panel (super-admin only):** Full CRUD for Groups, Members (incl. resume upload), Projects, Blog; Messages inbox; Project Requests inbox with status, assignment, internal notes, domain tags; Site Settings. **New:** Coder Accounts management (create, edit, revoke, reinstate, resend invite), per-request Access Grants (grant, revoke), Coder Applications inbox (review, approve, reject, convert to coder account), Domain Alerts (preview and send), and an audit log of all of these actions.
- **Coder portal (new, `/coder/*`):** Separate login; dashboard; own profile editing (bio, skills, social links, photo, resume); create/edit projects for the coder's own group (with gallery uploads); an **Opportunities** page listing only the project requests the super-admin has granted to that coder and not revoked.
- **Platform mechanics:** File upload handling (images + PDFs); responsive Bootstrap 4; themed 404/500 pages; `.env` config; Dockerized dev/test with offline tests; pagination on all list views; WCAG 2.1 AA basics; CSRF on every form.

### Out-of-Scope
- **Self-service account creation of any kind** — visitors and applicants cannot create logins. Applying to join as a coder creates an *application record*, not an account. Only the super-admin creates user accounts.
- **Chat / messaging between visitors, coders, and the admin** — there is no in-app chat or discussion thread feature. "Conversations" with visitors happen outside the platform (email/phone) and are managed by the super-admin; the platform only stores the lead and the admin's private notes.
- **Saved / Bookmarks** and **"Suggest a Group"** — remain removed.
- **Payments / marketplace transactions** — no payment gateway.
- **Granular per-coder permission editor** — all coders share one fixed coder role; access differences are expressed only through per-request grants.
- **Coders deleting projects, editing group-level fields, managing blog posts, or managing other coders** — admin-only in this phase (see §12 decisions).
- **Native mobile apps**, **real-time features** (websockets, live notifications), **multi-language** — unchanged.

## 4. User Personas

### Anonymous Visitor / Prospective Client
Arrives with general curiosity or a specific need ("I want to hire a team"). Browses Groups or Members, uses live filters, opens a profile popup or group page, and converts by contacting a group or submitting a project request. Has no account and no persistent state. Visitors can rely on one thing: **only the super-admin** will ever see their contact details and project brief unless the super-admin decides to share the brief (not their identity, by default) with a specific coder.

### Group Member (Represented Profile)
A person displayed publicly on their group's page and the Members directory. Before Version 2 they had no login. In Version 2 a member **may** be upgraded to a Coder by the super-admin. Members without a coder account continue to be maintained entirely by the super-admin.

### Coder (new)
A registered member of a group who has been given a login by the super-admin. Needs to keep their own profile, resume, and their group's project showcase accurate and current without bothering the admin. Can see a project request only when the super-admin has granted it to them. Never sees the Messages inbox, the Project Requests inbox, internal notes, requester identity (unless the grant explicitly shares it), other coders' accounts, or settings. Understands their account can be revoked at any time.

### Coder Applicant (new)
A visitor (developer, freelancer, student) who wants to be on the platform's radar. Submits the Join form with a domain of interest. Has no login; receives an email verification, and later receives domain alerts such as "A new Web App project in the Fintech domain has arrived." Can express interest from the alert or unsubscribe with one click. May be promoted by the super-admin into a Member and Coder.

### Super-Admin
The single operator of the platform. Creates and maintains every Group, Member, Project, Blog post, Coder account, and Access Grant; reviews every Contact message, Project Request, and Coder Application; decides who may see which request and for how long; sends domain alerts; and maintains platform settings. The only role with access to visitor communication and the only role that can create or revoke accounts.

## 5. Functional Requirements

### 5.1 Admin Control Panel (Foundational — Priority #1)
A sidebar control panel (Dashboard, Groups, Members, Projects, Blog, Messages, Project Requests, **Coders**, **Coder Applications**, **Audit Log**, Settings, Logout), visually distinct from the public site. Every list screen supports pagination. Every create/edit form is CSRF-protected and server-side validated with inline errors. Every destructive or access-changing action (delete, revoke) requires a confirm modal. Flash alerts report success/error. The Dashboard now also shows counts for active coders, pending applications, and open grants.

### 5.2 Authentication & Role Access
Three authenticated-or-anonymous tiers exist: Visitor (anonymous), Coder, Super-Admin.
- **Super-admin:** exactly one `AdminUser` row ever exists, seeded via `seed.py`, never via a UI form. Login at `/admin/login`. Every `/admin/*` route requires the super-admin role.
- **Coder:** accounts exist only because the super-admin created them. Login at `/coder/login` (separate themed form). Every `/coder/*` route requires an *active* coder. A coder session can never reach `/admin/*`, and the admin session can never be mistaken for a coder one.
- **Invite & password flow:** creating a coder emails a signed, time-limited invite link (72 hours) so the coder sets their own password; the super-admin never sees or sets coder passwords. Forgotten passwords use the same signed-token reset flow as the admin.
- **Revocation is immediate:** account status is checked on every coder request, not only at login, so revoking a coder ends their access at the next click even with an open session.
- Failed-login attempts are rate limited on both login forms.

### 5.3 Group Directory & Profiles
Unchanged from the prior PDR: Home (hero slider, platform stats, Featured Groups carousel, directory teaser, Request-a-Project CTA); `/groups` directory; `/group/<slug>` page with hero, About, Team, Tech Stack, Projects, optional Blog, stat strip, and Contact form. Version 2 adds one footer-level call to action ("Join as a Coder") on the Home page and in the footer.

### 5.4 Members Directory & Resume Management
Unchanged: `/members` with live filtering, resume download button (rendered only when a resume exists, with an `aria-label`), profile popup with credited projects. Resume upload moves from admin-only to admin **or** the member's own coder account (own profile only).

### 5.5 Lead Capture: Contact & Request-a-Project
Unchanged in behavior: Group Contact (`ContactMessage`) and Request a Project (`ProjectRequest`) with honeypot, CSRF, rate limits, emailed to the admin. Version 2 adds, on the admin side of a Project Request: **internal notes** (private to the super-admin), **domain tags** (prefilled from project type, editable), and the **Access Grants** panel (§5.9). These are visible to no one except the super-admin.

### 5.6 Search & Live Filtering
Unchanged: shared keyup-triggered AJAX pattern for `/api/groups` and `/api/members`.

### 5.7 Blog / Dev-log (per-group)
Unchanged: per-group, admin-only CRUD, rendered on the group page.

### 5.8 Site Settings & SEO Management
Unchanged, plus two new settings: (a) *Coder applications open* toggle (hide/disable `/join` when off), and (b) *Auto-send domain alerts* toggle (default **off**: the super-admin sends alerts manually).

### 5.9 Coder Accounts & Access Grants (new)
**Creating a coder.** In `/admin/coders/new` the super-admin picks an existing Member (or creates one inline, attached to a Group), enters the coder's email and username, and submits. The system sends the invite email. One member can have at most one coder account. The coder inherits their group from the linked Member.

**What a coder can do.**
- Edit their own Member profile: role, bio, skill tags, social links, photo, resume PDF. Name, group, and display order stay admin-controlled. (Photo alt text is generated from the member's name.)
- Create and edit Projects belonging to **their own group only**: title, description, tech tags, URLs, status, gallery images (alt text required). New projects created by a coder are saved as visible immediately unless the super-admin has set the site to require approval (see §12 decision D5; default: visible immediately, with the creator recorded in the audit log, and the super-admin can unpublish at any time). A coder cannot toggle `featured` and cannot delete projects.
- View the **Opportunities** page: only project requests currently granted to them.

**What a coder can never do or see.** Messages inbox; Project Requests inbox; any request not granted to them; admin internal notes; the identity of anyone who contacted the platform or asked for a call (unless a grant says otherwise); other coders' data; settings; any other group's projects.

**Access Grants.** On any Project Request the super-admin can grant it to one or more active coders. A grant has:
- *Scope:* **Brief only** (default) — project type, domain tags, budget range, timeline, description, attachment; or **Brief + requester contact** — adds requester name, email, and company. The super-admin must tick the second option deliberately.
- *Optional expiry date.*
- *Revocation:* the super-admin can revoke a grant at any time; it takes effect on the coder's next request. Revoked grants stay visible in the admin's history.
- The coder receives a "New opportunity assigned to you" email (without any requester details) when a grant is created.
- Internal notes and the status history are never part of any grant.

**Revoking and reinstating a coder.** The super-admin can revoke any coder account at any time. Revocation ends their session, blocks login, and revokes all of their open grants. Their Member profile and Projects stay published (content is the group's, not the coder's). The super-admin can reinstate the account later; reinstated coders start with no grants.

**Editing audit.** Every coder edit to a project or profile, and every admin coder/grant action, is written to the audit log (who, what, when).

### 5.10 Coder Portal (new)
`/coder/*` is a dedicated shell, visually closer to the admin than the marketing site: Dashboard (welcome, your group, quick links, count of granted opportunities), My Profile, My Group's Projects (list/create/edit), Opportunities (list + detail of granted requests only), Logout. Every list paginates. Forms are CSRF-protected with inline errors and flash alerts. When a coder's account or grant is revoked mid-session, they land on a plain "Your access has changed" page rather than an error trace.

### 5.11 Join as a Coder — Applications (new)
Dedicated public pages:
- `/join` — the application form: name, email, domains of interest (multi-select of project types: Web App, Mobile App, Desktop Software, API/Backend, Other, **plus** free-form domain/skill tags), short headline, GitHub/portfolio URL (optional), message (optional), optional resume PDF (≤5 MB), explicit consent checkbox for email alerts, honeypot field.
- `/join/thanks` — confirmation telling the visitor to check their email.
- `/join/verify/<token>` — email verification (signed, 7-day token). Alerts are only ever sent to verified addresses.
- `/join/unsubscribe/<token>` — one-click unsubscribe, no login needed.

Business rules: one active application per email address (re-applying updates the existing one); applying does not create a login; the applicant is told plainly that alerts are an opt-in perk and joining is subject to admin review. Admin side (`/admin/coder-applications`): list with status pill (Pending / Approved / Rejected / Converted), detail view, actions — Approve (keeps them in the alert pool), Reject (removes them from the alert pool, silent by default), **Convert to coder** (creates a Member + Coder account via the invite flow, attaching a Group chosen by the admin).

### 5.12 Domain Alerts (new)
When a Project Request arrives, the super-admin can open **Notify matching applicants**. The system shows a preview of the matched, verified, opted-in applicants (matching = overlap between the request's domain tags/project type and the applicant's domains). The admin writes a short **anonymized summary** (prefilled with project type and domain tags; the description is *not* included), reviews the recipient count, and sends. Each alert email contains only that summary plus two links: **I'm interested** and **Unsubscribe**. Alerts never include requester name, email, company, budget, or a link to the request. An applicant who clicks *I'm interested* is flagged on the admin's Notify screen, so the admin can follow up by converting them to a coder and granting the request. No applicant is ever emailed twice for the same request. If the *Auto-send domain alerts* setting is enabled, the system sends a default summary automatically when the request is submitted (default off).

### Ticketing / Support
Still no support-ticket system. Visitor-to-admin communication is only the Contact and Request-a-Project flows. There is no coder-to-admin messaging in this phase; coders contact the super-admin by ordinary means outside the platform.

### Password Reset & Notifications
Admin and coder password recovery both use signed, time-limited tokens (§5.2). Notifications (Flask-Mail): New Contact Message, New Project Request, Password Reset Requested (admin and coder variants), **Coder Invite**, **Opportunity Assigned**, **Application Verification**, **New Coder Application** (to admin), **Domain Alert**. Assignment of a request to a *Group* still sends no email (groups have no inbox); a grant to a *Coder* does, since coders have an email on file.

## 6. Non-Functional Requirements

- **Security:** CSRF on every form; salted password hashing; session cookies `HttpOnly`/`Secure` (production); secrets in `.env`; the legacy template's committed Gmail credentials must be rotated. **New:** role checks are enforced server-side on every route and on every query (a coder's queries are always scoped by their own `group_id` or by active grants); revocation is evaluated per request; coder-visible request payloads are built from an allow-list serializer so confidential fields cannot leak by accident; applicant alert emails contain no requester data.
- **Performance:** < 300 ms p95 for public read routes, the two `/api/*` endpoints, and the coder portal list pages.
- **Uptime:** 99.5 % in production.
- **Accessibility:** WCAG 2.1 AA; alt text required on every image field including coder-uploaded ones; `aria-label`s on icon-only controls.
- **Responsiveness:** Bootstrap 4 breakpoints unchanged.
- **Privacy:** applicant and coder personal data is collected only for stated purposes; unsubscribe is one click; deleting an applicant removes their stored resume file.
- **Testability:** all tests run offline in Docker, mail stubbed. **New:** a dedicated authorization test matrix (§10 of the TDR) proves a coder cannot reach any visitor-communication data.

## 7. System Architecture (Overview)

Still a **monolithic Flask application**, now organized into blueprints: public, api, contact, requests, **join**, auth (admin), **coder_auth**, admin, **coder**. A monolith remains appropriate: one operator, moderate traffic, no independently scaling component. Server-rendered Jinja2 with progressive-enhancement JavaScript; no SPA framework. Dockerized with Gunicorn and a reverse proxy in production. SQLite in dev/test; PostgreSQL in production via Flask-Migrate. Authorization is centralized in role decorators and a small access-policy service so the "who may see which request" rule lives in one place, not scattered across routes.

## 8. Database Schema (Summary)

Carried over: `Group` central; has many `Member`, `Project`, `BlogPost`, `ContactMessage`; optional target of `ProjectRequest.assigned_group_id`. `AdminUser` and `SiteSettings` are singletons.

New in Version 2:
- **`CoderUser`** — a login account linked one-to-one to a `Member` (the group is derived through the member). Has status (active/revoked), invite and revocation metadata.
- **`RequestAccessGrant`** — links one `ProjectRequest` to one `CoderUser` with a scope (brief-only or brief-plus-contact), optional expiry, and grant/revoke timestamps. This table is the *only* path by which a coder can ever see a request.
- **`CoderApplication`** — a visitor's application: contact email, domains (project types and tags), consent, verification state, status, and an optional link to the `CoderUser` they were converted into.
- **`DomainAlert`** and **`DomainAlertDelivery`** — a record of each alert batch (per request, with the admin-written anonymized summary) and one row per applicant emailed, including whether they clicked *I'm interested*. Prevents duplicate emails.
- **`AuditLog`** — append-only record of admin and coder actions on accounts, grants, applications, alerts, and coder-edited content.
- Changes to existing tables: `ProjectRequest` gains `domain_tags` and `internal_notes`; `Project` gains `created_by_coder_id` and `last_edited_by_coder_id` (nullable); `Member` itself is unchanged (the login lives in `CoderUser`, so a member's public data never carries credentials); `SiteSettings` gains `coder_applications_open` and `auto_send_domain_alerts`.

Full column-level definitions are in the companion Technical Design Report.

## 9. Technology Stack

- **Backend:** Python, Flask (blueprint-organized monolith)
- **Templating:** Jinja2 (`base.html` for public; `admin_base.html` for admin; **`coder_base.html`** for the coder portal; macros for cards)
- **Database / ORM:** SQLAlchemy (SQLite dev/test, PostgreSQL production) + Flask-Migrate
- **Auth:** Flask-Login with two user classes (`AdminUser`, `CoderUser`) behind role decorators; Werkzeug password hashing; `itsdangerous` signed tokens for invites, resets, email verification, unsubscribe
- **Forms / CSRF:** Flask-WTF
- **Mail:** Flask-Mail (SMTP), stubbed in tests
- **Rate limiting:** Flask-Limiter (login forms, public forms, `/join`)
- **Frontend:** Bootstrap 4, jQuery, AOS, Owl Carousel, Stellar.js, Magnific Popup, Waypoints + jquery.animateNumber, Scrollax (unchanged)
- **File uploads:** Werkzeug `secure_filename`. Public media (logos, covers, photos, screenshots, member resumes) under `static/uploads/`. **Request attachments and applicant resumes are confidential and stored in a private folder outside the static tree**, served only through authenticated admin (or, for granted requests, coder) download routes.
- **DevOps:** Docker + `docker-compose`, Gunicorn, `.env` / `python-dotenv`

## 10. Development Phases & Timeline

*(M0–M6 are unchanged and map to the already-seeded P0–P6 milestones. Version 2 adds two milestones, M7 and M8, so work already scripted for P0/P1 is not disturbed.)*

| Milestone | Goal | Key Deliverables |
|---|---|---|
| **M0 — Project Setup & Scaffolding** | Blank themed shell at `/` | App factory, config, Docker, base layout |
| **M1 — Data Models & Admin Auth Shell** | Admin can log in/out | Models + migration, `seed.py`, admin login/reset, admin shell |
| **M2 — Group Directory (Public, Read-Only)** | Browse seeded groups | `/`, `/groups`, `/group/<slug>` |
| **M3 — Admin CRUD for Groups, Members, Projects** | Admin manages content | CRUD, uploads, confirm-delete |
| **M4 — Contact, Request-a-Project & Messaging** | Both lead channels live | Contact + Request forms, admin inboxes |
| **M5 — Members Directory, Search/Filter & Blog** | Interactive features live | `/members`, `/api/*`, blog |
| **M6 — Settings, Polish, Hardening & Deploy** | Production-ready core | Settings, SEO, error pages, a11y, deploy |
| **M7 — Coder Accounts, Portal & Access Control (new)** | Coders work safely inside a wall | `CoderUser` + `RequestAccessGrant` + `AuditLog` models and migration; role decorators (`super_admin_required`, `coder_required`) retrofitted across all existing admin routes; admin Coders CRUD with invite/revoke/reinstate; coder login/reset; coder portal (dashboard, profile, group projects, Opportunities); per-request grant/revoke UI; authorization test matrix |
| **M8 — Join as a Coder & Domain Alerts (new)** | Applicant pool and perk alerts | `CoderApplication`, `DomainAlert`, `DomainAlertDelivery`; `/join` pages with verification and unsubscribe; admin Coder Applications inbox with approve/reject/convert; Notify-matching-applicants screen; settings toggles; hardening and a11y pass for new screens |

## 11. Admin & Permission Model

Three effective roles: **Visitor** (anonymous), **Coder** (account created by super-admin), **Super-Admin** (single). Coder rows marked *scoped* are limited to the coder's own group or to active grants.

| Permission / Resource | Visitor | Coder | Super-Admin |
|---|---|---|---|
| View public pages (Home, Groups, Group Detail, Members) | ✅ | ✅ | ✅ |
| Submit Group Contact form / Request-a-Project form | ✅ write-only | — | — |
| Submit Join-as-a-Coder application, verify email, unsubscribe | ✅ | — | — |
| Log into `/admin/*` | ❌ | ❌ | ✅ |
| Log into `/coder/*` | ❌ | ✅ (active only) | ❌ |
| Create / revoke / reinstate coder accounts | ❌ | ❌ | ✅ |
| Manage Groups (CRUD) | ❌ | ❌ | ✅ |
| Manage Members (CRUD) | ❌ | Edit **own** profile and resume only | ✅ |
| Create / edit Projects | ❌ | **Own group only** (no featured flag) | ✅ |
| Delete Projects | ❌ | ❌ | ✅ |
| Manage Blog posts | ❌ | ❌ | ✅ |
| View Messages inbox | ❌ | ❌ | ✅ |
| View Project Requests inbox, internal notes, status history | ❌ | ❌ | ✅ |
| View a specific Project Request | ❌ | Only if actively granted, only the granted fields | ✅ (all) |
| Grant / revoke access to a Project Request | ❌ | ❌ | ✅ |
| View / action Coder Applications | ❌ | ❌ | ✅ |
| Send Domain Alerts | ❌ | ❌ | ✅ |
| View Audit Log | ❌ | ❌ | ✅ |
| Edit Site Settings | ❌ | ❌ | ✅ |

## 12. Risk Analysis & Mitigation

| Risk | Mitigation |
|---|---|
| Single super-admin credential compromise grants total control | Strong salted hashing, rate-limited login, signed time-limited reset tokens, secrets rotation |
| **A coder sees visitor data they should not (confidentiality breach)** | Coders have no route to the inboxes; request access exists only through `RequestAccessGrant`; the coder-facing request view uses an allow-list serializer; every coder query is filtered by active grant; an authorization test matrix is a merge gate for M7 |
| **Revoked coder keeps working through an open session** | Account and grant status are re-checked on every request; revocation also invalidates the session; revoked grants return a neutral "access changed" page |
| **A coder edits or damages their group's content** | Coders cannot delete or feature projects; all coder edits are written to the audit log with before/after summary; the super-admin can unpublish or edit any project and revoke the account instantly |
| **Privilege escalation between coder and admin areas** | Separate login routes, separate user classes with prefixed session IDs, `super_admin_required` / `coder_required` decorators, and a test that every `/admin/*` route returns 302/403 to a coder session |
| Coder compromise (stolen coder password) | Rate-limited login, invite/reset by signed token only, no admin power, grants are time-boxable, revocation is one click |
| **Domain alerts leak requester identity or confidential brief details** | Alert content is limited to an admin-written anonymized summary; the system never auto-includes description, budget, or requester fields; preview screen before sending |
| **Alert spam / abuse of the Join form** (fake applicants, bots, harvested emails) | Honeypot + rate limiting on `/join`; email verification before any alert; one application per email; one-click unsubscribe; admin can reject and remove from the pool |
| Applicants confuse an application with an account | Clear wording on `/join` and thank-you page; no password field anywhere on the form |
| Public upload fields (screenshots, resumes, applications, attachments) become a malware vector | Per-field type whitelist, 5 MB cap, `secure_filename` + random names, non-executable static path |
| Public forms attract spam | Honeypot + Flask-Limiter on Contact, Request-a-Project, Join |
| Resumes expose personal data | Opt-in; stored on dedicated paths; takedown is one admin action; deleting an applicant deletes their file |
| Inconsistent admin or coder-entered data | Required-field validation, required alt text, inline errors |
| Free-form tag fragmentation (also affects alert matching) | Case-insensitive matching; JSON arrays are forward-compatible with a curated vocabulary |
| Outbound mail failures silently drop leads, invites, or alerts | DB write is independent of mail; failures are logged; admin can resend invites and see per-applicant alert delivery status |
| SQLite→PostgreSQL migration mismatches | Single migration history; tested against a Postgres container before go-live |

**Resolved decisions carried forward from earlier drafts:** Blog is per-group; password reset is a signed email-token flow; tags are free-form JSON with a future curated vocabulary as a content (not engineering) item; assigning a request to a *Group* sends no automatic email.

**Resolved decisions for Version 2** *(assumptions made where the brief was open — correct any that are wrong)*:
- **D1 — Coder = Member with a login.** A coder account is linked one-to-one to a Member row; the group is derived from that member. A person cannot be a coder in two groups in this phase.
- **D2 — The super-admin creates all accounts.** Coders set their own password via an invite link; the admin never handles coder passwords.
- **D3 — "Who talked about a project / who asked for a call" stays with the super-admin.** The platform has no chat feature; the confidential material is the Contact messages, Project Requests, requester identity, and the admin's private notes. None of it is exposed to coders by default.
- **D4 — Grants default to "brief only."** A coder sees what is needed to judge the work but not who asked. Sharing the requester's contact details is a separate, deliberate tick-box per grant.
- **D5 — Coder-created projects publish immediately** (no approval queue), because the brief says coders may "make" projects themselves; every action is audited and the admin can unpublish. If you prefer a "pending approval" step, it is a small addition (a `status = pending_review` value) — flag it and it can be added.
- **D6 — Coders cannot delete projects or feature them**, and cannot manage blog posts. Easy to widen later.
- **D7 — Coder applications are not accounts.** Approving an applicant keeps them in the alert pool; converting them is a separate admin action.
- **D8 — Domain alerts are sent manually by the super-admin by default**, with an anonymized summary the admin writes or edits. An optional setting can automate this. This keeps the confidentiality promise in the admin's hands.
- **D9 — Revoking a coder keeps their public profile and projects live.** Content belongs to the group; the admin can edit or remove it separately.

## 13. Success Metrics

### Technical KPIs
- 99.5 % uptime; < 300 ms p95 on public reads, `/api/*`, and coder list pages.
- Zero unhandled exceptions across the six core flows: browse Groups, browse Members, submit Contact, submit Request-a-Project, **coder login → edit project**, **submit Join application**.
- **100 % pass on the authorization matrix** (no coder or visitor path reaches visitor-communication data).

### Business KPIs
- `ProjectRequest` and per-group `ContactMessage` submissions per month.
- Visitor → lead conversion rate.
- **Verified coder applications per month; applicant-to-coder conversion rate; share of project requests that receive a domain alert and at least one "I'm interested" response.**

### User Adoption KPIs
- Time-to-find a relevant group or member.
- Home bounce rate; resume download rate.
- **Percentage of active coders who update their profile or a project within 30 days of invite (profile freshness).**
- **Median time from invite sent to coder's first login.**

## 14. Appendices

### 14.1 API Endpoint Summary

**Public**
| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/groups`, `/group/<slug>`, `/members` | Directories and detail pages |
| GET/POST | `/request-project` | Request-a-Project form |
| POST | `/group/<slug>/contact` | Submit group inquiry |
| GET/POST | `/join` | **Join as a Coder** application |
| GET | `/join/thanks` | Application received page |
| GET | `/join/verify/<token>` | Verify applicant email |
| GET/POST | `/join/unsubscribe/<token>` | One-click alert unsubscribe |
| GET/POST | `/join/interested/<token>` | Confirm and record "I'm interested" from an alert (GET shows a one-button page; POST records) |
| GET | `/api/groups`, `/api/members` | Live-filtered JSON |

**Admin** (super-admin only)
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/admin/login`, `/admin/forgot-password`, `/admin/reset-password/<token>` | Admin auth |
| POST | `/admin/logout` | End session |
| GET | `/admin/dashboard` | Overview |
| — | `/admin/groups…`, `/admin/groups/<id>/members…`, `/admin/groups/<id>/projects…`, `/admin/blog…` | Existing CRUD |
| GET | `/admin/messages` + read/delete | Contact inbox |
| GET | `/admin/project-requests` | Request inbox |
| GET | `/admin/project-requests/<id>` | **Request detail: notes, domain tags, grants, alert history** |
| POST | `/admin/project-requests/<id>/notes`, `/domain-tags` | **Save private notes / domain tags** |
| GET | `/admin/project-requests/<id>/attachment`, `/admin/coder-applications/<id>/resume` | **Private file downloads (admin only)** |
| POST | `/admin/project-requests/<id>/status`, `/assign`, `/delete` | Existing actions |
| POST | `/admin/project-requests/<id>/grants` | **Grant access to a coder** |
| POST | `/admin/project-requests/<id>/grants/<grant_id>/revoke` | **Revoke a grant** |
| GET/POST | `/admin/project-requests/<id>/notify` | **Preview/send domain alert** |
| GET | `/admin/coders` | **Coder accounts list** |
| GET/POST | `/admin/coders/new`, `/admin/coders/<id>/edit` | **Create/edit coder** |
| POST | `/admin/coders/<id>/revoke`, `/reinstate`, `/resend-invite` | **Revoke / reinstate / resend invite** |
| GET | `/admin/coder-applications`, `/admin/coder-applications/<id>` | **Applications inbox/detail** |
| POST | `/admin/coder-applications/<id>/approve`, `/reject`, `/convert`, `/delete` | **Review actions** |
| GET | `/admin/audit-log` | **Audit log** |
| GET/POST | `/admin/settings` | Settings (incl. new toggles) |

**Coder** (active coder only)
| Method | Path | Purpose |
|---|---|---|
| GET/POST | `/coder/login`, `/coder/forgot-password`, `/coder/reset-password/<token>`, `/coder/accept-invite/<token>` | Coder auth and invite acceptance |
| POST | `/coder/logout` | End session |
| GET | `/coder/dashboard` | Coder home |
| GET/POST | `/coder/profile` | Edit own profile and resume |
| GET | `/coder/projects` | Own group's projects |
| GET/POST | `/coder/projects/new`, `/coder/projects/<id>/edit` | Create / edit project |
| GET | `/coder/opportunities`, `/coder/opportunities/<request_id>` | Granted requests only (404 otherwise) |

### 14.2 Notification Templates
| Template | Trigger | Recipient | Content |
|---|---|---|---|
| New Contact Message | Group contact submitted | Admin | Group, submitter, message, link |
| New Project Request | Request-a-Project submitted | Admin | Requester, type, excerpt, link |
| Password Reset Requested | Forgot-password (admin or coder) | That account | Signed, time-limited link |
| **Coder Invite** | Admin creates/resends coder | New coder | Welcome, signed 72-hour set-password link |
| **Opportunity Assigned** | Admin grants a request | Coder | "A project has been shared with you" + portal link; no requester details |
| **Application Verification** | Join form submitted | Applicant | Verify-email link |
| **New Coder Application** | Application verified | Admin | Applicant name, domains, link |
| **Domain Alert** | Admin sends alert | Verified, opted-in applicants | Anonymized admin-written summary, *I'm interested* and *Unsubscribe* links |

### 14.3 Glossary
- **Group** — a coding team with a public profile, roster, and project portfolio.
- **Member** — an individual in exactly one Group; optionally with a resume.
- **Project** — work credited to a Group.
- **Coder** — a Member who has a login created by the super-admin; can edit own profile and own group's projects and see only granted requests.
- **Coder Applicant** — a visitor who submitted the Join form; has no account.
- **Access Grant** — a revocable permission letting one coder see one Project Request, with a stated scope.
- **Brief only / Brief + contact** — the two grant scopes; the second reveals requester identity.
- **Domain Alert** — an anonymized email telling matching applicants that a project in their domain has arrived.
- **c-panel** — the super-admin's `/admin/*` panel; the coder's equivalent is the coder portal (`/coder/*`).
- **ProjectRequest** / **ContactMessage** — inbound leads; visible only to the super-admin (plus granted brief fields for coders).
- **Featured** — flag controlling home-page highlighting; admin-only.
