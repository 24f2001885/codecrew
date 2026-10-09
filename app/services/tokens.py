import hashlib
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from flask import current_app

SALTS = {
    "admin_reset": "admin-reset",
    "coder_invite": "coder-invite",
    "coder_reset": "coder-reset",
    "app_verify": "app-verify",
    "app_unsub": "app-unsub",
    "alert_interest": "alert-interest",
}


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"])


def fingerprint(password_hash):
    """Returns first 16 hex characters of SHA256 of the password hash."""
    return hashlib.sha256((password_hash or "").encode()).hexdigest()[:16]


def make_token(purpose, payload):
    """
    Signs and serializes a payload with the purpose-specific salt.
    Raises KeyError if purpose is not in SALTS.
    """
    if purpose not in SALTS:
        raise KeyError(f"Unknown token purpose: {purpose}")
    return _serializer().dumps(payload, salt=SALTS[purpose])


def read_token(purpose, token, max_age=None):
    """
    Deserializes and verifies token with purpose-specific salt.
    Returns payload dict or None if invalid/expired. Never raises for bad input.
    max_age=None disables age checks.
    """
    if purpose not in SALTS or not token:
        return None
    try:
        return _serializer().loads(token, salt=SALTS[purpose], max_age=max_age)
    except (BadSignature, SignatureExpired, Exception):
        return None


def max_age_for(purpose):
    """Returns the configured max_age in seconds for a given purpose."""
    config = current_app.config
    if purpose in ("admin_reset", "coder_reset"):
        return config.get("RESET_TOKEN_MAX_AGE", 3600)
    elif purpose == "coder_invite":
        return config.get("INVITE_TOKEN_MAX_AGE", 259200)
    elif purpose == "app_verify":
        return config.get("APPLICATION_VERIFY_MAX_AGE", 604800)
    elif purpose == "alert_interest":
        return config.get("INTERESTED_TOKEN_MAX_AGE", 2592000)
    elif purpose == "app_unsub":
        return None
    return None
