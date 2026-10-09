import sys
import os
from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser
from app.models.site_settings import SiteSettings


def seed_admin():
    app = create_app()
    with app.app_context():
        db.create_all()

        username = app.config.get("ADMIN_SEED_USERNAME", "admin")
        password = app.config.get("ADMIN_SEED_PASSWORD", "change-me-before-running-seed")

        admin = AdminUser.query.filter_by(username=username).first()
        if not admin:
            admin = AdminUser(username=username)
            admin.set_password(password)
            db.session.add(admin)
            db.session.commit()
            print(f"[SEED] Created super_admin user: {username}")
        else:
            print(f"[SEED] Super_admin user already exists: {username}")

        # Ensure site settings singleton exists
        SiteSettings.get_settings()

        if "--sample" in sys.argv:
            try:
                from app.services.sample_data import seed_sample_data
                seed_sample_data()
                print("[SEED] Sample data populated successfully.")
            except ImportError:
                print("[SEED] Sample data module not present in this milestone.")


if __name__ == "__main__":
    seed_admin()
