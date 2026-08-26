"""
FILE PURPOSE: Marks app/routes as a package; documents blueprint rollout
order across milestones.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring listing which blueprint lands in which
   milestone: public (P0), auth (P1), admin (P3), contact + requests
   (P4), api (P5).
2. No logic needed — app/__init__.py imports each blueprint module
   directly when it's registered.

DEBUGGING:
# print("[DEBUG] app.routes package imported")

OFFLINE DOCKER TEST CASES:
- `import app.routes` does not raise.
"""
