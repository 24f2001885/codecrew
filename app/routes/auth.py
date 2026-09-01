"""
FILE PURPOSE: Auth blueprint — login/logout + the signed email-token
password-reset flow (PDR §5.2, resolved per Master Project Blueprint's
P1 map; TDR §5 REST design; TDR §6 session/security rules).

PROMPT FOR LLM IMPLEMENTATION:
1. auth_bp = Blueprint("auth", __name__, url_prefix="/admin").
2. Import login_manager from app.extensions; define
   @login_manager.user_loader def load_user(user_id): return
   AdminUser.query.get(user_id) (import AdminUser from
   app.models.admin_user — only resolves once Piyush's branch is
   merged, note that as a comment).
3. GET/POST "/login" -> login(): instantiate LoginForm(). On valid
   POST, look up AdminUser by username, check_password_hash against the
   submitted password; on success call login_user(admin) (Flask-Login)
   and redirect to url_for("admin.dashboard"); on failure, flash an
   "error"-category message ("Invalid username or password.") and
   re-render "admin/login.html" with the same form (inline error via
   the shared flash pattern, PDR §5.2). If current_user is already
   authenticated, redirect straight to the dashboard instead of
   re-showing the form.
4. POST "/logout" -> logout(): @login_required, call logout_user(),
   flash a "success" message, redirect to url_for("auth.login").
5. GET/POST "/forgot-password" -> forgot_password(): instantiate
   ForgotPasswordForm(). On valid POST, look up AdminUser by the
   submitted username; if found, build a signed token via
   itsdangerous.URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
   .dumps(admin.id, salt="password-reset") and call
   mailer.send_password_reset_email(admin, token) (from
   app.services.mailer — Utkarsh's own file below). Regardless of
   whether the username matched, flash the SAME generic "success"
   message ("If that account exists, a reset link has been sent.") and
   redirect to url_for("auth.login") — never reveal whether the
   username existed (TDR §6 security posture, applied here even though
   there's only one admin).
6. GET/POST "/reset-password/<token>" -> reset_password(token):
   verify the token via the same serializer's .loads(token,
   salt="password-reset", max_age=3600) inside a try/except; on
   failure (BadSignature/SignatureExpired), flash an "error" message
   and redirect to url_for("auth.forgot_password"). On success,
   instantiate ResetPasswordForm(); on valid POST, look up the AdminUser
   by the id embedded in the token, set
   admin.password_hash = generate_password_hash(form.password.data),
   db.session.commit(), flash a "success" message, redirect to
   url_for("auth.login"). On GET (token valid, no POST yet), render
   "admin/reset_password.html" with the form.
7. Rate limiting: apply the shared `limiter` (from app.extensions) to
   the login route specifically, e.g. @limiter.limit("10 per minute"),
   per TDR §6 ("to blunt credential-stuffing attempts against the
   single admin account").

DEBUGGING:
# print(f"[DEBUG] POST /admin/login — attempt for username={request.form.get('username')!r}")
# print(f"[DEBUG] POST /admin/forgot-password — token issued (or silently skipped) for username={request.form.get('username')!r}")

OFFLINE DOCKER TEST CASES:
- POST "/admin/login" with correct seeded credentials redirects (302)
  to "/admin/dashboard" and sets a session cookie.
- POST "/admin/login" with a wrong password returns 200 (re-rendered
  form) and does NOT set an authenticated session.
- GET "/admin/reset-password/not-a-real-token" redirects to
  "/admin/forgot-password" with a flashed error, rather than raising an
  unhandled exception.
- A token generated with max_age=3600 successfully resets the password
  when consumed immediately, and a manually-expired token (mocked
  time) is rejected.
"""
