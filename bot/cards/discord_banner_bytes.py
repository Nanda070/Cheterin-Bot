"""Normalize image bytes for Discord guild banner / icon uploads.

Discord often replies with HTTP 500 ``internal_error`` when it cannot decode
the image payload (odd JPEG progressive/subsampling, alpha PNG, wrong size),
not when Manage Guild / boost is missing. Prefer RGB PNG; fall back to JPEG.
"""

from __future__ import annotations

import io
import logging
from typing import Literal

from PIL import Image

logger = logging.getLogger("discord_banner_bytes")

BANNER_W = 960
BANNER_H = 540
ICON_SIZE = 512
JPEG_QUALITY = 90
MAX_UPLOAD_BYTES = 8 * 1024 * 1024

AssetFormat = Literal["png", "jpeg"]


def _to_rgb(img: Image.Image) -> Image.Image:
    """Flatten any alpha onto black and return an RGB image (no ICC / EXIF)."""
    work = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
    if work.mode == "RGBA":
        background = Image.new("RGB", work.size, (0, 0, 0))
        background.paste(work, mask=work.split()[-1])
        return background
    return work.convert("RGB")


def _resize(work: Image.Image, size: tuple[int, int] | None) -> Image.Image:
    if size is not None and work.size != size:
        return work.resize(size, Image.LANCZOS)
    return work


def image_to_discord_png(img: Image.Image, *, size: tuple[int, int] | None = None) -> bytes:
    """Encode as RGB PNG (no alpha, no progressive quirks)."""
    work = _resize(_to_rgb(img), size)
    buf = io.BytesIO()
    work.save(buf, format="PNG", optimize=False, compress_level=6)
    data = buf.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        return image_to_discord_jpeg(work, size=None)
    return data


def image_to_discord_jpeg(img: Image.Image, *, size: tuple[int, int] | None = None) -> bytes:
    """Encode as baseline RGB JPEG (4:4:4, non-progressive, no EXIF)."""
    work = _resize(_to_rgb(img), size)
    buf = io.BytesIO()
    work.save(
        buf,
        format="JPEG",
        quality=JPEG_QUALITY,
        optimize=False,
        progressive=False,
        subsampling=0,
    )
    data = buf.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        buf = io.BytesIO()
        work.save(
            buf,
            format="JPEG",
            quality=75,
            optimize=False,
            progressive=False,
            subsampling=0,
        )
        data = buf.getvalue()
    return data


def image_to_discord_bytes(
    img: Image.Image,
    *,
    size: tuple[int, int] | None = None,
    prefer: AssetFormat = "png",
) -> bytes:
    """Encode for Discord uploads; PNG first by default."""
    if prefer == "jpeg":
        return image_to_discord_jpeg(img, size=size)
    return image_to_discord_png(img, size=size)


def ensure_discord_banner_bytes(raw: bytes, *, prefer: AssetFormat = "png") -> bytes:
    """Re-encode arbitrary image bytes to a Discord-safe 960×540 asset."""
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        data = image_to_discord_bytes(img, size=(BANNER_W, BANNER_H), prefer=prefer)
    _assert_banner_payload(data)
    return data


def ensure_discord_icon_bytes(raw: bytes, *, prefer: AssetFormat = "png") -> bytes:
    """Re-encode icon bytes to a square RGB asset Discord accepts for icons."""
    with Image.open(io.BytesIO(raw)) as img:
        img.load()
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        cropped = img.crop((left, top, left + side, top + side))
        return image_to_discord_bytes(cropped, size=(ICON_SIZE, ICON_SIZE), prefer=prefer)


def _assert_banner_payload(data: bytes) -> None:
    if not data:
        raise ValueError("empty_banner_payload")
    if len(data) > MAX_UPLOAD_BYTES:
        raise ValueError(f"banner_too_large:{len(data)}")
    is_png = data.startswith(b"\x89PNG\r\n\x1a\n")
    is_jpeg = data[:3] == b"\xff\xd8\xff"
    if not (is_png or is_jpeg):
        raise ValueError(f"bad_banner_magic:{data[:8]!r}")
    with Image.open(io.BytesIO(data)) as check:
        check.load()
        if check.size != (BANNER_W, BANNER_H):
            raise ValueError(f"bad_banner_size:{check.size}")
        if check.mode != "RGB":
            raise ValueError(f"bad_banner_mode:{check.mode}")


def describe_image_bytes(data: bytes) -> dict:
    """Return metadata useful for CLI / logs (size, format, magic)."""
    info: dict = {
        "bytes": len(data),
        "magic_hex": data[:8].hex() if data else "",
        "is_png": data.startswith(b"\x89PNG\r\n\x1a\n") if data else False,
        "is_jpeg": (data[:3] == b"\xff\xd8\xff") if data else False,
    }
    try:
        with Image.open(io.BytesIO(data)) as img:
            img.load()
            info.update(
                {
                    "width": img.size[0],
                    "height": img.size[1],
                    "mode": img.mode,
                    "format": img.format,
                    "progressive": bool(img.info.get("progressive")),
                }
            )
    except Exception as exc:
        info["open_error"] = str(exc)
    return info


def format_discord_http_error(exc: Exception) -> dict:
    """Extract status / code / text / response extras from discord.HTTPException."""
    status = getattr(exc, "status", None)
    code = getattr(exc, "code", None)
    text = getattr(exc, "text", None)
    if not text:
        text = str(exc)
    response = getattr(exc, "response", None)
    reason = getattr(response, "reason", None) if response is not None else None
    errors = getattr(exc, "_errors", None)
    detail = {
        "status": int(status) if status is not None else None,
        "code": int(code) if isinstance(code, int) or (isinstance(code, str) and str(code).isdigit()) else code,
        "text": str(text)[:500],
        "response_reason": str(reason)[:200] if reason else None,
    }
    if errors:
        detail["errors"] = str(errors)[:500]
    return detail


def classify_discord_asset_error(detail: dict | None) -> str:
    """Map Discord error detail to a short machine reason for the dashboard."""
    if not detail:
        return "discord_rejected"
    status = detail.get("status")
    code = detail.get("code")
    text = (detail.get("text") or "").lower()
    response_reason = (detail.get("response_reason") or "").lower()
    blob = f"{text} {response_reason}"
    if status == 429 or code == 429:
        return "rate_limited"
    if status == 403 or code in (50013, 50001):
        return "missing_permissions"
    if any(token in blob for token in ("premium", "boost", "banner feature", "nitro", "guild feature")):
        return "boost_required"
    if status == 500 or "internal" in blob:
        return "invalid_image"
    if status == 400 or code in (50035, 50138):
        return "invalid_image"
    return "discord_rejected"


def guild_has_banner_feature(guild) -> bool:
    """True when Discord exposes the BANNER guild feature (boost tier 2+)."""
    features = getattr(guild, "features", None) or ()
    try:
        return "BANNER" in features
    except TypeError:
        return False
