"""Ядро модуля «Ежедневная рубрика».

Бот раз в день публикует тему/вопрос в заданный канал, чтобы разговор не
затухал в тихие дни. Настраивается в дашборде (раздел «Ежедневная рубрика»):
список тем, канал публикации и набор возможных времён публикации — каждый
день бот случайно выбирает одно время из набора и одну тему (без повторов,
пока не закончится весь список). Выключено по умолчанию.

Хранение — settings_db, per-guild (Фаза 2.1 MULTIGUILD_PLAN.md).
"""

import random
import re
from datetime import datetime, timezone, timedelta

import settings_db

MODULE_NAME = "daily_topic"

MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

MAX_TOPIC_LENGTH = 300
MAX_POST_TIMES = 10


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value or ""))


def _normalized(data: dict) -> dict:
    data.setdefault("enabled", False)
    data.setdefault("channel_id", "")
    data.setdefault("post_times", [])
    data.setdefault("topics", [])
    data.setdefault("seq", 0)
    data.setdefault("queue", [])
    data.setdefault("last_topic_id", None)
    data.setdefault("last_posted_date", "")
    data.setdefault("chosen_time", "")
    data.setdefault("chosen_time_date", "")
    return data


def _today_msk() -> str:
    # Backward-compat alias used by older tests; prefer _today_local(guild_id).
    return datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")


def get_settings(guild_id: int) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    return {
        "enabled": bool(data["enabled"]),
        "channel_id": str(data["channel_id"] or ""),
        "post_times": list(data["post_times"]),
        "topics": [{"id": t["id"], "text": t["text"]} for t in data["topics"]],
    }


def update_settings(guild_id: int, *, enabled: bool, channel_id: str, post_times: list[str]) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["enabled"] = bool(enabled)
    data["channel_id"] = channel_id
    data["post_times"] = list(post_times)
    settings_db.put(guild_id, MODULE_NAME, data)
    return get_settings(guild_id)


def add_topic(guild_id: int, text: str) -> dict:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["seq"] += 1
    topic = {"id": str(data["seq"]), "text": text}
    data["topics"].append(topic)
    settings_db.put(guild_id, MODULE_NAME, data)
    return topic


def update_topic(guild_id: int, topic_id: str, text: str) -> dict | None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    for topic in data["topics"]:
        if topic["id"] == str(topic_id):
            topic["text"] = text
            settings_db.put(guild_id, MODULE_NAME, data)
            return topic
    return None


def delete_topic(guild_id: int, topic_id: str) -> bool:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    topic_id = str(topic_id)
    before = len(data["topics"])
    data["topics"] = [t for t in data["topics"] if t["id"] != topic_id]
    if len(data["topics"]) == before:
        return False
    data["queue"] = [tid for tid in data["queue"] if tid != topic_id]
    settings_db.put(guild_id, MODULE_NAME, data)
    return True


def pick_next_topic(guild_id: int) -> dict | None:
    """Выбирает следующую тему по кругу без повторов, пока список не закончится.

    Возвращает None, если тем нет вообще. Меняет состояние (очередь, последняя
    выбранная тема) — вызывать только при реальной публикации, не для превью.
    """
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    ids = [t["id"] for t in data["topics"]]
    if not ids:
        return None

    data["queue"] = [tid for tid in data["queue"] if tid in ids]
    if not data["queue"]:
        shuffled = list(ids)
        random.shuffle(shuffled)
        if len(shuffled) > 1 and shuffled[0] == data["last_topic_id"]:
            shuffled[0], shuffled[1] = shuffled[1], shuffled[0]
        data["queue"] = shuffled

    topic_id = data["queue"].pop(0)
    data["last_topic_id"] = topic_id
    settings_db.put(guild_id, MODULE_NAME, data)

    return next((t for t in data["topics"] if t["id"] == topic_id), None)


def _today_local(guild_id: int) -> str:
    import timezone_core

    return timezone_core.today_local(guild_id)


def already_posted_today(guild_id: int) -> bool:
    """True if a topic was already posted for today's local calendar (or later).

    Uses ``>=`` so a timezone change that moves the local date *backward*
    still counts as already posted and does not double-post.
    Normal day rollover (posted date < today) still allows the next post.
    """
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    last = data["last_posted_date"] or ""
    if not last:
        return False
    return last >= _today_local(guild_id)


def mark_posted_today(guild_id: int) -> None:
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    data["last_posted_date"] = _today_local(guild_id)
    settings_db.put(guild_id, MODULE_NAME, data)


def get_today_post_time(guild_id: int) -> str | None:
    """Возвращает выбранное на сегодня время публикации, выбирая его при первом обращении."""
    data = _normalized(settings_db.get(guild_id, MODULE_NAME))
    post_times = data["post_times"]
    if not post_times:
        return None

    today = _today_local(guild_id)
    if data["chosen_time_date"] == today and data["chosen_time"] in post_times:
        return data["chosen_time"]

    chosen = random.choice(post_times)
    data["chosen_time"] = chosen
    data["chosen_time_date"] = today
    settings_db.put(guild_id, MODULE_NAME, data)
    return chosen


def should_post_now(guild_id: int) -> bool:
    """Пора ли публиковать тему дня: время настало и сегодня ещё не публиковали."""
    import timezone_core

    if already_posted_today(guild_id):
        return False
    target = get_today_post_time(guild_id)
    if target is None:
        return False
    now_hhmm = timezone_core.now_local(guild_id).strftime("%H:%M")
    return now_hhmm >= target
