"""Banner + server icon rotation: per-guild settings and asset management."""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import bot.core.settings_db as settings_db

MODULE_NAME = "banner_rotation"

ASSETS_ROOT = Path("banner_rotation_assets")

MAX_IMAGE_BYTES = 8 * 1024 * 1024
INTERVAL_MIN = 15
INTERVAL_MAX = 2880
INTERVAL_DEFAULT = 60

BANNER_MODE_PLAYLIST = "playlist"
BANNER_MODE_DYNAMIC = "dynamic"
BANNER_MODE_BOTH = "both"
BANNER_MODES = frozenset({BANNER_MODE_PLAYLIST, BANNER_MODE_DYNAMIC, BANNER_MODE_BOTH})
DYNAMIC_WINDOW_DAYS_DEFAULT = 30
DYNAMIC_WINDOW_DAYS_MIN = 1
DYNAMIC_WINDOW_DAYS_MAX = 365


def _is_supported_image(raw: bytes) -> bool:
    if raw.startswith(b"\x89PNG") or raw.startswith(b"\xff\xd8\xff") or raw.startswith(b"GIF8"):
        return True
    # WebP: RIFF....WEBP
    return len(raw) >= 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP"


def _ext_for_image(raw: bytes) -> str:
    if raw.startswith(b"\x89PNG"):
        return "png"
    if raw.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if raw.startswith(b"GIF8"):
        return "gif"
    if len(raw) >= 12 and raw.startswith(b"RIFF") and raw[8:12] == b"WEBP":
        return "webp"
    return "bin"


# ──────────────────────── helpers ────────────────────────


def _short_id() -> str:
    return uuid.uuid4().hex[:12]


def _storage_dir(guild_id: int, kind: str) -> Path:
    d = ASSETS_ROOT / str(guild_id) / f"{kind}s"
    d.mkdir(parents=True, exist_ok=True)
    return d


def validate_image(raw: bytes) -> None:
    """Raise ValueError if raw bytes are not a supported image or exceed size limit."""
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("image_too_large")
    if not _is_supported_image(raw):
        raise ValueError("invalid_format")


def validate_interval(minutes: int) -> int:
    try:
        minutes = int(minutes)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"interval must be {INTERVAL_MIN}–{INTERVAL_MAX}") from exc
    if not (INTERVAL_MIN <= minutes <= INTERVAL_MAX):
        raise ValueError(f"interval must be {INTERVAL_MIN}–{INTERVAL_MAX}")
    return minutes


def normalize_banner_mode(value: object) -> str:
    mode = str(value or BANNER_MODE_PLAYLIST).strip().lower()
    if mode not in BANNER_MODES:
        raise ValueError("invalid_banner_mode")
    return mode


def normalize_dynamic_window_days(value: object) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        days = DYNAMIC_WINDOW_DAYS_DEFAULT
    return max(DYNAMIC_WINDOW_DAYS_MIN, min(DYNAMIC_WINDOW_DAYS_MAX, days))


# ──────────────────────── settings ────────────────────────


