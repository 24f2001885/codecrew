import os
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from app.extensions import db
from app.models.coder_application import CoderApplication
from app.services.private_files import private_root


def test_purge_unverified_applications_cli(app):
    runner = app.test_cli_runner()

    with app.app_context():
        # Setup private upload resume file
        p_root = private_root() / "applications"
        p_root.mkdir(parents=True, exist_ok=True)
        test_resume = p_root / "old_unverified_resume.pdf"
        test_resume.write_bytes(b"%PDF-1.4 dummy resume")

        # 1. Old unverified (45 days old) -> MUST BE PURGED
        old_unverified = CoderApplication(
            name="Old Unverified",
            email="old.unverified@example.com",
            project_types=["web_app"],
            alerts_consent=True,
            email_verified_at=None,
            resume_pdf="old_unverified_resume.pdf",
            created_at=datetime.utcnow() - timedelta(days=45),
            status="pending",
        )

        # 2. Recent unverified (5 days old) -> MUST BE KEPT
        recent_unverified = CoderApplication(
            name="Recent Unverified",
            email="recent.unverified@example.com",
            project_types=["web_app"],
            alerts_consent=True,
            email_verified_at=None,
            created_at=datetime.utcnow() - timedelta(days=5),
            status="pending",
        )

        # 3. Old verified (60 days old) -> MUST BE KEPT
        old_verified = CoderApplication(
            name="Old Verified",
            email="old.verified@example.com",
            project_types=["web_app"],
            alerts_consent=True,
            email_verified_at=datetime.utcnow() - timedelta(days=59),
            created_at=datetime.utcnow() - timedelta(days=60),
            status="pending",
        )

        db.session.add_all([old_unverified, recent_unverified, old_verified])
        db.session.commit()

        old_unverified_id = old_unverified.id
        recent_unverified_id = recent_unverified.id
        old_verified_id = old_verified.id

    result = runner.invoke(args=["purge-unverified-applications", "--days", "30"])
    assert result.exit_code == 0
    assert "Purged 1 unverified application" in result.output

    with app.app_context():
        # Verify DB rows
        assert db.session.get(CoderApplication, old_unverified_id) is None
        assert db.session.get(CoderApplication, recent_unverified_id) is not None
        assert db.session.get(CoderApplication, old_verified_id) is not None

        # Verify private resume file was cleaned up from filesystem
        assert not test_resume.exists()


def test_move_request_attachments_cli(app):
    runner = app.test_cli_runner()

    with app.app_context():
        # Create legacy static requests upload folder with a file
        legacy_dir = Path(app.config.get("UPLOAD_FOLDER", "app/static/uploads")) / "requests"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        legacy_file = legacy_dir / "legacy_attachment.pdf"
        legacy_file.write_bytes(b"%PDF-1.4 legacy attachment")

        # Run move CLI command
        result = runner.invoke(args=["move-request-attachments"])
        assert result.exit_code == 0
        assert "Moved" in result.output

        # Verify file exists in private storage and not in legacy static directory
        target_file = private_root() / "requests" / "legacy_attachment.pdf"
        assert target_file.exists()
        assert not legacy_file.exists()

        # Clean up
        target_file.unlink(missing_ok=True)
