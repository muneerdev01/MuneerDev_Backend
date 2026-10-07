"""Content-aware validation for uploaded image and digital product files."""

from pathlib import PurePath

from fastapi import HTTPException, status

MAX_UPLOAD_BYTES = 100 * 1024 * 1024

_ALLOWED = {
    "image": {
        ".png": ({"image/png"}, lambda data: data.startswith(b"\x89PNG\r\n\x1a\n")),
        ".jpg": ({"image/jpeg", "image/jpg"}, lambda data: data.startswith(b"\xff\xd8\xff")),
        ".jpeg": ({"image/jpeg", "image/jpg"}, lambda data: data.startswith(b"\xff\xd8\xff")),
        ".webp": (
            {"image/webp"},
            lambda data: len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP",
        ),
    },
    "product_file": {
        ".pdf": ({"application/pdf"}, lambda data: data.startswith(b"%PDF-")),
        ".zip": (
            {"application/zip", "application/x-zip-compressed"},
            lambda data: data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08")),
        ),
    },
}


def validate_upload(filename: str | None, content_type: str | None, content: bytes, kind: str) -> str:
    """Reject mismatched extensions, declared MIME types, signatures, and oversized files."""
    if kind not in _ALLOWED:
        raise ValueError(f"Unsupported upload kind: {kind}")
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Maximum upload size is 100 MB.",
        )

    extension = PurePath(filename or "").suffix.lower()
    allowed_types = _ALLOWED[kind].get(extension)
    if allowed_types is None:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File extension is not allowed for {kind} uploads.",
        )

    allowed_mime_types, signature_matches = allowed_types
    declared_type = (content_type or "").split(";", maxsplit=1)[0].strip().lower()
    if declared_type not in allowed_mime_types or not signature_matches(content):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="File extension, content type, or file contents do not match.",
        )
    return "image/jpeg" if extension in {".jpg", ".jpeg"} else declared_type
