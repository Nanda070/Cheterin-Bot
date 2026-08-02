"""Ядро модуля «Семья» (портировано из FamQ): конфигурация, парсинг дат ДР,
цвета/лейблы статусов тикета, текст live-списков.

Домен без изменений относительно оригинала:
- ростер — live-список участников по заданным ролям;
- заявки — 2-этапная анкета -> приватный тред с решением staff;
- дни рождения — хранение дат, live-список по месяцам, ежедневная рассылка.

Всё модульно гейтится флагом `enabled`; конфигурация (роли/каналы/эмодзи)
настраивается через дашборд вместо хардкода .env, как в оригинале.
"""

import re

import embed_style
import i18n
import settings_db

MODULE_NAME = "family"

DEFAULT_THREAD_ARCHIVE_MINUTES = 10080  # 7 дней

MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

MONTH_ALIASES = {
    "январь": 1, "января": 1,
    "февраль": 2, "февраля": 2,
    "март": 3, "марта": 3,
    "апрель": 4, "апреля": 4,
    "май": 5, "мая": 5,
    "июнь": 6, "июня": 6,
    "июль": 7, "июля": 7,
    "август": 8, "августа": 8,
    "сентябрь": 9, "сентября": 9,
    "октябрь": 10, "октября": 10,
    "ноябрь": 11, "ноября": 11,
    "декабрь": 12, "декабря": 12,
}

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (выключен по умолчанию)."""
    data = settings_db.get(guild_id, MODULE_NAME)
    roster = data.get("roster", {})
    applications = data.get("applications", {})
    birthdays = data.get("birthdays", {})
    return {
        "enabled": bool(data.get("enabled", False)),
        "roster": {
            "list_channel_id": str(roster.get("list_channel_id") or ""),
            "target_roles": [
                {"label": str(r.get("label", "")), "role_id": str(r.get("role_id", ""))}
                for r in roster.get("target_roles", [])
            ],
        },
        "applications": {
            "application_channel_id": str(applications.get("application_channel_id") or ""),
            "log_channel_id": str(applications.get("log_channel_id") or ""),
            "staff_role_ids": [str(v) for v in applications.get("staff_role_ids", [])],
            "ticket_manager_role_id": str(applications.get("ticket_manager_role_id") or ""),
            "notify_role_id": str(applications.get("notify_role_id") or ""),
            "ticket_active_role_id": str(applications.get("ticket_active_role_id") or ""),
            "approve_role_ids": [str(v) for v in applications.get("approve_role_ids", [])],
            "yes_emoji_id": str(applications.get("yes_emoji_id") or ""),
            "no_emoji_id": str(applications.get("no_emoji_id") or ""),
            "thread_archive_minutes": int(applications.get("thread_archive_minutes", DEFAULT_THREAD_ARCHIVE_MINUTES)),
        },
        "birthdays": {
            "channel_id": str(birthdays.get("channel_id") or ""),
            "list_channel_id": str(birthdays.get("list_channel_id") or ""),
        },
    }


# ────────────────────────── Доступ ──────────────────────────

def has_staff_access(member) -> bool:
    if member.guild_permissions.administrator:
        return True
    staff_ids = {int(v) for v in get_settings(member.guild.id)["applications"]["staff_role_ids"]}
    return bool({role.id for role in member.roles} & staff_ids)


def can_manage_tickets(member) -> bool:
    if member.guild_permissions.administrator:
        return True
    raw = get_settings(member.guild.id)["applications"]["ticket_manager_role_id"]
    if not raw:
        return False
    return any(role.id == int(raw) for role in member.roles)


# ────────────────────────── Статусы тикета ──────────────────────────

def status_color(status: str) -> int:
    return {
        "open": embed_style.INFO_INT,
        "approved": embed_style.SUCCESS_INT,
        "denied": embed_style.DANGER_INT,
        "closed": embed_style.GOLD_INT,
    }.get(status, embed_style.NEUTRAL_INT)


def status_label(status: str, lang: str = i18n.DEFAULT_LANGUAGE) -> str:
    key = f"family.status.{status}"
    text = i18n.t(key, lang)
    return text if text != key else status


# ────────────────────────── Дни рождения ──────────────────────────

def parse_birthday_date(value: str, lang: str = i18n.DEFAULT_LANGUAGE) -> tuple[int, int, str]:
    cleaned = " ".join(value.strip().lower().replace(",", " ").split())
    numeric = re.fullmatch(r"(\d{1,2})[./\- ](\d{1,2})(?:[./\- ](\d{2,4}))?", cleaned)
    if numeric:
        day = int(numeric.group(1))
        month = int(numeric.group(2))
        year = numeric.group(3)
    else:
        textual = re.fullmatch(r"(\d{1,2})\s+([а-яё]+)(?:\s+(\d{2,4}))?", cleaned)
        if not textual or textual.group(2) not in MONTH_ALIASES:
            raise ValueError(i18n.t("family.birthdays.format_error", lang))
        day = int(textual.group(1))
        month = MONTH_ALIASES[textual.group(2)]
        year = textual.group(3)

    if not 1 <= month <= 12:
        raise ValueError(i18n.t("family.birthdays.month_range", lang))

    max_day = 29 if month == 2 else 30 if month in {4, 6, 9, 11} else 31
    if not 1 <= day <= max_day:
        raise ValueError(i18n.t("family.birthdays.invalid_date", lang))

    display = f"{day:02d}.{month:02d}"
    if year:
        if len(year) == 2:
            year = f"20{year}"
        display = f"{display}.{year}"
    return day, month, display


def build_birthday_text(rows: list[dict], guild, lang: str = i18n.DEFAULT_LANGUAGE) -> str:
    grouped: dict[int, list[dict]] = {month: [] for month in MONTHS}
    for row in rows:
        grouped[row["month"]].append(row)

    lines = [i18n.t("family.birthdays.list_header", lang), ""]
    for month, _ in MONTHS.items():
        name = i18n.t(f"family.month.{month}", lang)
        lines.append(i18n.t("family.birthdays.list_month_line", lang, month=month, name=name))
        for row in grouped[month]:
            member = guild.get_member(row["user_id"])
            mention = member.mention if member else f"<@{row['user_id']}>"
            lines.append(f"- {mention} {row['date_display']}")
        lines.append("")
    return "\n".join(lines).strip()
