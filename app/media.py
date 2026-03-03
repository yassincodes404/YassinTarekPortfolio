"""Media upload handling: file validation, saving, thumbnail generation."""

import uuid
import subprocess
import shutil
from pathlib import Path
from PIL import Image
from app.config import settings


THUMBNAIL_MAX_WIDTH = 320


def validate_upload(filename: str, content_type: str, size: int) -> str | None:
    """Validate upload. Returns error message or None if valid."""
    all_allowed = settings.ALLOWED_IMAGE_TYPES + settings.ALLOWED_VIDEO_TYPES
    if content_type not in all_allowed:
        return f"File type '{content_type}' is not allowed."

    if content_type in settings.ALLOWED_IMAGE_TYPES and size > settings.MAX_IMAGE_SIZE:
        return f"Image too large. Max size: {settings.MAX_IMAGE_SIZE // (1024*1024)}MB."

    if content_type in settings.ALLOWED_VIDEO_TYPES and size > settings.MAX_VIDEO_SIZE:
        return f"Video too large. Max size: {settings.MAX_VIDEO_SIZE // (1024*1024)}MB."

    return None


def save_upload(file_bytes: bytes, original_filename: str, content_type: str) -> dict:
    """Save uploaded file to disk. Returns dict with file info."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.upload_path / unique_name
    file_path.write_bytes(file_bytes)

    result = {
        "filename": unique_name,
        "original_filename": original_filename,
        "url": f"/uploads/{unique_name}",
        "mime": content_type,
        "size_bytes": len(file_bytes),
        "thumbnail_url": None,
    }

    # Generate thumbnail
    if content_type in settings.ALLOWED_IMAGE_TYPES:
        thumb_url = _create_image_thumbnail(file_path, unique_name)
        result["thumbnail_url"] = thumb_url
    elif content_type in settings.ALLOWED_VIDEO_TYPES:
        thumb_url = _create_video_thumbnail(file_path, unique_name)
        result["thumbnail_url"] = thumb_url

    return result


def _create_image_thumbnail(file_path: Path, unique_name: str) -> str | None:
    """Create resized thumbnail for an image. Returns URL or None."""
    try:
        thumb_name = f"thumb_{unique_name.rsplit('.', 1)[0]}.webp"
        thumb_path = settings.upload_path / thumb_name
        with Image.open(file_path) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            ratio = THUMBNAIL_MAX_WIDTH / img.width
            new_height = int(img.height * ratio)
            if img.width > THUMBNAIL_MAX_WIDTH:
                img = img.resize((THUMBNAIL_MAX_WIDTH, new_height), Image.LANCZOS)
            img.save(thumb_path, "WEBP", quality=80)
        return f"/uploads/{thumb_name}"
    except Exception:
        return None


def _create_video_thumbnail(file_path: Path, unique_name: str) -> str | None:
    """Extract a frame from video using ffmpeg. Returns URL or None."""
    try:
        if not shutil.which("ffmpeg"):
            return None
        thumb_name = f"thumb_{unique_name.rsplit('.', 1)[0]}.jpg"
        thumb_path = settings.upload_path / thumb_name
        subprocess.run(
            [
                "ffmpeg", "-i", str(file_path),
                "-ss", "00:00:01",
                "-vframes", "1",
                "-vf", f"scale={THUMBNAIL_MAX_WIDTH}:-1",
                str(thumb_path),
                "-y",
            ],
            capture_output=True,
            timeout=30,
        )
        if thumb_path.exists():
            return f"/uploads/{thumb_name}"
        return None
    except Exception:
        return None


def delete_upload(filename: str) -> bool:
    """Delete a file and its thumbnail from disk."""
    file_path = settings.upload_path / filename
    if file_path.exists():
        file_path.unlink()

    # Try to delete thumbnail variants
    stem = filename.rsplit(".", 1)[0]
    for ext in (".webp", ".jpg"):
        thumb = settings.upload_path / f"thumb_{stem}{ext}"
        if thumb.exists():
            thumb.unlink()

    return True
