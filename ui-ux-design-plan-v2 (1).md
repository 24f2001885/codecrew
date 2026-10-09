# UI/UX DESIGN PLAN: CodeCrews — Version 2

> Derived from `project-definition-report-v2.md` (PDR) and `technical-design-report-v2.md` (TDR). Supersedes the earlier design plan. **What's new:** a third mode (the Coder Portal), the "Join as a Coder" pages, and the admin screens that manage coders, access grants, applications and domain alerts. Everything not mentioned here (Home, Groups, Group Detail, Members, Request-a-Project, Messages, Blog, Settings) is unchanged.

---

## 1. Design Principles

1. **Motion continuity** — the original template's animation language (AOS reveals, Stellar parallax, Owl Carousel, animated counters) carries across every *public* screen, including the new Join pages.
2. **Card-first browsing** — Groups, Members and Projects render through the shared macros `group_card()`, `member_card()`, `project_card()`.
3. **Zero-friction lead capture** — visitors still reach the platform through exactly two doors (Contact, Request-a-Project), plus one new, clearly separate door for people who want to *join* (Join as a Coder). The three forms share one validation and flash-alert pattern.
4. **Three visually distinct modes** — Public (dark, animated, marketing), Admin (dense sidebar utility shell), **Coder (same utility feel as Admin, with a green accent strip and a persistent "Coder" label so nobody mistakes it for the admin area)**. No hero, parallax or carousel appears in `/admin/*` or `/coder/*`.
5. **Confidentiality is visible** — wherever a coder sees something derived from a visitor's request, the screen *says* what is hidden and why ("Requester details are kept private by the platform admin"). Coders should never wonder whether a field is missing by mistake.
6. **Access changes are never silent** — revoking, granting and converting always use a confirm modal that states the consequence in plain words, and a revoked coder lands on a friendly "Your access has changed" page, not an error.
7. **Mobile-first grid** — Bootstrap 4 breakpoints unchanged; coder portal and join pages are fully usable on a phone.

---

## 2. Wireframe Reference

- **Visitor (public):** sticky top navbar with `.scrolled` state after 150 px; primary nav: **Home · Groups · Our Members · Request a Project · Join as a Coder** (the last styled as an outlined button so it reads as a secondary action, not the main lead CTA). Footer widget block adds a "Join as a Coder" link. A slim, dismissible banner strip on the Home page below the hero: "Developer? Join our coder pool and hear about projects in your domain." linking to `/join`.
- **Join pages (public):** `/join` is a single centered column on the dark theme: heading, one-paragraph explanation of the perk, form card (white surface, text `#212529`). `/join/thanks` and `/join/verify/<token>` are single-card confirmation pages.
- **Super-Admin (c-panel):** fixed left sidebar: Dashboard, Groups, Members, Projects, Blog, Messages, Project Requests, **Coders, Coder Applications, Audit Log**, Settings, Logout. Top bar with title/breadcrumb. Table-list + dedicated form-page pattern.
- **Coder portal:** fixed left sidebar (narrower): Dashboard, My Profile, My Group's Projects, Opportunities, Logout. Top bar shows the coder's name, group, and a green "Coder" tag. No Messages, no Requests inbox, no Settings entry exists in this sidebar at all (absence, not greyed-out).

---

## 3. Information Architecture (Sitemap)

### 3.1 Public / Shared
- Home (`/`) · Groups (`/groups`) · Group Detail (`/group/<slug>`) · Our Members (`/members`) · Request a Project (`/request-project`)
- **Join as a Coder (`/join`)**
  - **Application sent (`/join/thanks`)**
  - **Email verified (`/join/verify/<token>`)**
  - **Unsubscribed (`/join/unsubscribe/<token>`)**
  - **Express interest (`/join/interested/<token>`)**
  - **Applications closed (shown at `/join` when the admin setting is off)**
- 404 / 403 / 500 error pages

