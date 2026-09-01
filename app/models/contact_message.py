"""
FILE PURPOSE: ContactMessage model — full columns (TDR §4 table:
contact_messages). group_id is NOT NULL as of v2 — no more nullable
"suggestion" case (PDR §3.2, TDR §4).

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions.
2. class ContactMessage(db.Model) with __tablename__ = "contact_messages".
3. Columns exactly per TDR §4: id (UUID PK); group_id (String(36) FK ->
   groups.id, NOT NULL, indexed, ondelete="CASCADE"); name (String(120),
   not null); email (String(255), not null); subject (String(200),
   nullable); message (Text, not null); is_read (Boolean, not null,
   default False); created_at (DateTime, not null, default now,
   indexed — "for inbox sort" per TDR §4).
4. __repr__ returning "<ContactMessage from {self.name}>".

DEBUGGING:
# print(f"[DEBUG] ContactMessage full model registered: {ContactMessage.__tablename__}")

OFFLINE DOCKER TEST CASES:
- Constructing a ContactMessage with group_id=None and attempting to
  persist it raises an IntegrityError (NOT NULL enforcement — this is
  the explicit v2 schema change from TDR §4).
- `is_read` defaults to False on a freshly created row.
- Querying ContactMessage ordered by created_at descending returns the
  most recently created row first (supports the inbox sort use case).
"""
