from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.config import settings

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "video/mp4", "video/quicktime", "video/webm"}
MAX_BYTES = 256 * 1024 * 1024
UPLOAD_DIR = Path("uploads")


async def save_upload(file: UploadFile) -> dict[str, str | int]:
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Unsupported media type")
    content = await file.read(MAX_BYTES + 1)
    if len(content) > MAX_BYTES:
        raise ValueError("File is larger than 256 MB")
    suffix = Path(file.filename or "media").suffix.lower()[:10]
    safe_stem = re.sub(r"[^a-zA-Z0-9]+", "_", Path(file.filename or "media").stem).strip("_")[:40] or "media"
    filename = f"{uuid4().hex}_{safe_stem}{suffix}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    destination = UPLOAD_DIR / filename
    destination.write_bytes(content)
    return {
        "filename": filename,
        "url": f"{settings.api_public_url.rstrip('/')}/uploads/{filename}",
        "content_type": file.content_type or "application/octet-stream",
        "size": len(content),
    }
