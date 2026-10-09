"""
app.forms package: WTForms definitions.
"""
from wtforms.validators import ValidationError
from app.forms.auth_forms import LoginForm, ForgotPasswordForm, ResetPasswordForm


def parse_tag_string(raw_string, max_tags=20, max_length=30):
    """
    Parses comma-separated tag string:
    lowercase, stripped, unique while preserving order, length validated.
    """
    if not raw_string:
        return []

    tags = []
    seen = set()
    for item in raw_string.split(","):
        tag = item.strip().lower()
        if not tag:
            continue
        if len(tag) > max_length:
            raise ValidationError(f"Tag '{tag}' exceeds maximum allowed length of {max_length} characters.")
        if tag not in seen:
            seen.add(tag)
            tags.append(tag)

    if len(tags) > max_tags:
        raise ValidationError(f"Cannot specify more than {max_tags} tags.")

    return tags


__all__ = ["LoginForm", "ForgotPasswordForm", "ResetPasswordForm", "parse_tag_string"]
