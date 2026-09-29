"""Тесты settings_db: хранилище настроек модулей per-guild (Фаза 2.1)."""

import pytest

import bot.core.settings_db as settings_db


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_missing_returns_empty_dict():
    assert settings_db.get(404, "fun") == {}


def test_put_then_get_roundtrip():
    settings_db.put(404, "fun", {"enabled": True, "roulette_cooldown_sec": 30})
    assert settings_db.get(404, "fun") == {"enabled": True, "roulette_cooldown_sec": 30}


def test_put_overwrites_existing():
    settings_db.put(404, "fun", {"enabled": True})
    settings_db.put(404, "fun", {"enabled": False})
    assert settings_db.get(404, "fun") == {"enabled": False}


def test_isolated_by_guild_id():
    settings_db.put(1, "fun", {"enabled": True})
    settings_db.put(2, "fun", {"enabled": False})
    assert settings_db.get(1, "fun") == {"enabled": True}
    assert settings_db.get(2, "fun") == {"enabled": False}


def test_isolated_by_module():
    settings_db.put(404, "fun", {"enabled": True})
    settings_db.put(404, "economy", {"enabled": False})
    assert settings_db.get(404, "fun") == {"enabled": True}
    assert settings_db.get(404, "economy") == {"enabled": False}


def test_get_uses_cache_without_hitting_db_again(monkeypatch):
    settings_db.put(404, "fun", {"enabled": True})
    settings_db.get(404, "fun")  # populates cache

    def _boom():
        raise AssertionError("не должно обращаться к БД повторно — значение в кэше")

    monkeypatch.setattr(settings_db, "connect", _boom)
    assert settings_db.get(404, "fun") == {"enabled": True}


def test_put_refreshes_cache_immediately():
    settings_db.put(404, "fun", {"enabled": True})
    settings_db.get(404, "fun")  # populates cache with old value
    settings_db.put(404, "fun", {"enabled": False})
    assert settings_db.get(404, "fun") == {"enabled": False}


def test_get_returns_a_copy_not_the_cached_reference():
    settings_db.put(404, "fun", {"items": [1, 2, 3]})
    result = settings_db.get(404, "fun")
    result["items"].append(4)
    assert settings_db.get(404, "fun") == {"items": [1, 2, 3]}


def test_has_reflects_existing_rows():
    assert settings_db.has(404, "fun") is False
    settings_db.put(404, "fun", {"enabled": True})
    assert settings_db.has(404, "fun") is True
    assert settings_db.has(404, "economy") is False
