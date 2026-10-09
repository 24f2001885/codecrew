import os
import uuid
from pathlib import Path
from werkzeug.utils import secure_filename
from flask import current_app

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
PDF_EXTENSIONS = {".pdf"}
ALLOWED_SUBFOLDERS = {"logos", "covers", "photos", "screenshots", "resumes"}


class UploadError(ValueError):
    """Raised when an uploaded file fails validation."""
    pass


def _sniff_header(header, kind, ext):
    if kind == "pdf":
        return header.startswith(b"%PDF-")
    elif kind == "image":
        if ext in (".jpg", ".jpeg"):
            return header.startswith(b"\xff\xd8\xff")
        elif ext == ".png":
            return header.startswith(b"\x89PNG\r\n\x1a\n") or header.startswith(b"\x89PNG")
        elif ext == ".webp":
            return header.startswith(b"RIFF") and b"WEBP" in header[:16]
    return False


def save_upload(file_storage, subfolder, kind):
    """
    Saves an uploaded file to current_app.config['UPLOAD_FOLDER']/<subfolder>.
    kind is 'image' or 'pdf'.
    Returns path relative to static folder (e.g. 'uploads/logos/...') or None if no file.
    """
    if file_storage is None or not getattr(file_storage, "filename", None) or file_storage.filename == "":
        return None

    if subfolder not in ALLOWED_SUBFOLDERS:
        raise ValueError(f"Disallowed upload subfolder: {subfolder}")

    original_filename = secure_filename(file_storage.filename)
    if not original_filename:
        original_filename = "upload"

    ext = Path(original_filename).suffix.lower()
    allowed_exts = IMAGE_EXTENSIONS if kind == "image" else PDF_EXTENSIONS

    if ext not in allowed_exts:
        raise UploadError(f"Disallowed file extension '{ext}'. Allowed: {', '.join(allowed_exts)}")

    # Header check
    header = file_storage.read(16)
    file_storage.seek(0)
    if not _sniff_header(header, kind, ext):
        raise UploadError(f"Corrupted or invalid {kind} file header.")

    # Size check
    file_storage.seek(0, os.SEEK_END)
    size = file_storage.tell()
    file_storage.seek(0)

    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 5242880)
    if size > max_bytes:
        raise UploadError(f"File exceeds maximum allowed size of {max_bytes // (1024 * 1024)} MB.")

    stored_name = f"{uuid.uuid4().hex[:12]}_{original_filename}"
    upload_root = Path(current_app.config["UPLOAD_FOLDER"])
    dest_dir = upload_root / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / stored_name
    file_storage.save(str(dest_path))

    return f"uploads/{subfolder}/{stored_name}"


def delete_upload(relative_path):
    """
    Safely deletes a file inside UPLOAD_FOLDER given its relative path (e.g. 'uploads/logos/...').
    Guards strictly against path traversal.
    """
    if not relative_path:
        return False

    upload_root = Path(current_app.config["UPLOAD_FOLDER"]).resolve()

    # If relative_path starts with 'uploads/', strip it to resolve against upload_root
    clean_path = relative_path
    if clean_path.startswith("uploads/"):
        clean_path = clean_path[len("uploads/"):]

    target = (upload_root / clean_path).resolve()

    try:
        # Must stay within upload_root
        target.relative_to(upload_root)
    except ValueError:
        return False

    if target.is_file():
        try:
            target.unlink()
            return True
        except OSError:
            return False

    return False


def replace_upload(old_path, new_file, subfolder, kind):
    """
    Saves new_file first, then deletes old_path only if saving succeeded.
    """
    new_path = save_upload(new_file, subfolder, kind)
    if new_path and old_path:
        delete_upload(old_path)
    return new_path
