"""
FILE PURPOSE: P1 acceptance tests — matches the Master Project
Blueprint's P1 Goal verbatim ("the admin can log in, out, and reset a
forgotten password; no manageable content exists yet"). Depends on
Piyush's AdminUser model, Utkarsh's auth routes/forms/mailer, and
Harshlata's templates all being merged into the branch under test.

PROMPT FOR LLM IMPLEMENTATION:
1. test_login_page_loads(client): GET "/admin/login" returns 200 and
   the body contains a csrf_token input.
2. test_login_success_redirects_to_dashboard(client, admin_user,
   admin_password): POST "/admin/login" with the correct
   username/password redirects (302) toward "/admin/dashboard".
3. test_login_failure_shows_inline_error(client, admin_user): POST
   "/admin/login" with a wrong password returns 200 (re-rendered form)
   and the body contains an "alert-danger" (or equivalent error) marker,
   not a raw exception.
4. test_dashboard_requires_login(client): GET "/admin/dashboard"
   without a session redirects (302) to "/admin/login".
5. test_logout_clears_session(logged_in_client): POST "/admin/logout"
   then GET "/admin/dashboard" redirects to "/admin/login" again
   (proves the session was actually cleared, not just the response
   flashed).
6. test_forgot_password_always_flashes_generic_message(client,
   admin_user): POST "/admin/forgot-password" with a username that does
   NOT exist still redirects with the same generic flash as a real
   username would (no user-enumeration leak, per TDR §6).
7. test_reset_password_with_invalid_token_redirects(client): GET
   "/admin/reset-password/garbage-token" redirects to
   "/admin/forgot-password" rather than raising.
8. test_all_models_registered(app): within an app context, assert
   {"admin_users","groups","members","projects","blog_posts",
   "contact_messages","project_requests","site_settings"} is a subset of
   db.metadata.tables.keys() (carried forward from P0's stub-model test,
   now verifying the FULL models load without error).

DEBUGGING:
# print("[DEBUG] running P1 acceptance tests")

OFFLINE DOCKER TEST CASES:
- All eight tests above pass with zero network access (MAIL_SUPPRESS_SEND=True
  suppresses the password-reset email's actual send), entirely against
  the SQLite test database created by conftest.py, once all five task
  branches are integrated into phase1.
"""
