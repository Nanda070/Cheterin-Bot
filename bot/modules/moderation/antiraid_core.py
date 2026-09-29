"""Ядро модуля «Антирейд»: детект всплеска входов новых участников.

Без импорта discord — юнит-тестируемо напрямую (подход fun_core.py). Модуль
ПОЛНОСТЬЮ ВЫКЛЮЧЕН ПО УМОЛЧАНИЮ и ни на что не влияет, пока его явно не
включат тумблером в дашборде (раздел «Антирейд») — это проверяется когом на
входе в on_member_join раньше любой другой логики.

При срабатывании (N входов за X секунд, из них M — «свежих» аккаунтов младше
заданного возраста) ког включает уже существующий lockdown_core.activate_antispam
и, опционально, slowmode в текстовых каналах.
"""

from collections import deque
from datetime import datetime, timezone

import bot.core.settings_db as settings_db

MODULE_NAME = "antiraid"

DEFAULT_JOIN_WINDOW_SEC = 10
DEFAULT_JOIN_THRESHOLD = 5
DEFAULT_MIN_ACCOUNT_AGE_HOURS = 24  # 0 — считать все входы, без фильтра по возрасту аккаунта
DEFAULT_ACTION_LOCKDOWN = True
DEFAULT_ACTION_SLOWMODE_SEC = 0     # 0 — не включать slowmode
DEFAULT_COOLDOWN_MINUTES = 30       # не срабатывать повторно раньше, чем через это время

JOIN_WINDOW_SEC_MAX = 3600
JOIN_THRESHOLD_MAX = 1000
ACCOUNT_AGE_HOURS_MAX = 8760  # год
SLOWMODE_SEC_MAX = 21600      # лимит Discord на slowmode — 6 часов
COOLDOWN_MINUTES_MAX = 1440

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами. enabled=False по умолчанию — модуль не
    активен, пока администратор явно не включит его в дашборде."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "join_window_sec": int(data.get("join_window_sec", DEFAULT_JOIN_WINDOW_SEC)),
        "join_threshold": int(data.get("join_threshold", DEFAULT_JOIN_THRESHOLD)),
        "min_account_age_hours": int(data.get("min_account_age_hours", DEFAULT_MIN_ACCOUNT_AGE_HOURS)),
        "action_lockdown": bool(data.get("action_lockdown", DEFAULT_ACTION_LOCKDOWN)),
        "action_slowmode_sec": int(data.get("action_slowmode_sec", DEFAULT_ACTION_SLOWMODE_SEC)),
        "cooldown_minutes": int(data.get("cooldown_minutes", DEFAULT_COOLDOWN_MINUTES)),
    }


def is_suspicious_account(account_created_at: datetime, joined_at: datetime, min_age_hours: int) -> bool:
    """Считается ли аккаунт «свежим» (подозрительным) на момент входа."""
    if min_age_hours <= 0:
        return True  # фильтр по возрасту отключён — считаем все входы
    age = joined_at - account_created_at
    return age.total_seconds() < min_age_hours * 3600


class JoinTracker:
    """Скользящее окно недавних «подозрительных» входов на один сервер.

    Чистая структура данных без discord — принимает уже посчитанный признак
    suspicious извне (через is_suspicious_account), сама только считает окно.
    """

    def __init__(self, window_sec: int):
        self.window_sec = window_sec
        self._joins: deque[datetime] = deque()

    def register(self, at: datetime) -> int:
        """Добавить вход и вернуть текущее число подозрительных входов в окне."""
        self._joins.append(at)
        cutoff = at.timestamp() - self.window_sec
        while self._joins and self._joins[0].timestamp() < cutoff:
            self._joins.popleft()
        return len(self._joins)

    def reset(self) -> None:
        self._joins.clear()


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
