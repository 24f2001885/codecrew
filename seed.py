import argparse
from app import create_app
from app.extensions import db
from app.models.admin_user import AdminUser
from app.models.site_settings import SiteSettings
from app.services.sample_data import create_sample_data


def run():
    parser = argparse.ArgumentParser(description="CodeCrews database seeder")
    parser.add_argument("--sample", action="store_true", help="Populate sample groups, members, and projects")
    parser.add_argument("--sample-only", action="store_true", help="Populate sample data only without admin credentials")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()

        if not args.sample_only:
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

        if args.sample or args.sample_only:
            num = create_sample_data()
            print(f"[SEED] Created {num} sample groups.")


if __name__ == "__main__":
    run()
