#!/usr/bin/env bash
# P4.sh
# CodeCrews — Milestone P4: Contact, Request-a-Project & Messaging
#
# Developer: Abhishek (Team Lead and sole developer)
#
# Goal (Master Project Blueprint v2): the two ways data enters the system
# without admin action — group inquiries and platform-wide project
# requests — are fully functional, and ONLY the super-admin can see them.
# Version 2 note: request attachments are stored in a PRIVATE folder (not
# the public static folder) and downloaded through an authenticated route.
#
# This script contains zero application logic; every file is a heredoc
# holding a PROMPT for an LLM (code-implementer), on ONE task branch.
#
# Source docs: master-project-blueprint-v2.md §3 (P4), PDR v2 §5.5,
# TDR v2 §4/§5/§6/§8.1, Design Plan v2 §4.3.

set -e

echo "====================================================="
echo "CodeCrews — P4: Contact, Request-a-Project & Messaging"
echo "Developer: Abhishek"
echo "====================================================="

echo ""
echo "--- Phase 4 initialization ---"
git checkout MAIN
git pull origin MAIN || echo "WARNING: could not pull MAIN (offline — continuing)."

if git show-ref --quiet refs/heads/phase4-seed; then
    echo "phase4-seed already exists — skipping."
else
    git checkout -b phase4-seed MAIN
fi
if git show-ref --quiet refs/heads/phase4; then
    echo "phase4 already exists — skipping."
else
    git checkout -b phase4 phase4-seed
fi
git push -u origin phase4-seed || echo "WARNING: could not push phase4-seed."
git push -u origin phase4 || echo "WARNING: could not push phase4."

git checkout phase4
mkdir -p app/forms app/services app/routes app/templates/admin app/templates/public
mkdir -p app/templates/emails instance/private_uploads/requests tests
git add -A
git commit -q -m "P4: skeleton verification" || echo "Nothing to commit."
git push origin phase4 || echo "WARNING: could not push phase4."

echo ""
echo "--- Creating task-abhishek-phase4-contact-requests ---"
git checkout -b task-abhishek-phase4-contact-requests phase4

cat << 'EOF' > app/services/private_files.py
"""
FILE PURPOSE: Storage and download of CONFIDENTIAL files (request
attachments now; applicant resumes in P8) outside the static tree
(TDR v2 §6 "Private files").

PROMPT FOR LLM IMPLEMENTATION:
1. Constants: ATTACHMENT_EXTENSIONS = {".pdf", ".docx"}; RESUME_EXTENSIONS
   = {".pdf"}; allowed private subfolders = {"requests", "applications"}.
2. def private_root(): Path(current_app.config["PRIVATE_UPLOAD_FOLDER"])
   resolved; create it if missing.
3. def save_private(file_storage, subfolder, allowed_extensions): same
   checks as services/uploads.py (empty filename -> None; extension
   whitelist; size <= MAX_CONTENT_LENGTH; magic bytes: PDF b"%PDF-", DOCX
   zip header b"PK\x03\x04"). Stored name = uuid4().hex + extension (the
   original name is NOT kept in the path). Returns the path relative to
   the subfolder (just the stored name). Raise UploadError (import from
   services.uploads) with a friendly message on failure.
4. def delete_private(subfolder, stored_name): delete only inside
   private_root()/subfolder; ignore missing; return bool.
5. def send_private(subfolder, stored_name, download_name): resolve the
   path, 404 if missing or outside the folder, and return
   flask.send_file(path, as_attachment=True, download_name=download_name)
   with header X-Content-Type-Options: nosniff.
6. No route lives here; routes decide who may call send_private.

DEBUGGING:
# print(f"[DEBUG] private save subfolder={subfolder} stored={stored!r}")

OFFLINE DOCKER TEST CASES:
- A real tiny PDF saves under the private folder and NOT under the static
  upload folder.
- A .exe renamed .pdf is rejected.
- send_private for a missing file returns 404.
- A stored name containing ".." is refused.
"""
EOF

