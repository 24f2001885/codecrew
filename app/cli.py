import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import click
from app.extensions import db
from app.models.coder_application import CoderApplication
from app.services.private_files import delete_private, private_root


def register_cli_commands(app):
    @app.cli.command("purge-unverified-applications")
    @click.option("--days", default=None, type=int, help="Override TTL days threshold")
    def purge_unverified_applications(days):
        """Purges applications unverified for more than TTL days along with resumes."""
        ttl_days = days if days is not None else app.config.get("UNVERIFIED_APPLICATION_TTL_DAYS", 30)
        cutoff = datetime.utcnow() - timedelta(days=ttl_days)

        old_unverified = CoderApplication.query.filter(
            CoderApplication.email_verified_at.is_(None),
            CoderApplication.created_at < cutoff,
        ).all()

        purged_count = 0
        for record in old_unverified:
            if record.resume_pdf:
                delete_private("applications", record.resume_pdf)
            db.session.delete(record)
            purged_count += 1

        db.session.commit()
        click.echo(f"Purged {purged_count} unverified application(s) older than {ttl_days} days.")

    @app.cli.command("move-request-attachments")
    def move_request_attachments():
        """Moves legacy request attachments from public static uploads to private storage."""
        upload_folder = app.config.get("UPLOAD_FOLDER", "app/static/uploads")
        legacy_dir = Path(upload_folder) / "requests"
        target_dir = private_root() / "requests"
        target_dir.mkdir(parents=True, exist_ok=True)

        if not legacy_dir.exists():
            click.echo("Legacy requests directory not found. Nothing to move.")
            return

        moved_count = 0
        for item in legacy_dir.iterdir():
            if item.is_file():
                dest = target_dir / item.name
                shutil.move(str(item), str(dest))
                moved_count += 1

        click.echo(f"Moved {moved_count} file(s) to private storage: {target_dir}")
