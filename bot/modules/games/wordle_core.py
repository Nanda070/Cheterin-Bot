"""Ядро русского Вордла: оценка догадок, слово дня, настройки.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и fun_core.py).
Механика повторяет оригинальный Wordle: 6 попыток угадать слово из 5 букв,
🟩 — буква на месте, 🟨 — есть в слове, но не там, ⬛ — буквы в слове нет.
Дубли букв обрабатываются как в оригинале: сначала точные совпадения,
затем «жёлтые» расходуют оставшийся запас буквы.
"""

import random
from datetime import date, datetime, timedelta, timezone

import bot.core.i18n as i18n
import bot.core.settings_db as settings_db
import bot.data.wordle_data as wordle_data

MODULE_NAME = "wordle"

WORD_LEN = 5
MAX_ATTEMPTS = 6

# Thin MSK helper for tests / callers without guild_id. Prefer today_for_guild.
EPOCH = date(2026, 7, 19)
MSK = timezone(timedelta(hours=3))
_SHUFFLE_SEED = 404_2026  # фиксированный: порядок слов не меняется между рестартами

DEFAULT_ANNOUNCE_TIME = "09:00"

GREEN, YELLOW, GRAY = "g", "y", "b"
SQUARES = {GREEN: "🟩", YELLOW: "🟨", GRAY: "⬛"}
EMPTY_SQUARE = "⬜"

_shuffled_answers: list[str] | None = None


# ────────────────────────── Настройки ──────────────────────────

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (выключен по умолчанию).

    channel_id — строка, не число: Discord ID (snowflake) превышает
    Number.MAX_SAFE_INTEGER во фронтенде, JS-числом его хранить нельзя."""
    data = settings_db.get(guild_id, MODULE_NAME)
    return {
        "enabled": bool(data.get("enabled", False)),
        "channel_id": str(data.get("channel_id", "") or ""),
        "announce_time": str(data.get("announce_time", DEFAULT_ANNOUNCE_TIME)),
    }


def is_valid_announce_time(value: str) -> bool:
    parts = value.split(":")
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return False
    hour, minute = int(parts[0]), int(parts[1])
    return 0 <= hour <= 23 and 0 <= minute <= 59


# ────────────────────────── Слова ──────────────────────────

def normalize(word: str) -> str:
    return word.strip().lower().replace("ё", "е")


def guess_error(word: str, *, lang: str | None = None) -> str | None:
    """None — слово валидно, иначе текст ошибки для игрока."""
    lang = lang or i18n.DEFAULT_LANGUAGE
    if len(word) != WORD_LEN:
        return i18n.t("wordle.error.word_len", lang, word_len=WORD_LEN)
    if not all("а" <= ch <= "я" for ch in word):
        return i18n.t("wordle.error.cyrillic_only", lang)
    if word not in wordle_data.ALL_WORDS:
        return i18n.t("wordle.error.not_in_dict", lang, word=word.upper())
    return None


def _answers_shuffled() -> list[str]:
    global _shuffled_answers
    if _shuffled_answers is None:
        words = list(wordle_data.ANSWER_WORDS)
        random.Random(_SHUFFLE_SEED).shuffle(words)
        _shuffled_answers = words
    return _shuffled_answers


def today_msk() -> date:
    """MSK calendar date (tests / callers without guild). Prefer today_for_guild."""
    return datetime.now(MSK).date()


def today_for_guild(guild_id: int) -> date:
    import bot.core.timezone_core as timezone_core

    return timezone_core.now_local(guild_id).date()


def day_number(today: date | None = None) -> int:
    """Номер сегодняшнего Вордла (день эпохи = №1)."""
    return ((today or today_msk()) - EPOCH).days + 1


def word_for_day(day_no: int) -> str:
    words = _answers_shuffled()
    return words[(day_no - 1) % len(words)]


def training_word() -> str:
    return random.choice(wordle_data.ANSWER_WORDS)


# ────────────────────────── Оценка догадки ──────────────────────────

def evaluate(guess: str, answer: str) -> str:
    """Строка из WORD_LEN символов g/y/b (🟩/🟨/⬛)."""
    result = [GRAY] * WORD_LEN
    remaining: dict[str, int] = {}

    for i, (g, a) in enumerate(zip(guess, answer)):
        if g == a:
            result[i] = GREEN
        else:
            remaining[a] = remaining.get(a, 0) + 1

    for i, g in enumerate(guess):
        if result[i] == GREEN:
            continue
        if remaining.get(g, 0) > 0:
            result[i] = YELLOW
            remaining[g] -= 1

    return "".join(result)


def squares(states: str) -> str:
    return "".join(SQUARES[s] for s in states)


def is_win(states: str) -> bool:
    return states == GREEN * WORD_LEN


# ────────────────────────── Отрисовка доски (текст) ──────────────────────────

def board_lines(guesses: list[str], states: list[str]) -> list[str]:
    """Строки эфемерной доски: квадраты + слово, пустые ряды — ⬜."""
    lines = [
        f"{squares(st)}  **`{guess.upper()}`**"
        for guess, st in zip(guesses, states)
    ]
    for _ in range(MAX_ATTEMPTS - len(guesses)):
        lines.append(EMPTY_SQUARE * WORD_LEN)
    return lines


def share_grid(states: list[str]) -> str:
    """Спойлер-фри сетка результата (только квадраты, без букв)."""
    return "\n".join(squares(st) for st in states)


def letter_hints(guesses: list[str], states: list[str], answer: str) -> tuple[str, str]:
    """(буквы в слове, отсутствующие буквы) — подсказка-клавиатура под доской."""
    present: set[str] = set()
    absent: set[str] = set()
    for guess, st in zip(guesses, states):
        for ch, s in zip(guess, st):
            if s == GRAY and ch not in answer:
                absent.add(ch)
            elif s in (GREEN, YELLOW):
                present.add(ch)
    fmt = lambda letters: " ".join(sorted(ch.upper() for ch in letters))  # noqa: E731
    return fmt(present), fmt(absent)


def result_score_text(won: bool, attempts: int) -> str:
    """«4/6» или «X/6» — как в оригинальном шеринге."""
    return f"{attempts}/{MAX_ATTEMPTS}" if won else f"X/{MAX_ATTEMPTS}"