### 3.2 Admin
- Login · Forgot/Reset password
- Dashboard (now includes active coders, pending applications, open grants)
- Groups / Members / Projects / Blog CRUD (unchanged)
- Messages Inbox (unchanged)
- Project Requests Inbox → **Project Request Detail** (new): request summary, internal notes, domain tags, Access Grants panel, Alerts panel → **Notify Applicants (preview/send)**
- **Coders** list → Coder Create/Edit form
- **Coder Applications** list → Application Detail (with Convert-to-coder form)
- **Audit Log**
- Settings (adds two toggles)

### 3.3 Staff / Employee
**N/A.** The "coder" role is the only non-admin account type and is described in 3.4; there is still no separate staff tier.

### 3.4 User / Customer — **Coder Portal (new)**
- Accept Invite (`/coder/accept-invite/<token>`) · Login (`/coder/login`) · Forgot/Reset password
- Dashboard (`/coder/dashboard`)
- My Profile (`/coder/profile`)
- My Group's Projects (`/coder/projects`) → Project Create/Edit form
- Opportunities (`/coder/opportunities`) → Opportunity Detail
- Access Changed page (shown after revocation)

Anonymous visitors still have no account and no persistent state.

---

## 4. Key User Flows

### 4.1 Login, Invite & Password Reset
- **Admin:** unchanged (`/admin/login`, seeded account, signed-token reset).
- **Coder invite (new):** super-admin creates a coder → coder receives an email "You've been added to CodeCrews" → clicks the link → **Accept Invite** page (set password + confirm, password-strength hint, link expiry note) → redirected to `/coder/login` with a success flash → logs in → Dashboard. An expired or already-used link shows a friendly page with "Ask the platform admin to resend your invite."
- **Coder login:** same dark themed login pattern as admin but with the heading "Coder sign-in" and the green accent; failed attempt uses the same inline alert styling; revoked accounts see the **same generic error as a wrong password** ("Invalid username or password") so account status is not leaked.
- **Coder password reset:** same generic-message flow as the admin's.
- **No registration anywhere.** Accounts are created only by the super-admin.

### 4.2 Core Transaction Flow — "Discover → Engage" (unchanged for visitors)
Home → live search on `/groups` or `/members` → Group page / member popup → contact the group, or `/request-project`. Nothing is saved between visits. The only new branch: a developer-visitor can detour to **Join as a Coder** from the navbar, footer, or Home banner.

### 4.3 Contact & Request-a-Project Flow (unchanged for visitors)
Visitor submits → super-admin reviews in the inboxes → status/assignment as before. **New admin steps on a Project Request Detail page:** add private notes, confirm/edit domain tags, grant to coders, notify matching applicants. A visitor's request is never shown to a coder until the admin takes one of these deliberate actions.

### 4.4 Admin: Create and Manage a Coder (new)
1. **Coders → New coder.** Pick an existing member (searchable select grouped by group), or choose "Create new member" (reveals group + name fields). Enter username and email. Submit.
2. Row appears with an **Invited** badge; "Resend invite" is available. Once the coder sets a password the badge becomes **Active**.
3. **Revoke:** row action → confirm modal: "Revoke {name}? They will be signed out immediately, cannot log in, and all their open project-request access will be removed. Their profile and projects stay published." Optional reason field. Badge becomes **Revoked**; the row's action becomes **Reinstate** (modal notes "They will start with no project-request access").
4. Every action writes to the Audit Log.

### 4.5 Admin: Share a Project Request with a Coder, and Take It Back (new)
1. Open a Project Request → **Access** panel lists current and past grants (coder, scope, granted date, expiry, status).
2. **Grant access:** choose an Active coder, choose scope with plain-language radio labels — **"Brief only — project details, no requester identity" (default)** or **"Brief + requester contact — name, email, company"** (second option carries an amber warning icon) — optional expiry date → confirm. The coder gets an email "A project has been shared with you" with no requester details.
3. **Revoke:** row action → confirm modal "{coder} will immediately lose access to this request." → status becomes Revoked (kept in history).
4. The admin also sees a read-only line "Coders never see: your notes, status, or assignments."

