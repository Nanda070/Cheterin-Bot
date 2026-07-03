import json
import os
import re

CONFIG_FILE = "feedback_categories.json"

KEY_PATTERN = re.compile(r"^[a-z0-9_]+$")
PREFIX_PATTERN = re.compile(r"^[A-Z0-9]{1,6}$")


def load_categories() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_categories(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def validate_category_spec(spec: dict, categories: dict, existing_key: str | None = None) -> str | None:
    if existing_key is None:
        key = spec.get("key", "")
        if not KEY_PATTERN.match(key or ""):
            return "invalid_key"
        if key in categories:
            return "key_taken"

    case_prefix = spec.get("case_prefix", "")
    if not PREFIX_PATTERN.match(case_prefix or ""):
        return "invalid_case_prefix"
    for other_key, other in categories.items():
        if other_key == existing_key:
            continue
        if other.get("case_prefix") == case_prefix:
            return "case_prefix_taken"

    for text_field, max_len in (
        ("title", 80),
        ("button_label", 80),
        ("case_title", 80),
        ("modal_title", 80),
        ("approved_text", 1024),
        ("denied_text", 1024),
    ):
        value = spec.get(text_field, "")
        if not value or len(value) > max_len:
            return f"invalid_{text_field}"

    thread_name = spec.get("thread_name", "")
    if not thread_name or len(thread_name) > 80:
        return "invalid_thread_name"

    fields = spec.get("fields") or []
    if not (1 <= len(fields) <= 5):
        return "invalid_field_count"

    field_keys = set()
    for field in fields:
        field_key = field.get("key", "")
        if not field_key or field_key in field_keys:
            return "invalid_field_key"
        field_keys.add(field_key)
        label = field.get("label", "")
        if not label or len(label) > 45:
            return "invalid_field_label"
        max_length = field.get("max_length")
        if not isinstance(max_length, int) or not (1 <= max_length <= 4000):
            return "invalid_field_max_length"
        if field.get("style") not in ("short", "paragraph"):
            return "invalid_field_style"

    if spec.get("mini_summary_key") not in field_keys:
        return "invalid_mini_summary_key"

    return None


def migrate_from_env_if_needed() -> None:
    if os.path.exists(CONFIG_FILE):
        return
    channel_id_raw = os.getenv("CHANNEL_COMPLAINT_PLAY")
    role_id_raw = os.getenv("ROLE_PLAYERS")
    if not channel_id_raw or not role_id_raw:
        return

    categories = {
        "players": {
            "title": "Жалоба на участника",
            "button_label": "            Жалоба на участника            ",
            "channel_id": channel_id_raw,
            "case_prefix": "PR",
            "case_title": "Жалоба на участника",
            "thread_name": "player-report",
            "review_role_ids": [role_id_raw],
            "approved_text": "Участник наказан.",
            "denied_text": "Жалоба отклонена.",
            "modal_title": "Жалоба на участника",
            "fields": [
                {
                    "key": "offender",
                    "label": "Ник / ID участника",
                    "style": "short",
                    "required": True,
                    "max_length": 120,
                },
                {
                    "key": "complaint",
                    "label": "Суть жалобы",
                    "style": "paragraph",
                    "required": True,
                    "max_length": 1000,
                },
                {
                    "key": "datetime",
                    "label": "Дата и время ситуации",
                    "style": "short",
                    "required": False,
                    "max_length": 120,
                },
                {
                    "key": "proof",
                    "label": "Доказательства",
                    "style": "paragraph",
                    "required": False,
                    "max_length": 1000,
                },
            ],
            "mini_summary_key": "offender",
        },
    }
    save_categories(categories)
