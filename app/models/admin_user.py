"""
FILE PURPOSE: AdminUser model — full columns (TDR §4 table: admin_users).
Also needs to satisfy Flask-Login's UserMixin contract, since
login_manager (app/extensions.py) authenticates against this model.

PROMPT FOR LLM IMPLEMENTATION:
1. Import uuid, datetime (timezone), db from app.extensions, and
   UserMixin from flask_login.
2. class AdminUser(db.Model, UserMixin) with __tablename__ = "admin_users".
3. Columns exactly per TDR §4: id (String(36) UUID PK, default
   lambda: str(uuid.uuid4())); username (String(80), unique, not null);
   password_hash (String(255), not null); created_at (DateTime, not
   null, default datetime.now(timezone.utc)).
4. UserMixin gives get_id()/is_authenticated/etc for free — since id is
   already a string, no override needed.
5. __repr__ returning "<AdminUser {self.username}>".

DEBUGGING:
# print(f"[DEBUG] AdminUser stub -> full model registered: {AdminUser.__tablename__}")

OFFLINE DOCKER TEST CASES:
- AdminUser(username="admin", password_hash="x").get_id() returns the
  row's UUID string once persisted (id is not None after db.session.add
  + commit + refresh).
- AdminUser.query.filter_by(username="admin").first() round-trips
  correctly after seed.py creates a row.
- The `username` column rejects a duplicate value at the DB level
  (unique constraint) when two rows share a username.
"""
