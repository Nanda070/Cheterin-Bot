"""Build a per-user moderation case timeline from warns_db + moderation_log.

Pure helpers (no Discord I/O) so routes and unit tests can share the same merge,
dedupe, and sort logic.
"""

from __future__ import annotations

CASE_TIMELINE_LIMIT = 100

# Moderation-log event types that duplicate a warns_db row for the same warn.
_WARN_LOG_KINDS = frozenset({"warn_manual"})


def _ts_second(ts: str | None) -> str:
    if not ts:
        return ""
    # ISO timestamps are comparable; truncate fractional seconds for loose match.
    return ts[:19]


def warn_to_item(warn: dict) -> dict:
    return {
        "id": f"warn:{warn['id']}",
        "kind": "warn",
        "timestamp": warn.get("created_at") or "",
        "reason": warn.get("reason") or "",
        "moderator_id": warn.get("moderator_id"),
        "moderator_display": None,
        "extra": "",
        "meta": {
            "source": warn.get("source"),
            "removed": bool(warn.get("removed")),
            "warn_id": warn.get("id"),
            "expires_at": warn.get("expires_at"),
            "removed_by": warn.get("removed_by"),
            "removed_at": warn.get("removed_at"),
        },
    }


def event_to_item(event: dict, index: int) -> dict:
    kind = event.get("type") or "unknown"
    ts = event.get("timestamp") or ""
    return {
        "id": f"log:{ts}:{kind}:{index}",
        "kind": kind,
        "timestamp": ts,
        "reason": event.get("reason") or "",
        "moderator_id": event.get("moderator_id"),
        "moderator_display": event.get("moderator_display"),
        "extra": event.get("extra") or "",
        "meta": {
            "user_display": event.get("user_display"),
        },
    }


def _is_duplicate_warn_log(event: dict, warn_items: list[dict]) -> bool:
    """Skip warn_manual log rows that already appear in warns_db (prefer DB)."""
    if event.get("type") not in _WARN_LOG_KINDS:
        return False
    event_ts = _ts_second(event.get("timestamp"))
    event_reason = (event.get("reason") or "").strip()
    event_mod = event.get("moderator_id")
    for item in warn_items:
        if _ts_second(item.get("timestamp")) != event_ts:
            continue
        if (item.get("reason") or "").strip() != event_reason:
            continue
        item_mod = item.get("moderator_id")
        if event_mod and item_mod and str(event_mod) != str(item_mod):
            continue
        return True
    return False


def build_case_timeline(
    warns: list[dict],
    events: list[dict],
    user_id: str | int,
    *,
    limit: int = CASE_TIMELINE_LIMIT,
) -> list[dict]:
    """Merge warns + filtered mod-log events for one user; newest first."""
    uid = str(user_id)
    warn_items = [warn_to_item(w) for w in warns]
    items: list[dict] = list(warn_items)

    for index, event in enumerate(events):
        if str(event.get("user_id") or "") != uid:
            continue
        if _is_duplicate_warn_log(event, warn_items):
            continue
        items.append(event_to_item(event, index))

    items.sort(key=lambda item: item.get("timestamp") or "", reverse=True)
    return items[: max(0, limit)]


def serialize_timeline_user(user) -> dict:
    """Serialize a discord.Member or discord.User for the timeline header."""
    avatar = None
    display_avatar = getattr(user, "display_avatar", None)
    if display_avatar is not None:
        avatar = str(display_avatar.url)
    display_name = getattr(user, "display_name", None) or getattr(user, "name", "")
    return {
        "id": str(user.id),
        "username": getattr(user, "name", "") or "",
        "display_name": display_name,
        "avatar": avatar,
    }
