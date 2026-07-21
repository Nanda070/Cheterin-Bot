"""Ядро модуля «Автомодерация»: 9 настраиваемых фильтров сообщений (ссылки,
инвайты, скам-ссылки, плохие слова, повторяемый текст, caps lock, эмоции,
упоминания, zalgo), эскалация по количеству активных варнов участника и
настройки варнов по умолчанию для ручной выдачи.

Каждый фильтр независимо включается и настраивается: удалять ли сообщение,
какую меру пресечения применять (ничего/варн/мут/кик/бан), на какой срок
(0 = бессрочно/без срока действия варна) и уведомлять ли нарушителя
(с шаблоном сообщения). Модуль в целом выключен по умолчанию.
"""

import re
from urllib.parse import urlparse

import settings_db

MODULE_NAME = "automod"

FILTER_KEYS = [
    "links",
    "invites",
    "scam_links",
    "bad_words",
    "repeated_text",
    "caps_lock",
    "emoji_spam",
    "mentions",
    "zalgo",
]

FILTER_LABELS: dict[str, str] = {
    "links": "Ссылки",
    "invites": "Приглашения",
    "scam_links": "Скам и фишинг ссылки",
    "bad_words": "Плохие слова",
    "repeated_text": "Повторяемый текст",
    "caps_lock": "Caps Lock",
    "emoji_spam": "Эмоции",
    "mentions": "Упоминания",
    "zalgo": "Zalgo",
}

FILTER_DESCRIPTIONS: dict[str, str] = {
    "links": "Нежелательные ссылки",
    "invites": "Приглашения на сервера Discord",
    "scam_links": "Бесплатный сыр бывает только в мышеловке",
    "bad_words": "Мат, нежелательные выражения",
    "repeated_text": "Никто не любит излишний флуд",
    "caps_lock": "НЕ НАДО НА МЕНЯ ОРАТЬ!",
    "emoji_spam": "Чрезмерное использование смайликов",
    "mentions": "Чрезмерное использование упоминаний",
    "zalgo": "Чрезмерное использование символов Zalgo",
}

PUNISHMENTS = ("none", "warn", "mute", "kick", "ban")
ESCALATION_ACTIONS = ("mute", "kick", "ban")

MAX_DURATION_MINUTES = 40320  # 28 дней — максимум таймаута Discord
DEFAULT_NOTIFY_TEMPLATE = "Привет {{member}}! Вы получили предупреждение за нарушение правил сервера: {{reason}}."
DEFAULT_MANUAL_WARN_DURATION_MINUTES = 30 * 1440  # 30 дней

_DEFAULT_FILTER: dict = {
    "enabled": False,
    "delete_message": True,
    "punishment": "warn",
    "duration_minutes": 0,
    "notify_member": False,
    "notify_channel_id": "",
    "notify_template": DEFAULT_NOTIFY_TEMPLATE,
}

FILTER_EXTRA_DEFAULTS: dict[str, dict] = {
    "links": {"whitelist_domains": []},
    "invites": {"allow_own_server": True},
    "scam_links": {"blocklist_keywords": []},
    "bad_words": {"words": []},
    "repeated_text": {"max_repeats": 4, "consecutive_only": True, "reset_on_trigger": True},
    "caps_lock": {"max_percent": 70, "min_length": 10},
    "emoji_spam": {"max_count": 10},
    "mentions": {"max_count": 5},
    "zalgo": {"max_count": 5},
}


def _default_filter(key: str) -> dict:
    return {**_DEFAULT_FILTER, **FILTER_EXTRA_DEFAULTS.get(key, {})}


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("escalation_seq", 0)
    data.setdefault("escalation", [])
    data.setdefault("manual_warn_duration_minutes", DEFAULT_MANUAL_WARN_DURATION_MINUTES)

    filters = data.setdefault("filters", {})
    for key in FILTER_KEYS:
        entry = {**_default_filter(key), **filters.get(key, {})}
        filters[key] = entry
    return data


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    return {
        "enabled": bool(data["enabled"]),
        "filters": {
            key: {
                "label": FILTER_LABELS[key],
                "description": FILTER_DESCRIPTIONS[key],
                **data["filters"][key],
            }
            for key in FILTER_KEYS
        },
        "escalation": list(data["escalation"]),
        "manual_warn_duration_minutes": int(data["manual_warn_duration_minutes"]),
    }


def get_filter_config(guild_id: int, key: str) -> dict | None:
    if key not in FILTER_KEYS:
        return None
    return _normalized(settings_db.get(guild_id, MODULE_NAME))["filters"][key]


