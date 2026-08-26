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
