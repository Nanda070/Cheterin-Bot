import re
from pathlib import Path

import pytest

import i18n
import language_core
import settings_db
from locales import en as en_locale
from locales import ru as ru_locale

_REPO_ROOT = Path(__file__).resolve().parents[3]
_LITERAL_T_RE = re.compile(r'i18n\.t\(\s*"([a-z][a-z0-9_.]+)"')
_LITERAL_GUILD_T_RE = re.compile(r'i18n\.guild_t\([^,]+,\s*"([a-z][a-z0-9_.]+)"')


def _bot_py_files() -> list[Path]:
    files = [p for p in _REPO_ROOT.glob("*.py") if not p.name.startswith("_audit")]
    backend = _REPO_ROOT / "dashboard" / "backend"
    if backend.exists():
        for path in backend.rglob("*.py"):
            if "tests" in path.parts or path.name.startswith("_audit"):
                continue
            files.append(path)
    return files


def _collect_literal_i18n_keys() -> set[str]:
    keys: set[str] = set()
    for path in _bot_py_files():
        src = path.read_text(encoding="utf-8")
        if "i18n." not in src:
            continue
        keys.update(_LITERAL_T_RE.findall(src))
        keys.update(_LITERAL_GUILD_T_RE.findall(src))
    return keys


def test_t_returns_russian_by_default():
    assert i18n.t("error.module_disabled") == "Модуль отключён."


def test_t_returns_english_when_requested():
    assert i18n.t("error.module_disabled", "en") == "This module is disabled."


def test_t_formats_placeholders():
    assert i18n.t("welcome.title", "ru", guild_name="Test") == "Добро пожаловать на Test!"


def test_t_falls_back_to_key_for_unknown():
    assert i18n.t("missing.key", "en") == "missing.key"


def test_t_falls_back_to_russian_for_unknown_lang():
    assert i18n.t("error.module_disabled", "fr") == "Модуль отключён."


def test_module_disabled_named():
    assert "Развлечения" in i18n.module_disabled("ru", "fun")
    assert "Fun" in i18n.module_disabled("en", "fun")


def test_guild_t_uses_server_language(monkeypatch, tmp_path):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    settings_db.init()
    language_core.set_language(42, "en")
    assert i18n.guild_t(42, "verification.success").startswith("✅ Welcome")


def test_pick_random_returns_known_key():
    text = i18n.pick_random("fun.roulette.intro", "ru", 6)
    assert text.endswith("…")


def test_literal_i18n_keys_exist_in_both_locales():
    """Catch blackjack-style mismatches: code key not present in locale dicts."""
    en_keys = set(en_locale.MESSAGES)
    ru_keys = set(ru_locale.MESSAGES)
    missing_en = sorted(k for k in _collect_literal_i18n_keys() if k not in en_keys)
    missing_ru = sorted(k for k in _collect_literal_i18n_keys() if k not in ru_keys)
    assert missing_en == [], f"Missing EN locale keys: {missing_en}"
    assert missing_ru == [], f"Missing RU locale keys: {missing_ru}"


def test_blackjack_locale_keys_resolve():
    """Regression: buttons/footer must not show raw keys like casino.bj.btn.hit."""
    keys = (
        "casino.bj.btn_hit",
        "casino.bj.btn_stand",
        "casino.bj.btn_double",
        "casino.bj.balance_footer",
        "casino.bj.timeout_footer",
        "casino.bj.result.blackjack",
        "casino.bj.result.win",
        "casino.bj.result.push",
        "casino.bj.result.lose",
    )
    for key in keys:
        for lang in ("ru", "en"):
            text = i18n.t(key, lang, balance="100")
            assert text != key, f"{key} unresolved for {lang}"
            assert not text.startswith("casino.bj.btn."), f"old dotted btn key style: {text}"


def test_fun_roulette_pick_random_keys_exist():
    for prefix, count in (
        ("fun.roulette.intro", 6),
        ("fun.roulette.survive", 10),
        ("fun.roulette.death", 8),
    ):
        for i in range(1, count + 1):
            key = f"{prefix}.{i}"
            assert key in en_locale.MESSAGES, key
            assert key in ru_locale.MESSAGES, key


def test_locale_placeholder_parity():
    """EN/RU strings for the same key should declare the same {placeholders}."""
    ph = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")
    mismatches = []
    for key in sorted(set(en_locale.MESSAGES) & set(ru_locale.MESSAGES)):
        en_ph = set(ph.findall(en_locale.MESSAGES[key]))
        ru_ph = set(ph.findall(ru_locale.MESSAGES[key]))
        if en_ph != ru_ph:
            mismatches.append((key, sorted(en_ph), sorted(ru_ph)))
    assert mismatches == []