cat << 'EOF' > app/services/mailer.py
"""
FILE PURPOSE: Flask-Mail wrapper — P4 adds the contact and project-request
notifications (TDR v2 §8.1). Mail failure NEVER blocks the caller.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep send_password_reset_email exactly as P1 built it.
2. Add a private helper _send(subject, body, recipients): builds a
   flask_mail.Message with sender MAIL_DEFAULT_SENDER, calls mail.send in
   try/except; on success log INFO, on failure logger.exception; returns
   True/False. Never re-raises.
3. def send_contact_notification(contact_message): subject "New Contact
   Message — {group name}", recipient ADMIN_NOTIFICATION_EMAIL, body from
   templates/emails/new_contact.txt rendered with render_template;
   includes group name, submitter name/email, subject, message, and the
   absolute URL of url_for("admin.messages", _external=True).
4. def send_project_request_notification(project_request): subject "New
   Project Request — {project_type label}", body from
   templates/emails/new_project_request.txt: requester name/email, type,
   a description excerpt (first 300 characters), and the absolute URL to
   the admin project-requests inbox. Recipient is the admin only.
5. Add a comment: coder/applicant notifications arrive in P7/P8.

DEBUGGING:
# print(f"[DEBUG] mailer._send subject={subject!r} ok={ok}")

OFFLINE DOCKER TEST CASES:
- With MAIL_SUPPRESS_SEND=True, send_contact_notification returns True and
  mail.record_messages() captures one message with the right subject.
- If mail.send is monkeypatched to raise, the function returns False and
  does not raise.
- The project request email body never includes more than 300 characters
  of the description.
"""
EOF

