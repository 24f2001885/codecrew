import re
from app.extensions import db


def slugify(text):
    """
    Transforms text to a clean URL-friendly slug:
    lowercase, replaces non-alphanumerics with a single '-', limits to 120 chars, fallback to 'item'.
    """
    if not text:
        return "item"

    cleaned = text.lower().strip()
    cleaned = re.sub(r"[^a-z0-9]+", "-", cleaned)
    cleaned = cleaned.strip("-")

    if not cleaned:
        return "item"

    return cleaned[:120].rstrip("-")


def unique_slug(model, base, scope=None, exclude_id=None):
    """
    Generates a unique slug for a model.
    scope: dict of column filters, e.g. {'group_id': 'xyz'}
    exclude_id: optional ID to ignore when editing an existing record
    """
    raw_slug = slugify(base)
    candidate = raw_slug
    counter = 1

    while True:
        query = model.query.filter_by(slug=candidate)
        if scope:
            query = query.filter_by(**scope)
        if exclude_id is not None:
            query = query.filter(model.id != exclude_id)

        if not query.first():
            return candidate

        counter += 1
        candidate = f"{raw_slug}-{counter}"