### 4.6 Coder: Daily Work (new)
- **Dashboard:** greeting, group name, two summary cards (My group's projects; Open opportunities), and a "Recently edited" list.
- **Edit profile:** form with role, bio, skill chips, social URLs, photo upload, resume PDF upload. Name and group are shown read-only with the note "Ask the admin to change these." Save → flash.
- **Projects:** list of own group's projects (title, status pill, last edited by/at). **New project** / **Edit** open a dedicated form page (not a modal, because of uploads): title, description, tech chips, GitHub/live URLs, status, gallery uploader where each image row has a required "Describe this image" alt-text field. No "Featured" control and no Delete button exist. Save → flash; the project is live on the group page immediately.
- **Opportunities:** table of granted requests: type, domain chips, budget, timeline, date shared. Detail page shows the brief; a gray panel at the top reads either "Requester details are kept private by the platform admin." (brief-only) or shows the contact block (brief + contact). Attachment appears as a download button if present. There are no reply, chat, or accept buttons — the page ends with "The platform admin will contact you about next steps."
- **Revoked mid-session:** next click lands on **Access Changed** ("Your access to this area has been changed by the platform admin. Please contact them if you think this is a mistake.") with a link back to the public site.

### 4.7 Visitor: Join as a Coder (new)
1. Visitor clicks **Join as a Coder** → `/join`.
2. Reads: "Want to be considered for projects? Tell us your domain. We'll email you when a matching project arrives. This doesn't create an account." Fills the form: name, email, domains (multi-select checkboxes of the five project types), skills/domain tags (chip input; plain comma-separated fallback without JS), headline, GitHub/portfolio, message, optional resume PDF, a required consent checkbox ("Email me about projects in my domains; I can unsubscribe any time"). Honeypot hidden.
3. Submit → `/join/thanks` ("Check your email to confirm your address"). Re-applying with the same email updates the existing application and says so.
4. Clicks the verification link → **Email verified** page ("You're on our radar. The admin will review your application.").
5. Later: receives a **Domain Alert** email — short anonymized summary, a green **"I'm interested"** button and an **Unsubscribe** link. Clicking *I'm interested* opens a one-button confirm page, then a thank-you; the visitor is told "If the platform admin picks you, they'll get in touch." No project link or requester information is ever shown.
6. **Unsubscribe** works in one click without login and shows a confirmation with a "Changed your mind? Re-apply" link.

### 4.8 Admin: Review Applications and Send Alerts (new)
- **Coder Applications** list: columns — name, email, domains (chips), verified (check/dash), status pill, applied date. Filters: status, verified. Row → detail with resume link (admin-only download), notes, delivery history, and actions **Approve · Reject · Convert to coder · Delete**.
- **Convert to coder:** choose group (required), confirm display name/role, set username → creates Member + invited Coder account → application becomes **Converted** with a link to the coder.
- **Notify Applicants** (from a Project Request): page shows matched applicant count, a table of matches (name, matching domains, previously alerted?), a textarea for the **anonymized summary** with a character counter and prefilled text, and a bold checklist line: "Do not include names, company, budget, or specifics that could identify the requester." Button: **Send to N applicants** (batch size shown, e.g. "first 100"), then a result banner "Sent 100, failed 0 — 37 remaining." After sending, a list shows who clicked **I'm interested** so the admin can convert and grant.

---

## 5. Screen Inventory

**Public**
- Home / Landing (now with Join banner and navbar item)
- Groups Directory · Group Detail · Our Members · Request a Project
- **Join as a Coder (form) · Join — Application Sent · Join — Email Verified · Join — Unsubscribed · Join — Express Interest (confirm + thanks) · Join — Applications Closed**
- 404 · **403** · 500

**Admin**
- Login · Forgot/Reset Password · Dashboard
- Groups List/Form · Members List/Form · Projects List/Form · Blog List/Form
- Messages Inbox · Project Requests Inbox
- **Project Request Detail (notes, domain tags, access grants, alert history)**
- **Notify Applicants (preview + send)**
- **Coders List · Coder Create/Edit Form**
- **Coder Applications List · Application Detail (incl. Convert form)**
- **Audit Log**
- Settings (adds "Accept coder applications" and "Auto-send domain alerts" toggles)

**Coder portal (new)**
- Accept Invite · Login · Forgot Password · Reset Password
- Dashboard · My Profile · Projects List · Project Create/Edit Form
- Opportunities List · Opportunity Detail
- Access Changed

---

## 6. Status Badge Convention

| State | Color |
|---|---|
| Featured (Group or Project) | Amber `#ffbd39` |
| Published / Active | Green `#a0f669` |
| Draft / Pending Review (blog) | Gold `#ffc107` |
| Unread Message | Red dot `#dc3545` |
| Error / Delete-confirm | Red `#dc3545` |
| Project Request — New | Blue `#17a2b8` |
| Project Request — In Review | Gold `#ffc107` |
| Project Request — Contacted | Green `#a0f669` |
| Project Request — Closed | Gray `#6c757d` |
| **Coder — Invited** | Blue `#17a2b8` |
| **Coder — Active** | Green `#a0f669` |
| **Coder — Revoked** | Red `#dc3545` |
| **Grant — Brief only** | Gray `#6c757d` |
| **Grant — Brief + contact** | Amber `#ffbd39` with a person icon |
| **Grant — Active** | Green `#a0f669` |
| **Grant — Revoked / Expired** | Red `#dc3545` / Gray `#6c757d` |
| **Application — Pending** | Gold `#ffc107` |
| **Application — Approved** | Green `#a0f669` |
| **Application — Rejected** | Gray `#6c757d` |
| **Application — Converted** | Blue `#17a2b8` |
| **Alert delivery — Sent / Failed / Interested** | Gray / Red `#dc3545` / Green `#a0f669` |

Every badge pairs color with text (never color alone). No Saved/Bookmark badge exists.

---

## 7. Style Guide Basics

Unchanged base (TDR §7):
- **Framework:** Bootstrap 4.3.1; no bundler.
- **Primary** `#ffbd39` · **Secondary** `#a0f669` · **Loader** `#F96D00` · **Background** `#000000` · **Body text** `#999999` · **Text on light surfaces** `#212529` · **Font** Poppins (100–900), fallback Arial/sans-serif.

Version 2 additions:
- **Admin shell:** dark gray `#111` sidebar, amber active item.
- **Coder shell:** same layout as admin, with a 4 px `#a0f669` strip at the top of the sidebar, a green "Coder" pill beside the user's name, and a muted `coder.css` file for the few differences.
- **Confidentiality notice component** (`.cc-private-note`): gray panel with a lock icon and `#999` text on `#1a1a1a`, used on Opportunity Detail and in the admin's Access panel.
- **Consequence modals:** Revoke/Reinstate/Convert use a red or amber header and a one-sentence consequence line above the confirm button.
- **Join form card:** white surface (`#fff`) with `#212529` text, matching the existing contact form panel.

---

## 8. Accessibility & Responsiveness

- **Target:** WCAG 2.1 AA.
- **Grid:** Bootstrap 4 breakpoints unchanged. Admin and coder tables become stacked cards below `md`; the coder sidebar collapses behind a labeled burger.
- **Icon-only controls** require `aria-label`s: burger menus, resume-download icons, modal close buttons, and the new revoke/reinstate/resend icon buttons (e.g., `aria-label="Revoke access for {coder name}"`).
- **Images:** member photos use the member name as alt text; **project gallery images require an admin- or coder-entered description (alt) field, enforced by the form**, in both admin and coder portals.
- **Forms:** every `/join`, coder and admin field has a visible label; errors are announced with `role="alert"`; the consent checkbox is an explicit labeled control, not pre-checked; the chip input falls back to a plain text field without JavaScript.
- **Status and consequences** are never conveyed by color alone (text label + icon).
- **Emails** (invite, verification, alert) are plain-text first, with the main action as a single clearly labeled link.
- **Empty and edge states** have text: "No opportunities have been shared with you yet", "No applications yet", "No matching applicants for this request", "No grants yet".
