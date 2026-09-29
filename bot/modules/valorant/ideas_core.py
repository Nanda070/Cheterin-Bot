"""Guild-scoped idea intake, moderation queue, and publication settings."""

from __future__ import annotations

from datetime import datetime, timezone

import bot.core.settings_db as settings_db

MODULE_NAME = "ideas"
CASES_KEY = "ideas_cases"
DEFAULT_PROMPT = "Post an idea here. Staff will review it before publishing."
DEFAULT_VOTE_EMOJIS = ["👍", "👎"]


def get_settings(guild_id: int) -> dict:
    raw = settings_db.get(guild_id, MODULE_NAME)
    emojis = raw.get("vote_emojis") if isinstance(raw.get("vote_emojis"), list) else DEFAULT_VOTE_EMOJIS
    prompt = str(raw.get("prompt") or "").strip()
    if not prompt:
        import bot.core.i18n as i18n

        prompt = i18n.t("ideas.default_prompt", i18n.lang_for(guild_id))[:1000]
    return {
        "enabled": bool(raw.get("enabled", False)),
        "intake_channel_id": str(raw.get("intake_channel_id") or ""),
        "review_channel_id": str(raw.get("review_channel_id") or ""),
        "channel_id": str(raw.get("channel_id") or ""),
        "prompt": prompt[:1000],
        "vote_emojis": [str(emojis[0])[:64], str(emojis[1])[:64]] if len(emojis) >= 2 else list(DEFAULT_VOTE_EMOJIS),
    }


def save_settings(guild_id: int, patch: dict) -> dict:
    current = get_settings(guild_id)
    current["enabled"] = bool(patch.get("enabled", current["enabled"]))
    for key in ("intake_channel_id", "review_channel_id", "channel_id"):
        if key in patch:
            value = str(patch.get(key) or "")
            current[key] = value if not value or value.isdigit() else ""
    if "prompt" in patch:
        current["prompt"] = str(patch.get("prompt") or DEFAULT_PROMPT).strip()[:1000] or DEFAULT_PROMPT
    if isinstance(patch.get("vote_emojis"), list) and len(patch["vote_emojis"]) >= 2:
        current["vote_emojis"] = [str(patch["vote_emojis"][0])[:64], str(patch["vote_emojis"][1])[:64]]
    settings_db.put(guild_id, MODULE_NAME, current)
    return get_settings(guild_id)


def _cases(guild_id: int) -> dict[str, dict]:
    raw = settings_db.get(guild_id, CASES_KEY, {})
    return raw if isinstance(raw, dict) else {}


def list_cases(guild_id: int, status: str | None = None) -> list[dict]:
    rows = list(_cases(guild_id).values())
    if status:
        rows = [row for row in rows if row.get("status") == status]
    return sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)


def create_case(guild_id: int, submitter_id: int, text: str, attachment_url: str = "") -> dict:
    cases = _cases(guild_id)
    index = 1
    while f"IDEA-{index:04d}" in cases:
        index += 1
    case = {"case_id": f"IDEA-{index:04d}", "submitter_id": int(submitter_id), "text": text.strip()[:1500], "attachment_url": attachment_url[:1000], "status": "pending", "created_at": datetime.now(timezone.utc).isoformat()}
    cases[case["case_id"]] = case
    settings_db.put(guild_id, CASES_KEY, cases)
    return case


def decide_case(guild_id: int, case_id: str, approved: bool, moderator_id: int) -> dict | None:
    cases = _cases(guild_id)
    case = cases.get(case_id)
    if case is None or case.get("status") != "pending":
        return None
    case.update({"status": "approved" if approved else "denied", "reviewed_by": int(moderator_id), "reviewed_at": datetime.now(timezone.utc).isoformat()})
    cases[case_id] = case
    settings_db.put(guild_id, CASES_KEY, cases)
    return case
