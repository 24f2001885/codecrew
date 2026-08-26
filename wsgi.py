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
