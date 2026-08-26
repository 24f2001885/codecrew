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
