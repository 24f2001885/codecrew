"""
FILE PURPOSE: Marks app/services as a package; documents service rollout
order.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring noting business logic kept out of routes lands
   as: uploads.py (P3), mailer.py (P4), search.py (P5).
2. No logic needed in P0.

DEBUGGING:
# print("[DEBUG] app.services package imported")

OFFLINE DOCKER TEST CASES:
- `import app.services` does not raise.
"""