def get_settings(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    raw_mode = str(data.get("banner_mode") or BANNER_MODE_PLAYLIST).strip().lower()
    banner_mode = raw_mode if raw_mode in BANNER_MODES else BANNER_MODE_PLAYLIST
    return {
        "enabled": bool(data.get("enabled", False)),
        "banner_enabled": bool(data.get("banner_enabled", True)),
        "banner_mode": banner_mode,
        "dynamic_window_days": normalize_dynamic_window_days(data.get("dynamic_window_days")),
        "icon_enabled": bool(data.get("icon_enabled", True)),
        "interval_minutes": int(data.get("interval_minutes", INTERVAL_DEFAULT)),
        "log_channel_id": str(data.get("log_channel_id") or ""),
        "banners": list(data.get("banners") or []),
        "icons": list(data.get("icons") or []),
        "last_banner_id": str(data.get("last_banner_id") or ""),
        "last_icon_id": str(data.get("last_icon_id") or ""),
        "last_banner_at": int(data.get("last_banner_at") or 0),
        "last_icon_at": int(data.get("last_icon_at") or 0),
        "next_run_at": int(data.get("next_run_at") or 0),
    }


def save_settings(
    guild_id: int,
    *,
    enabled: bool,
    banner_enabled: bool = True,
    banner_mode: str = BANNER_MODE_PLAYLIST,
    dynamic_window_days: int = DYNAMIC_WINDOW_DAYS_DEFAULT,
    icon_enabled: bool = True,
    interval_minutes: int = INTERVAL_DEFAULT,
    log_channel_id: str = "",
) -> dict:
    interval_minutes = validate_interval(interval_minutes)
    banner_mode = normalize_banner_mode(banner_mode)
    dynamic_window_days = normalize_dynamic_window_days(dynamic_window_days)
    data = settings_db.get(guild_id, MODULE_NAME)
    data.update({
        "enabled": bool(enabled),
        "banner_enabled": bool(banner_enabled),
        "banner_mode": banner_mode,
        "dynamic_window_days": dynamic_window_days,
        "icon_enabled": bool(icon_enabled),
        "interval_minutes": interval_minutes,
        "log_channel_id": str(log_channel_id or ""),
    })
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


# ──────────────────────── image management ────────────────────────


def add_image(guild_id: int, kind: str, raw: bytes, original_name: str) -> dict:
    """Store raw bytes, return image metadata dict."""
    if kind not in ("banner", "icon"):
        raise ValueError("invalid_kind")
    validate_image(raw)
    img_id = _short_id()
    filename = f"{img_id}.{_ext_for_image(raw)}"
    path = _storage_dir(guild_id, kind) / filename
    path.write_bytes(raw)
    entry = {
        "id": img_id,
        "filename": filename,
        "original_name": original_name[:128],
        "uploaded_at": int(time.time()),
    }
    data = settings_db.get(guild_id, MODULE_NAME)
    key = f"{kind}s"
    images = list(data.get(key) or [])
    images.append(entry)
    data[key] = images
    settings_db.put(guild_id, MODULE_NAME, data)
    return entry


def delete_image(guild_id: int, kind: str, image_id: str) -> bool:
    if kind not in ("banner", "icon"):
        return False
    data = settings_db.get(guild_id, MODULE_NAME)
    key = f"{kind}s"
    images = list(data.get(key) or [])
    before = len(images)
    found = next((img for img in images if img["id"] == image_id), None)
    if found:
        images = [img for img in images if img["id"] != image_id]
        data[key] = images
        if data.get(f"last_{kind}_id") == image_id:
            data[f"last_{kind}_id"] = ""
        settings_db.put(guild_id, MODULE_NAME, data)
        path = _storage_dir(guild_id, kind) / found["filename"]
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return len(images) < before


def get_image_path(guild_id: int, kind: str, image_id: str) -> Path | None:
    data = settings_db.get(guild_id, MODULE_NAME)
    key = f"{kind}s"
    for img in data.get(key) or []:
        if img["id"] == image_id:
            p = _storage_dir(guild_id, kind) / img["filename"]
            return p if p.exists() else None
    return None


def list_image_paths(guild_id: int, kind: str) -> list[tuple[dict, Path]]:
    data = settings_db.get(guild_id, MODULE_NAME)
    result = []
    for img in data.get(f"{kind}s") or []:
        p = _storage_dir(guild_id, kind) / img["filename"]
        if p.exists():
            result.append((img, p))
    return result


# ──────────────────────── rotation logic ────────────────────────


def pick_next_image(images: list[dict], last_id: str) -> dict | None:
    """Return the next image in cycle, skipping the one with last_id."""
    if not images:
        return None
    if len(images) == 1:
        return images[0]
    ids = [img["id"] for img in images]
    try:
        idx = ids.index(last_id)
        next_idx = (idx + 1) % len(ids)
    except ValueError:
        next_idx = 0
    return images[next_idx]


def mark_rotated(guild_id: int, kind: str, image_id: str, interval_minutes: int) -> None:
    data = settings_db.get(guild_id, MODULE_NAME)
    now = int(time.time())
    data[f"last_{kind}_id"] = image_id
    data[f"last_{kind}_at"] = now
    data["next_run_at"] = now + interval_minutes * 60
    settings_db.put(guild_id, MODULE_NAME, data)
