"""
FILE PURPOSE: Marks app/models as a package; documents the P0 stub
strategy.

PROMPT FOR LLM IMPLEMENTATION:
1. Add a module docstring explaining that every sibling model in P0 is a
   bare stub (table name + primary key only) so Flask-Migrate's history
   starts clean, and that full columns per TDR §4 land in P1.
2. No imports or logic needed here — sibling modules are imported
   explicitly by app/__init__.py (Abhinav's task-abhinav-app-core).

DEBUGGING:
# print("[DEBUG] app.models package imported")

OFFLINE DOCKER TEST CASES:
- `import app.models` does not raise.
"""