cat << 'EOF' > app/templates/emails/new_contact.txt
{#
FILE PURPOSE: Plain-text email body for "New Contact Message".

PROMPT FOR LLM IMPLEMENTATION:
1. Plain text only. Lines: group name, "From: {name} <{email}>", "Subject:
   {subject or '(none)'}", a blank line, the message, a blank line, and
   "Open the inbox: {inbox_url}".
2. No HTML. Jinja autoescape is off for .txt, so only print fields the
   system already validated.

DEBUGGING:
{# [DEBUG] new_contact.txt rendered #}

OFFLINE DOCKER TEST CASES:
- The rendered text contains the sender email and the inbox URL.
#}
EOF

cat << 'EOF' > app/templates/emails/new_project_request.txt
{#
FILE PURPOSE: Plain-text email body for "New Project Request".

PROMPT FOR LLM IMPLEMENTATION:
1. Lines: requester name and email, company (if any), project type label,
   budget and timeline (if any), a blank line, the description excerpt
   (first 300 chars, add "..." when truncated), a blank line, and "Review
   it: {inbox_url}".
2. Mention whether an attachment was included (yes/no) but never link it.

DEBUGGING:
{# [DEBUG] new_project_request.txt rendered #}

OFFLINE DOCKER TEST CASES:
- The text contains the requester email and the inbox URL, and the word
  "attachment" appears only as a yes/no note.
#}
EOF

cat << 'EOF' > app/forms/contact_forms.py
"""
FILE PURPOSE: Flask-WTF form for a group's contact form (PDR §5.5).

PROMPT FOR LLM IMPLEMENTATION:
1. class ContactForm(FlaskForm): name (DataRequired, Length 2-120); email
   (DataRequired, Email, Length max 255); subject (Optional, Length max
   200); message (DataRequired, Length 10-4000); website (StringField,
   the honeypot, no validators); submit.
2. Custom validate_website: if the honeypot has any value raise
   ValidationError("Spam detected") — the route treats this as a silent
   success (does not store, shows the normal thank-you) so bots learn
   nothing.
3. Strip whitespace on all text fields.

DEBUGGING:
# print(f"[DEBUG] ContactForm honeypot filled={bool(self.website.data)}")

OFFLINE DOCKER TEST CASES:
- A valid submission validates.
- A bad email fails with an inline error.
- A filled honeypot fails validation (route handles silently).
"""
EOF

cat << 'EOF' > app/forms/request_forms.py
"""
FILE PURPOSE: Flask-WTF form for the platform-wide Request-a-Project page
(PDR §5.5).

PROMPT FOR LLM IMPLEMENTATION:
1. class RequestForm(FlaskForm): name (DataRequired, Length 2-120); email
   (DataRequired, Email); company (Optional, max 150); project_type
   (SelectField with choices web_app "Web App", mobile_app "Mobile App",
   desktop_software "Desktop Software", api_backend "API / Backend", other
   "Other"; DataRequired); budget_range (Optional, max 80); timeline
   (Optional, max 80); description (TextAreaField, DataRequired, Length
   20-5000); attachment (FileField, Optional, FileAllowed pdf/docx);
   website (honeypot); submit.
2. Honeypot behavior identical to ContactForm.
3. The attachment's deeper checks (size, magic bytes) happen in
   services/private_files.py.

DEBUGGING:
# print(f"[DEBUG] RequestForm type={self.project_type.data}")

OFFLINE DOCKER TEST CASES:
- project_type outside the five choices fails.
- A 10-character description fails (too short).
- An .exe attachment fails FileAllowed.
"""
EOF

cat << 'EOF' > app/routes/contact.py
"""
FILE PURPOSE: Public POST endpoint for a group's contact form
(/group/<slug>/contact, PDR §5.5, TDR v2 §5).

PROMPT FOR LLM IMPLEMENTATION:
1. contact_bp = Blueprint("contact", __name__).
2. POST /group/<slug>/contact: get the group or 404; build ContactForm;
   apply limiter "5 per hour" per IP plus "30 per day".
3. On a filled honeypot: do not store anything, flash the normal success
   message and redirect to the group page (silent).
4. On valid data: create ContactMessage(group_id=group.id, name, email,
   subject, message), commit FIRST, then call
   mailer.send_contact_notification (failure must not undo the row),
   flash success "Thanks — your message was sent to {group.name}.",
   log INFO, redirect to url_for("public.group_detail", slug=slug) +
   "#contact".
5. On validation errors: re-render "public/group_detail.html" with the
   form errors shown inline (reuse the group_detail view's context
   builder from routes/public.py via a small helper) and HTTP 200.
6. Only POST is allowed (GET -> 405).

DEBUGGING:
# print(f"[DEBUG] contact POST group={slug} valid={form.validate_on_submit()}")

OFFLINE DOCKER TEST CASES:
- A valid POST creates exactly one ContactMessage tied to the group and
  one mail is captured.
- A filled honeypot creates zero rows but still redirects with a flash.
- The 6th POST within an hour from the same IP returns 429.
- If sending mail raises, the row still exists and the user still sees
  success.
"""
EOF

cat << 'EOF' > app/routes/requests.py
"""
FILE PURPOSE: Public Request-a-Project page (GET form + POST submit)
(PDR §5.5, TDR v2 §5).

PROMPT FOR LLM IMPLEMENTATION:
1. requests_bp = Blueprint("requests", __name__).
2. GET /request-project: render "public/request_project.html" with an
   empty RequestForm.
3. POST /request-project: limiter "5 per hour" per IP. Honeypot handled
   silently like contact. On valid data: if an attachment is present call
   services.private_files.save_private(file, "requests", {".pdf", ".docx"})
   (UploadError -> inline form error); create ProjectRequest with
   status "new", attachment_path = the stored name; commit; call
   mailer.send_project_request_notification (best effort); flash success
   "Thanks — we received your request."; redirect to
   url_for("requests.request_project").
4. On validation failure re-render the page with inline errors (200).
5. Leave a comment: P8 may trigger automatic domain alerts here when the
   admin enabled that setting.
6. The blueprint is named "requests" but the module must not shadow the
   third-party "requests" library — import it explicitly if ever needed.

DEBUGGING:
# print(f"[DEBUG] request-project POST type={form.project_type.data}")

OFFLINE DOCKER TEST CASES:
- GET returns 200 with all fields and a csrf token.
- A valid POST with a PDF stores the file in the PRIVATE folder and not in
  static/uploads, creates one ProjectRequest with status "new".
- A valid POST without attachment works.
- A filled honeypot stores nothing.
- Mail failure does not remove the row.
"""
EOF

cat << 'EOF' > app/templates/public/request_project.html
<!--
FILE PURPOSE: Platform-wide "Request a Project" form page (Design Plan
§4.3).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "base.html" %}; hero-style heading "Tell us what you want
   built" with a short paragraph explaining that the request goes only to
   the platform admin.
2. A white form card (text #212529): all RequestForm fields with visible
   labels, inline errors with role="alert", a hidden honeypot input named
   website (display:none, tabindex -1, autocomplete off), csrf hidden tag,
   enctype multipart/form-data, and a submit button in amber.
3. Help text under attachment: "PDF or DOCX, up to 5 MB."
4. A short privacy note: "Your details are seen only by the platform
   admin."

DEBUGGING:
<!-- <script>console.log("[DEBUG] request_project.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- The form is multipart, has a csrf_token input and the hidden honeypot.
- Each field has an associated <label>.
-->
EOF

cat << 'EOF' > app/templates/public/group_detail.html
<!--
FILE PURPOSE: Group detail — P4 wires the contact form for real.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything P2 built.
2. Contact form: action="{{ url_for('contact.contact', slug=group.slug) }}"
   method="POST", {{ form.hidden_tag() }}, inline errors beside each
   field (role="alert"), the hidden honeypot field, and a visible label
   for every input.
3. The page receives a ContactForm named form (built in the view helper);
   preserve submitted values after an error.

DEBUGGING:
<!-- <script>console.log("[DEBUG] group_detail contact form wired");</script> -->

OFFLINE DOCKER TEST CASES:
- The form action points to /group/<slug>/contact.
- After an invalid submission the page shows the inline error and keeps
  the typed name.
-->
EOF

cat << 'EOF' > app/templates/partials/navbar.html
<!--
FILE PURPOSE: Navbar — P4 links "Request a Project".

PROMPT FOR LLM IMPLEMENTATION:
1. Keep P2's links and active-state logic.
2. "Request a Project" -> url_for('requests.request_project').
3. "Our Members" remains href="#" until P5.

DEBUGGING:
<!-- <script>console.log("[DEBUG] navbar P4");</script> -->

OFFLINE DOCKER TEST CASES:
- The Request a Project link resolves to /request-project.
-->
EOF

cat << 'EOF' > app/routes/admin.py
"""
FILE PURPOSE: Admin blueprint — P4 adds the Messages inbox and the Project
Requests inbox (TDR v2 §5). Super-admin only.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything P3 built and the guard.
2. Messages: GET /admin/messages (query page, is_read filter;
   ordered by created_at desc; 20 per page; shows group name);
   POST /admin/messages/<id>/read toggles is_read; POST
   /admin/messages/<id>/delete. Endpoint name for the list: "messages".
3. Project Requests: GET /admin/project-requests (page, status filter;
   created_at desc; 20 per page; columns requester, type, submitted date,
   status pill, assigned group); POST /admin/project-requests/<id>/status
   (validate against new/in_review/contacted/closed); POST
   .../<id>/assign (assigned_group_id empty string clears it; invalid
   group id -> flash error); POST .../<id>/delete (also delete the private
   attachment file); GET .../<id>/attachment streams the private file via
   services.private_files.send_private with a download name built from
   the request id (never trust the original name). Assigning a group sends
   NO email (PDR §12).
4. Dashboard: add counts for unread messages and new project requests.
5. Do not add request detail, notes, grants or coder routes (P7).

DEBUGGING:
# print(f"[DEBUG] admin request {id} status -> {new_status}")

OFFLINE DOCKER TEST CASES:
- Anonymous access to every route above redirects to login.
- Changing status to an invalid value flashes an error and changes nothing.
- Assigning then clearing a group works and no mail is sent.
- Deleting a request removes the private attachment file.
- The attachment URL is not reachable via /static/.
"""
EOF

cat << 'EOF' > app/templates/admin/messages.html
<!--
FILE PURPOSE: Contact inbox — inquiries only (no suggestion filter).

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "admin/admin_base.html" %}; title "Messages".
2. Filter links: All / Unread. Table: red dot for unread (with sr-only
   text "Unread"), group name, sender name and email, subject, short
   message preview, date, actions Mark read/unread (POST form) and Delete
   (confirm modal, aria-label naming the sender).
3. Expand/collapse or detail row to read the full message.
4. Pagination; empty state "No messages yet."

DEBUGGING:
<!-- <script>console.log("[DEBUG] messages.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Unread rows show the red dot and its text alternative.
- The delete button uses POST with a csrf token.
-->
EOF

cat << 'EOF' > app/templates/admin/project_requests.html
<!--
FILE PURPOSE: Project Requests inbox with status pills and group
assignment.

PROMPT FOR LLM IMPLEMENTATION:
1. {% extends "admin/admin_base.html" %}; title "Project Requests".
2. Status filter tabs: All / New / In Review / Contacted / Closed.
3. Table: requester name+email, company, project type label, submitted
   date, status pill (New blue, In Review gold, Contacted green, Closed
   gray — always with text), assigned group, attachment link (admin
   download route) when present.
4. Inline change-status select that POSTs on change (form per row with
   csrf), and an assign-to-group select + Save button per row.
5. Delete with confirm modal. Show the full description in an expandable
   row.
6. Empty state "No project requests yet."

DEBUGGING:
<!-- <script>console.log("[DEBUG] project_requests.html rendered");</script> -->

OFFLINE DOCKER TEST CASES:
- Status pills render with the right text for each status.
- The attachment link points at /admin/project-requests/<id>/attachment,
  never at /static/.
-->
EOF

cat << 'EOF' > app/__init__.py
"""
FILE PURPOSE: Flask application factory — P4 registers the two public
lead-capture blueprints.

PROMPT FOR LLM IMPLEMENTATION:
1. Keep everything built in P0-P3 and the P1 patch (config, extensions,
   model imports, logging, `now` context processor, public/auth/admin
   blueprints).
2. Register contact_bp (app/routes/contact.py) and requests_bp
   (app/routes/requests.py).
3. Add a before-first-use step that creates the PRIVATE_UPLOAD_FOLDER
   directory if missing (os.makedirs exist_ok=True).
4. Add an error handler for 413 (request too large) that flashes "That
   file is larger than 5 MB." and redirects back (referrer or home).
5. Update the comment listing remaining blueprints: join/coder_auth/coder
   (P7, P8), api (P5).

DEBUGGING:
# print("[DEBUG] blueprints: public, auth, admin, contact, requests")

OFFLINE DOCKER TEST CASES:
- app.url_map contains /group/<slug>/contact and /request-project.
- Creating the app twice does not raise when the private folder exists.
- Posting a body larger than MAX_CONTENT_LENGTH returns a friendly redirect
  (not a 500).
"""
EOF

cat << 'EOF' > tests/test_contact_forms.py
"""
FILE PURPOSE: P4 tests — group contact flow.

PROMPT FOR LLM IMPLEMENTATION:
1. test_contact_valid_creates_message_and_mail(client, sample_groups).
2. test_contact_invalid_email_shows_inline_error.
3. test_contact_honeypot_silent_success.
4. test_contact_rate_limit_returns_429 (enable the limiter in this test via
   a config override).
5. test_contact_mail_failure_keeps_row (monkeypatch mail.send to raise).
6. test_contact_get_is_405.
7. test_admin_messages_inbox_requires_login_and_lists_message.
8. test_mark_read_and_delete_via_post_only.
9. test_message_always_has_group_id (NOT NULL enforced).

DEBUGGING:
# print("[DEBUG] running contact flow tests")

OFFLINE DOCKER TEST CASES:
- All pass offline with MAIL_SUPPRESS_SEND=True and record_messages().
"""
EOF

cat << 'EOF' > tests/test_project_requests.py
"""
FILE PURPOSE: P4 tests — Request-a-Project flow and admin inbox.

PROMPT FOR LLM IMPLEMENTATION:
1. test_request_form_get_200.
2. test_request_valid_creates_row_status_new_and_mail.
3. test_request_with_pdf_saved_privately: file under PRIVATE_UPLOAD_FOLDER,
   not under static/uploads, and GET /static/... of that name is 404.
4. test_request_rejects_bad_attachment_type_and_size.
5. test_request_honeypot_silent.
6. test_admin_inbox_lists_request_and_status_change_persists.
7. test_assign_group_sends_no_email.
8. test_delete_request_removes_private_file.
9. test_attachment_download_requires_admin: anonymous -> 302; admin -> 200
   with Content-Disposition attachment and nosniff header.
10. test_end_to_end_request_to_admin_status: submit -> login -> see in
    inbox -> change status -> persists (TDR §10 E2E example).

DEBUGGING:
# print("[DEBUG] running project request tests")

OFFLINE DOCKER TEST CASES:
- All pass offline.
"""
EOF

git add -A
git commit -q -m "P4 seed: contact, request-a-project and messaging placeholders (Abhishek)"
git push -u origin task-abhishek-phase4-contact-requests || echo "WARNING: could not push task-abhishek-phase4-contact-requests."

echo ""
echo "====================================================="
echo "Milestone P4 Seeded Successfully!"
echo "NEXT STEPS (Abhishek):"
echo "1. Feed the seeded files to your LLM (code-implementer) to generate the code."
echo "2. Run: docker-compose -f docker-compose.test.yml run --rm web pytest"
echo "3. Commit in logical chunks, open a PR into 'phase4', review and merge."
echo "4. If tests pass: git checkout MAIN && git merge phase4, then tag the release."
echo "5. Execute P5.sh."
echo "====================================================="
