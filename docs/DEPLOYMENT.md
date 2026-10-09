# CodeCrews Production Deployment Guide

This guide describes how to deploy CodeCrews to a production environment using Docker Compose, PostgreSQL 16, Nginx, and Gunicorn.

---

## 1. Prerequisites

- **Host Operating System:** Linux (Ubuntu 22.04 LTS or newer recommended)
- **Container Tools:** Docker Engine 24.0+ and Docker Compose v2.20+
- **Domain & DNS:** A and AAAA records pointing to host IP address
- **SSL Certificates:** TLS certificates issued via Certbot or existing provider

---

## 2. First Deploy

### Step 1: Clone Repository & Create Environment Configuration
```bash
git clone https://github.com/24f2001885/codecrew.git /opt/codecrews
cd /opt/codecrews
cp .env.example .env
```

Ensure `.env` contains:
```bash
FLASK_ENV=production
SECRET_KEY=generate-a-strong-random-key-here
DATABASE_URL=postgresql://codecrews:codecrews_secret@db:5432/codecrews
SESSION_COOKIE_SECURE=True
TRUSTED_PROXY_COUNT=1
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=notifications@example.com
MAIL_PASSWORD=smtp-app-password
MAIL_DEFAULT_SENDER=CodeCrews <notifications@example.com>
```

### Step 2: Build Images and Run Database Migrations
```bash
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml run --rm web flask db upgrade
docker compose -f docker-compose.prod.yml run --rm web python seed.py
```

### Step 3: Launch All Services
```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## 3. Moving from SQLite to PostgreSQL

When migrating existing SQLite data to production PostgreSQL:
1. Dump data from development SQLite database:
   ```bash
   sqlite3 instance/codecrews.db .dump > dump_sqlite.sql
   ```
2. Configure PostgreSQL credentials in `.env` (`DATABASE_URL=postgresql://...`).
3. Apply all schema migrations on an empty PostgreSQL database:
   ```bash
   docker compose -f docker-compose.prod.yml run --rm web flask db upgrade
   ```
4. Test and verify migrations with the Postgres container before redirecting live traffic.

---

## 4. Backups

Perform daily automated backups of both the PostgreSQL database and uploaded files:

### Database Backup
```bash
docker compose -f docker-compose.prod.yml exec -T db pg_dump -U codecrews -d codecrews -F c > /backups/db_$(date +%Y%m%d_%H%M%S).dump
```

### Uploaded Files Backup
Backup both public assets and private document uploads:
```bash
tar -czf /backups/uploads_public_$(date +%Y%m%d).tar.gz -C /opt/codecrews/app/static uploads
docker compose -f docker-compose.prod.yml run --rm web tar -czf /tmp/private.tar.gz -C /code/instance private_uploads
```

---

## 5. Rotating Secrets

1. **SECRET_KEY:** Generate a new 64-character token (`python -c "import secrets; print(secrets.token_hex(32))"`). Update `.env` and restart web container. Note: existing active sessions will be invalidated.
2. **SMTP Credentials:** Generate a new App Password in your email provider and update `MAIL_PASSWORD`.
3. **LEGACY NOTICE:** Remember that credentials from the legacy `server.js` implementation must be revoked and rotated immediately upon transitioning to the Python/Flask stack.

---

## 6. Scheduled Tasks

Setup host cron jobs (`crontab -e`) for regular maintenance tasks:
```bash
# Nightly backup at 02:00 AM
0 2 * * * /opt/codecrews/scripts/backup.sh > /var/log/codecrews_backup.log 2>&1

# Database vacuuming every Sunday at 03:00 AM
0 3 * * 0 docker compose -f /opt/codecrews/docker-compose.prod.yml exec -T db vacuumdb -U codecrews -d codecrews --analyze
```
*(Note: Automated purge commands for soft-deleted items will arrive in milestone P8).*

---

## 7. Rollback Procedure

If a release needs to be rolled back to the previous stable release tag:
```bash
# Checkout previous release tag
git checkout v5

# Rebuild containers
docker compose -f docker-compose.prod.yml build web

# Revert database migrations if applicable
docker compose -f docker-compose.prod.yml run --rm web flask db downgrade

# Restart web service
docker compose -f docker-compose.prod.yml up -d web
```

---

## 8. Troubleshooting & Log Locations

- **Flask / Gunicorn App Logs:** `docker compose -f docker-compose.prod.yml logs -f web`
- **Nginx Access & Error Logs:** `docker compose -f docker-compose.prod.yml logs -f proxy`
- **PostgreSQL Logs:** `docker compose -f docker-compose.prod.yml logs -f db`

---

## 9. Verification Checklist (Fresh Machine)

- [ ] `.env` created with production secrets and non-default database password.
- [ ] `docker compose -f docker-compose.prod.yml config` validates without errors.
- [ ] Database healthy and migrations applied successfully via `flask db upgrade`.
- [ ] Gunicorn healthcheck reports healthy on container startup.
- [ ] Homepage loads with HTTP 200 and security headers (`X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`).
- [ ] Admin login accessible and protected under rate limiter.
- [ ] Direct access to `/static/../instance/private_uploads` is blocked by proxy with 404/deny.
