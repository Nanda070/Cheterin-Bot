"""Ядро модуля «Ежедневная рубрика».

Бот раз в день публикует тему/вопрос в заданный канал, чтобы разговор не
затухал в тихие дни. Настраивается в дашборде (раздел «Ежедневная рубрика»):
список тем, канал публикации и набор возможных времён публикации — каждый
день бот случайно выбирает одно время из набора и одну тему (без повторов,
пока не закончится весь список). Выключено по умолчанию.

Хранение — daily_topic_config.json, тот же паттерн load/save, что и у
giveaway_core.py.
"""

import json
import os
import random
import re
from datetime import datetime, timezone, timedelta

CONFIG_FILE = "daily_topic_config.json"

MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

MAX_TOPIC_LENGTH = 300
MAX_POST_TIMES = 10


def is_valid_time(value: str) -> bool:
    return bool(TIME_RE.match(value or ""))


def load_config() -> dict:
    """Чтение конфига, устойчивое к гонкам с параллельной записью (дашборд пишет,
    планировщик читает каждую минуту): любая ошибка чтения/парсинга — пустой конфиг,
    а не исключение, которое убило бы tasks.loop планировщика."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}
    return {}


def save_config(data: dict) -> None:
    """Атомарная запись (tmp + os.replace): читатель никогда не увидит недописанный
    JSON, даже если планировщик читает файл в момент сохранения из дашборда."""
    tmp_path = CONFIG_FILE + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    os.replace(tmp_path, CONFIG_FILE)


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
    return datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d")


def get_settings() -> dict:
    data = _normalized(load_config())
    return {
        "enabled": bool(data["enabled"]),
        "channel_id": str(data["channel_id"] or ""),
        "post_times": list(data["post_times"]),
        "topics": [{"id": t["id"], "text": t["text"]} for t in data["topics"]],
    }


def update_settings(*, enabled: bool, channel_id: str, post_times: list[str]) -> dict:
    data = _normalized(load_config())
    data["enabled"] = bool(enabled)
    data["channel_id"] = channel_id
    data["post_times"] = list(post_times)
    save_config(data)
    return get_settings()


def add_topic(text: str) -> dict:
    data = _normalized(load_config())
    data["seq"] += 1
    topic = {"id": str(data["seq"]), "text": text}
    data["topics"].append(topic)
    save_config(data)
    return topic


def update_topic(topic_id: str, text: str) -> dict | None:
    data = _normalized(load_config())
    for topic in data["topics"]:
        if topic["id"] == str(topic_id):
            topic["text"] = text
            save_config(data)
            return topic
    return None


def delete_topic(topic_id: str) -> bool:
    data = _normalized(load_config())
    topic_id = str(topic_id)
    before = len(data["topics"])
    data["topics"] = [t for t in data["topics"] if t["id"] != topic_id]
    if len(data["topics"]) == before:
        return False
    data["queue"] = [tid for tid in data["queue"] if tid != topic_id]
    save_config(data)
    return True


def pick_next_topic() -> dict | None:
    """Выбирает следующую тему по кругу без повторов, пока список не закончится.

    Возвращает None, если тем нет вообще. Меняет состояние (очередь, последняя
    выбранная тема) — вызывать только при реальной публикации, не для превью.
    """
    data = _normalized(load_config())
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
    save_config(data)

    return next((t for t in data["topics"] if t["id"] == topic_id), None)


def already_posted_today() -> bool:
    data = _normalized(load_config())
    return data["last_posted_date"] == _today_msk()


def mark_posted_today() -> None:
    data = _normalized(load_config())
    data["last_posted_date"] = _today_msk()
    save_config(data)


def get_today_post_time() -> str | None:
    """Возвращает выбранное на сегодня время публикации, выбирая его при первом обращении."""
    data = _normalized(load_config())
    post_times = data["post_times"]
    if not post_times:
        return None

    today = _today_msk()
    if data["chosen_time_date"] == today and data["chosen_time"] in post_times:
        return data["chosen_time"]

    chosen = random.choice(post_times)
    data["chosen_time"] = chosen
    data["chosen_time_date"] = today
    save_config(data)
    return chosen


def should_post_now() -> bool:
    """Пора ли публиковать тему дня: время настало и сегодня ещё не публиковали."""
    if already_posted_today():
        return False
    target = get_today_post_time()
    if target is None:
        return False
    now_hhmm = datetime.now(MOSCOW_TZ).strftime("%H:%M")
    return now_hhmm >= target
