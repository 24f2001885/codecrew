import io
import pytest
from app.services.uploads import save_upload, delete_upload, UploadError
from app.services.slugs import slugify, unique_slug
from app.models.group import Group
from app.extensions import db
from werkzeug.datastructures import FileStorage


def test_slugify():
    assert slugify("Acme Devs!!") == "acme-devs"
    assert slugify("  Hello World 2026!  ") == "hello-world-2026"
    assert slugify("---") == "item"
    assert slugify("") == "item"


def test_unique_slug(app):
    with app.app_context():
        g1 = Group(name="Alpha Squad", slug=unique_slug(Group, "Alpha Squad"))
        db.session.add(g1)
        db.session.commit()

        # Duplicate should append -2
        slug2 = unique_slug(Group, "Alpha Squad")
        assert slug2 == "alpha-squad-2"

        # Exclude existing id allows keeping its own slug
        slug_self = unique_slug(Group, "Alpha Squad", exclude_id=g1.id)
        assert slug_self == "alpha-squad"


def test_upload_header_sniffing(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.app_context():
        # Valid PNG header (\x89PNG\r\n\x1a\n)
        png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        valid_png = FileStorage(stream=io.BytesIO(png_content), filename="test.png")
        path = save_upload(valid_png, "logos", "image")
        assert path.startswith("uploads/logos/")

        # Fake text file pretending to be PNG
        fake_png = FileStorage(stream=io.BytesIO(b"This is just plain text, not a PNG"), filename="fake.png")
        with pytest.raises(UploadError, match="header"):
            save_upload(fake_png, "logos", "image")

        # Valid PDF header (%PDF-)
        pdf_content = b"%PDF-1.4 sample content"
        valid_pdf = FileStorage(stream=io.BytesIO(pdf_content), filename="doc.pdf")
        pdf_path = save_upload(valid_pdf, "resumes", "pdf")
        assert pdf_path.startswith("uploads/resumes/")


def test_upload_path_traversal_prevention(app, tmp_path):
    app.config["UPLOAD_FOLDER"] = str(tmp_path)
    with app.app_context():
        valid_png = FileStorage(stream=io.BytesIO(b"\x89PNG\r\n\x1a\n"), filename="test.png")
        with pytest.raises(ValueError, match="Disallowed upload subfolder"):
            save_upload(valid_png, "../dangerous", "image")

        assert delete_upload("../../etc/passwd") is False
        assert delete_upload("/etc/hosts") is False
