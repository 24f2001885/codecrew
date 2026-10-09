import os
import uuid
from pathlib import Path
from flask import current_app, abort, send_file
from app.services.uploads import UploadError

ATTACHMENT_EXTENSIONS = {".pdf", ".docx"}
RESUME_EXTENSIONS = {".pdf"}
ALLOWED_PRIVATE_SUBFOLDERS = {"requests", "applications"}


def private_root() -> Path:
    folder = current_app.config.get("PRIVATE_UPLOAD_FOLDER", "instance/private_uploads")
    root = Path(folder).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def save_private(file_storage, subfolder: str, allowed_extensions: set) -> str:
    if not file_storage or not getattr(file_storage, "filename", None):
        return None

    if subfolder not in ALLOWED_PRIVATE_SUBFOLDERS:
        raise ValueError(f"Disallowed private subfolder '{subfolder}'. Allowed: {ALLOWED_PRIVATE_SUBFOLDERS}")

    filename = file_storage.filename.strip()
    ext = os.path.splitext(filename)[1].lower()
    if ext not in allowed_extensions:
        raise UploadError(f"Extension '{ext}' is not allowed for private uploads.")

    # Read header bytes to verify magic numbers
    header = file_storage.read(16)
    if ext == ".pdf" and not header.startswith(b"%PDF-"):
        raise UploadError("File header does not match expected PDF signature.")
    if ext == ".docx" and not header.startswith(b"PK\x03\x04"):
        raise UploadError("File header does not match expected DOCX signature.")

    # Check file size
    file_storage.seek(0, os.SEEK_END)
    file_size = file_storage.tell()
    file_storage.seek(0)

    max_bytes = current_app.config.get("MAX_CONTENT_LENGTH", 5 * 1024 * 1024)
    if file_size > max_bytes:
        raise UploadError(f"File size ({file_size} bytes) exceeds maximum limit ({max_bytes} bytes).")

    # Generate random unique filename (do NOT preserve original filename for confidential files)
    stored_name = f"{uuid.uuid4().hex}{ext}"

    dest_dir = private_root() / subfolder
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / stored_name

    file_storage.save(str(dest_path))
    file_storage.seek(0)

    return stored_name


def delete_private(subfolder: str, stored_name: str) -> bool:
    if not stored_name or ".." in stored_name:
        return False

    subfolder_dir = (private_root() / subfolder).resolve()
    target_path = (subfolder_dir / stored_name).resolve()

    # Prevent directory traversal
    try:
        target_path.relative_to(subfolder_dir)
    except ValueError:
        return False

    if target_path.exists() and target_path.is_file():
        try:
            target_path.unlink()
            return True
        except OSError:
            return False
    return False


def send_private(subfolder: str, stored_name: str, download_name: str):
    if not stored_name or ".." in stored_name:
        abort(404)

    subfolder_dir = (private_root() / subfolder).resolve()
    target_path = (subfolder_dir / stored_name).resolve()

    try:
        target_path.relative_to(subfolder_dir)
    except ValueError:
        abort(404)

    if not target_path.exists() or not target_path.is_file():
        abort(404)

    resp = send_file(
        str(target_path),
        as_attachment=True,
        download_name=download_name,
    )
    resp.headers["X-Content-Type-Options"] = "nosniff"
    return resp
