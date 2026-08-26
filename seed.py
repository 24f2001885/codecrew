"""
FILE PURPOSE: Database seed CLI (full logic lands in P1 — this milestone
only wires up the entrypoint per TDR §13's operational runbook).

PROMPT FOR LLM IMPLEMENTATION:
1. Import create_app from app.
2. Define run(): builds the app via create_app(), enters an
   app.app_context(), and for P0 only prints a message confirming the app
   context loads (e.g. "Seed script scaffolded (P0). Super-admin + sample
   data land in P1.") — no AdminUser/Group creation yet, that's P1 scope
   (PDR §5.2: seeded from ADMIN_SEED_USERNAME/ADMIN_SEED_PASSWORD, never a
   UI form).
3. `if __name__ == "__main__": run()`.

DEBUGGING:
# print("[DEBUG] seed.py invoked — no-op until P1 implements AdminUser + sample data")

OFFLINE DOCKER TEST CASES:
- Running `python seed.py` exits 0 and prints a message, with no database
  writes attempted yet.
"""
