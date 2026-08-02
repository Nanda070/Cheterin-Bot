"""Auto-reactions: react to new messages by rule (keywords + channel scope)."""

from __future__ import annotations

import re
import uuid

import settings_db

MODULE_NAME = "auto_reactions"

MAX_RULES = 25
MAX_EMOJIS_PER_RULE = 10
# Discord allows at most 20 unique reactions on a message.
MAX_GUILD_EMOJIS_REACT = 20
MAX_KEYWORDS_PER_RULE = 30
MAX_KEYWORD_LEN = 100
MAX_EMOJI_LEN = 64
CHANNEL_MODES = frozenset({"all", "include"})
EMOJI_MODES = frozenset({"list", "all_guild"})

_CUSTOM_EMOJI_RE = re.compile(r"^<a?:\w+:\d+>$")


def _empty() -> dict:
    return {"enabled": False, "rules": [], "seq": 0}


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("rules", [])
    data.setdefault("seq", 0)
    return data


def _normalize_rule(raw: dict) -> dict | None:
    if not isinstance(raw, dict):
        return None
    rule_id = str(raw.get("id") or "").strip()
    if not rule_id:
        return None

    emoji_mode = raw.get("emoji_mode") or "list"
    if emoji_mode not in EMOJI_MODES:
        emoji_mode = "list"

    emojis_raw = raw.get("emojis") or []
    if not isinstance(emojis_raw, list):
        emojis_raw = []
    emojis = [str(e).strip() for e in emojis_raw if isinstance(e, str) and str(e).strip()]
    emojis = emojis[:MAX_EMOJIS_PER_RULE]

    keywords_raw = raw.get("keywords") or []
    if not isinstance(keywords_raw, list):
        keywords_raw = []
    keywords = [
        str(k).strip()
        for k in keywords_raw
        if isinstance(k, str) and str(k).strip() and len(str(k).strip()) <= MAX_KEYWORD_LEN
    ][:MAX_KEYWORDS_PER_RULE]

    mode = raw.get("channel_mode") or "all"
    if mode not in CHANNEL_MODES:
        mode = "all"

    def _id_list(key: str) -> list[str]:
        vals = raw.get(key) or []
        if not isinstance(vals, list):
            return []
        out = []
        for v in vals:
            s = str(v).strip()
            if s.isdigit():
                out.append(s)
        return out

    return {
        "id": rule_id,
        "emoji_mode": emoji_mode,
        "emojis": [] if emoji_mode == "all_guild" else emojis,
        "keywords": keywords,
        "channel_mode": mode,
        "channel_ids": _id_list("channel_ids"),
        "exclude_channel_ids": _id_list("exclude_channel_ids"),
        "ignore_bots": bool(raw.get("ignore_bots", True)),
    }


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    rules = []
    for raw in data["rules"]:
        rule = _normalize_rule(raw if isinstance(raw, dict) else {})
        if rule is not None:
            rules.append(rule)
    return {
        "enabled": bool(data["enabled"]),
        "rules": rules,
    }


def save_config(guild_id: int, *, enabled: bool, rules: list[dict]) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    normalized_rules = []
    for raw in rules[:MAX_RULES]:
        rule = _normalize_rule(raw if isinstance(raw, dict) else {})
        if rule is None:
            continue
        if rule["emoji_mode"] != "all_guild" and not rule["emojis"]:
            continue
        normalized_rules.append(rule)
    data["enabled"] = bool(enabled)
    data["rules"] = normalized_rules
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def new_rule_id() -> str:
    return uuid.uuid4().hex[:12]


def channel_matches_rule(rule: dict, channel_id: int | str) -> bool:
    """Whether ``channel_id`` is in scope for the rule."""
    cid = str(channel_id)
    excludes = {str(x) for x in rule.get("exclude_channel_ids") or []}
    if cid in excludes:
        return False

    mode = rule.get("channel_mode") or "all"
    if mode == "include":
        includes = {str(x) for x in rule.get("channel_ids") or []}
        return cid in includes
    # mode == "all"
    return True


def keywords_match(keywords: list[str], content: str) -> bool:
    """Empty keywords = match all. Otherwise case-insensitive substring."""
    if not keywords:
        return True
    haystack = (content or "").lower()
    return any(k.lower() in haystack for k in keywords)


def matching_rules_for_message(
    settings: dict,
    *,
    channel_id: int | str,
    content: str,
    author_is_bot: bool,
) -> list[dict]:
    if not settings.get("enabled"):
        return []
    matched = []
    for rule in settings.get("rules") or []:
        if rule.get("ignore_bots", True) and author_is_bot:
            continue
        if not channel_matches_rule(rule, channel_id):
            continue
        if not keywords_match(rule.get("keywords") or [], content):
            continue
        if rule.get("emoji_mode") == "all_guild":
            matched.append(rule)
            continue
        if not rule.get("emojis"):
            continue
        matched.append(rule)
    return matched


def guild_emoji_tokens(guild_emojis) -> list:
    """Return up to Discord's per-message reaction limit of guild emoji objects."""
    if not guild_emojis:
        return []
    return list(guild_emojis)[:MAX_GUILD_EMOJIS_REACT]


def is_valid_emoji_token(token: str) -> bool:
    if not isinstance(token, str):
        return False
    t = token.strip()
    if not t or len(t) > MAX_EMOJI_LEN:
        return False
    if _CUSTOM_EMOJI_RE.match(t):
        return True
    # unicode / short text emoji
    return True
