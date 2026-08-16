"""Normalize image bytes for Discord guild banner / icon uploads.

Discord often replies with HTTP 500 ``internal_error`` for bad dimensions,
alpha PNGs, or odd encodings — not Missing Permissions. Prefer RGB JPEG.
"""

from __future__ import annotations

import io

from PIL import Image

BANNER_W = 960
BANNER_H = 540
ICON_SIZE = 512
JPEG_QUALITY = 90
MAX_UPLOAD_BYTES = 8 * 1024 * 1024


def image_to_discord_jpeg(img: Image.Image, *, size: tuple[int, int] | None = None) -> bytes:
    """Flatten alpha onto black, optionally resize, encode as RGB JPEG."""
    work = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
    if work.mode == "RGBA":
        background = Image.new("RGB", work.size, (0, 0, 0))
        background.paste(work, mask=work.split()[-1])
        work = background
    else:
        work = work.convert("RGB")
    if size is not None and work.size != size:
        work = work.resize(size, Image.LANCZOS)
    buf = io.BytesIO()
    work.save(buf, format="JPEG", quality=JPEG_QUALITY, optimize=True)
    data = buf.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        buf = io.BytesIO()
        work.save(buf, format="JPEG", quality=75, optimize=True)
        data = buf.getvalue()
    return data


def ensure_discord_banner_bytes(raw: bytes) -> bytes:
    """Re-encode arbitrary image bytes to a Discord-safe 960×540 JPEG."""
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        return image_to_discord_jpeg(img, size=(BANNER_W, BANNER_H))


def ensure_discord_icon_bytes(raw: bytes) -> bytes:
    """Re-encode icon bytes to a square RGB JPEG."""
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        cropped = img.crop((left, top, left + side, top + side))
        return image_to_discord_jpeg(cropped, size=(ICON_SIZE, ICON_SIZE))


def format_discord_http_error(exc: Exception) -> dict:
    """Extract status / code / text from discord.HTTPException (or similar)."""
    status = getattr(exc, "status", None)
    code = getattr(exc, "code", None)
    text = getattr(exc, "text", None)
    if not text:
        text = str(exc)
    return {
        "status": int(status) if status is not None else None,
        "code": int(code) if isinstance(code, int) or (isinstance(code, str) and str(code).isdigit()) else code,
        "text": str(text)[:500],
    }


def classify_discord_asset_error(detail: dict | None) -> str:
    """Map Discord error detail to a short machine reason for the dashboard."""
    if not detail:
        return "discord_rejected"
    status = detail.get("status")
    code = detail.get("code")
    text = (detail.get("text") or "").lower()
    if status == 429 or code == 429:
        return "rate_limited"
    if status == 403 or code in (50013, 50001):
        return "missing_permissions"
    if any(token in text for token in ("premium", "boost", "banner feature", "nitro", "guild feature")):
        return "boost_required"
    if status == 500 or "internal" in text:
        return "invalid_image"
    if status == 400 or code in (50035, 50138):
        return "invalid_image"
    return "discord_rejected"