def update_module_enabled(guild_id: int, enabled: bool) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["enabled"] = bool(enabled)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def update_filter(guild_id: int, key: str, fields: dict) -> dict | None:
    if key not in FILTER_KEYS:
        return None
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["filters"][key].update(fields)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)["filters"][key]


def update_manual_warn_duration(guild_id: int, minutes: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["manual_warn_duration_minutes"] = int(minutes)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def add_escalation_rule(guild_id: int, count: int, action: str, duration_minutes: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["escalation_seq"] += 1
    rule = {"id": str(data["escalation_seq"]), "count": count, "action": action, "duration_minutes": duration_minutes}
    data["escalation"].append(rule)
    settings_db.put(guild_id, MODULE_NAME, data)
    return rule


def update_escalation_rule(guild_id: int, rule_id: str, fields: dict) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for rule in data["escalation"]:
        if rule["id"] == str(rule_id):
            rule.update(fields)
            settings_db.put(guild_id, MODULE_NAME, data)
            return rule
    return None


def delete_escalation_rule(guild_id: int, rule_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    before = len(data["escalation"])
    data["escalation"] = [r for r in data["escalation"] if r["id"] != str(rule_id)]
    if len(data["escalation"]) == before:
        return False
    settings_db.put(guild_id, MODULE_NAME, data)
    return True


def find_escalation_rule(guild_id: int, active_warn_count: int) -> dict | None:
    """Правило эскалации, точно соответствующее текущему числу активных варнов."""
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for rule in data["escalation"]:
        if rule["count"] == active_warn_count:
            return rule
    return None


def render_notify_template(template: str, member_mention: str, reason: str) -> str:
    text = template
    for key, value in {"{{member}}": member_mention, "{{reason}}": reason}.items():
        text = text.replace(key, value)
    return text


# ────────────────────────── Детекторы (чистые функции) ──────────────────────────

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_INVITE_RE = re.compile(r"(?:discord\.gg/|discord(?:app)?\.com/invite/)[a-zA-Z0-9-]+", re.IGNORECASE)
_CUSTOM_EMOJI_RE = re.compile(r"<a?:\w+:\d+>")
_UNICODE_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]"
)
_ZALGO_RE = re.compile(r"[̀-ͯ҉]")


def extract_urls(content: str) -> list[str]:
    return _URL_RE.findall(content)


def url_domain(url: str) -> str:
    full = url if "://" in url else f"http://{url}"
    try:
        netloc = urlparse(full).netloc.lower()
    except ValueError:
        return ""
    return netloc.removeprefix("www.")


def detect_links(content: str, whitelist_domains: list[str]) -> bool:
    urls = extract_urls(content)
    if not urls:
        return False
    whitelist = {d.lower().removeprefix("www.") for d in whitelist_domains}
    return any(url_domain(u) not in whitelist for u in urls)


def detect_invites(content: str, allow_own_server: bool, server_invite_link: str) -> bool:
    matches = _INVITE_RE.findall(content)
    if not matches:
        return False
    if not allow_own_server or not server_invite_link:
        return True
    own = server_invite_link.strip().rstrip("/").lower()
    return any(m.lower() not in own and own not in m.lower() for m in matches)


def detect_scam_links(content: str, blocklist_keywords: list[str]) -> bool:
    if not blocklist_keywords:
        return False
    lowered = content.lower()
    return any(kw.strip().lower() in lowered for kw in blocklist_keywords if kw.strip())


def detect_bad_words(content: str, words: list[str]) -> bool:
    if not words:
        return False
    lowered = content.lower()
    return any(w.strip().lower() in lowered for w in words if w.strip())


def detect_repeated_text(recent_signatures: list[str], current: str, max_repeats: int) -> bool:
    if max_repeats <= 0:
        return False
    matches = sum(1 for s in recent_signatures if s == current)
    return matches + 1 >= max_repeats


def detect_caps_lock(content: str, max_percent: int, min_length: int) -> bool:
    letters = [c for c in content if c.isalpha()]
    if len(letters) < min_length:
        return False
    upper = sum(1 for c in letters if c.isupper())
    return (upper / len(letters)) * 100 >= max_percent


def detect_emoji_spam(content: str, max_count: int) -> bool:
    if max_count <= 0:
        return False
    total = len(_CUSTOM_EMOJI_RE.findall(content)) + len(_UNICODE_EMOJI_RE.findall(content))
    return total >= max_count


def detect_mentions(mention_count: int, max_count: int) -> bool:
    return max_count > 0 and mention_count >= max_count


def detect_zalgo(content: str, max_count: int) -> bool:
    return max_count > 0 and len(_ZALGO_RE.findall(content)) >= max_count
