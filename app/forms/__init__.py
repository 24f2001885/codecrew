"""
FILE PURPOSE: Marks app/forms as a package; documents form rollout order.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring noting Flask-WTF, CSRF-protected forms are
   added starting P1 (auth_forms.py) and P3 onward (group/member/project/
   blog/contact/request/settings forms), per the Master Project
   Blueprint's directory structure.
2. No logic needed in P0.

DEBUGGING:
# print("[DEBUG] app.forms package imported")

OFFLINE DOCKER TEST CASES:
- `import app.forms` does not raise.
"""
