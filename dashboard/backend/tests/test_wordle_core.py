"""Тесты ядра Вордла: целостность словаря, оценка догадок, слово дня, настройки."""

import re
from collections import Counter
from datetime import date

import pytest

import bot.core.settings_db as settings_db
import bot.modules.games.wordle_core as wordle_core
import bot.data.wordle_data as wordle_data


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


# ────────────────────────── Словарь ──────────────────────────

def test_dictionary_integrity():
    all_words = wordle_data.ANSWER_WORDS + wordle_data.EXTRA_GUESSES
    assert all(len(w) == wordle_core.WORD_LEN for w in all_words)
    assert all(re.fullmatch("[а-я]{5}", w) for w in all_words), "только кириллица без ё"
    dups = [w for w, c in Counter(all_words).items() if c > 1]
    assert dups == []
    assert len(wordle_data.ANSWER_WORDS) >= 500


def test_all_answers_are_guessable():
    assert set(wordle_data.ANSWER_WORDS) <= wordle_data.ALL_WORDS


# ────────────────────────── Нормализация и валидация ──────────────────────────

def test_normalize_lowers_and_replaces_yo():
    assert wordle_core.normalize("  Актёр ") == "актер"


def test_guess_error_cases():
    assert wordle_core.guess_error("дом") is not None  # короткое
    assert wordle_core.guess_error("word!") is not None  # не кириллица
    assert wordle_core.guess_error("бзыкф") is not None  # нет в словаре
    assert wordle_core.guess_error("школа") is None


# ────────────────────────── Оценка догадки ──────────────────────────

def test_evaluate_all_green():
    assert wordle_core.evaluate("школа", "школа") == "ggggg"
    assert wordle_core.is_win(wordle_core.evaluate("школа", "школа"))


def test_evaluate_yellow_and_gray():
    # ответ «канат»: к на месте, а есть (2 шт), т есть не на месте
    states = wordle_core.evaluate("катер", "канат")
    assert states[0] == wordle_core.GREEN  # к
    assert states[1] == wordle_core.GREEN  # а
    assert states[2] == wordle_core.YELLOW  # т есть в слове
    assert states[3] == wordle_core.GRAY  # е нет
    assert states[4] == wordle_core.GRAY  # р нет


def test_evaluate_duplicate_letters_consume_stock():
    # В ответе одна «а», в догадке две: только одна должна подсветиться
    states = wordle_core.evaluate("арара", "актер")
    a_marks = [s for ch, s in zip("арара", states) if ch == "а"]
    assert a_marks.count(wordle_core.GREEN) == 1
    assert a_marks.count(wordle_core.YELLOW) == 0
    assert a_marks.count(wordle_core.GRAY) == 2
    r_marks = [s for ch, s in zip("арара", states) if ch == "р"]
    assert r_marks.count(wordle_core.YELLOW) == 1  # одна «р» в ответе


def test_evaluate_green_priority_over_yellow():
    # Единственная «о» ответа расходуется зелёной позицией — дубль в догадке серый
    states = wordle_core.evaluate("особа", "школа")
    assert states[2] == wordle_core.GREEN  # о на месте
    assert states[0] == wordle_core.GRAY  # вторая «о» — запас исчерпан зелёной
    assert states[4] == wordle_core.GREEN  # а на месте


# ────────────────────────── Слово дня ──────────────────────────

def test_day_number_epoch():
    assert wordle_core.day_number(wordle_core.EPOCH) == 1
    assert wordle_core.day_number(date(2026, 7, 21)) == 3


def test_word_for_day_deterministic_and_from_answers():
    word = wordle_core.word_for_day(5)
    assert word == wordle_core.word_for_day(5)
    assert word in wordle_data.ANSWER_WORDS
    assert wordle_core.word_for_day(6) != word or len(wordle_data.ANSWER_WORDS) == 1


def test_word_for_day_wraps_around():
    total = len(wordle_data.ANSWER_WORDS)
    assert wordle_core.word_for_day(1) == wordle_core.word_for_day(total + 1)


def test_training_word_from_answers():
    assert wordle_core.training_word() in wordle_data.ANSWER_WORDS


# ────────────────────────── Отрисовка ──────────────────────────

def test_board_lines_pads_empty_rows():
    lines = wordle_core.board_lines(["школа"], ["ggggg"])
    assert len(lines) == wordle_core.MAX_ATTEMPTS
    assert "ШКОЛА" in lines[0]
    assert lines[1] == wordle_core.EMPTY_SQUARE * wordle_core.WORD_LEN


def test_share_grid_has_no_letters():
    grid = wordle_core.share_grid(["gybbg", "ggggg"])
    assert "🟩" in grid and "🟨" in grid
    assert not re.search("[а-яА-Я]", grid)


def test_letter_hints():
    present, absent = wordle_core.letter_hints(["катер"], [wordle_core.evaluate("катер", "канат")], "канат")
    assert "К" in present and "Т" in present
    assert "Е" in absent and "Р" in absent


def test_result_score_text():
    assert wordle_core.result_score_text(True, 4) == "4/6"
    assert wordle_core.result_score_text(False, 6) == "X/6"


# ────────────────────────── Настройки ──────────────────────────

def test_settings_defaults():
    settings = wordle_core.get_settings(404)
    assert settings == {"enabled": False, "channel_id": "", "announce_time": "09:00"}


def test_settings_roundtrip():
    wordle_core.save_config(404, {"enabled": True, "channel_id": "42", "announce_time": "18:30"})
    settings = wordle_core.get_settings(404)
    assert settings["enabled"] is True
    assert settings["channel_id"] == "42"
    assert settings["announce_time"] == "18:30"


def test_is_valid_announce_time():
    assert wordle_core.is_valid_announce_time("09:00")
    assert wordle_core.is_valid_announce_time("23:59")
    assert not wordle_core.is_valid_announce_time("24:00")
    assert not wordle_core.is_valid_announce_time("9:60")
    assert not wordle_core.is_valid_announce_time("время")
