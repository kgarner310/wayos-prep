"""File upload security — type and size validation."""

from fastapi import HTTPException, UploadFile

from app.core.config import settings

ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf",
}


def validate_upload(file: UploadFile) -> None:
    """Validate file type and size. Raises HTTPException on rejection."""
    # Check extension
    filename = (file.filename or "").lower()
    ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            415,
            f"File type '.{ext}' not allowed. Accepted: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    # Check content type
    ct = (file.content_type or "").lower()
    if ct and ct not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            415,
            f"Content type '{ct}' not allowed. Accepted: {', '.join(sorted(ALLOWED_CONTENT_TYPES))}",
        )

    # Check size — read position, check, and reset
    file.file.seek(0, 2)  # seek to end
    size = file.file.tell()
    file.file.seek(0)  # reset to start

    if size > settings.MAX_UPLOAD_SIZE_BYTES:
        max_mb = settings.MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
        raise HTTPException(
            413,
            f"File too large ({size / (1024*1024):.1f}MB). Maximum: {max_mb:.0f}MB",
        )
