import pytest

import spam_core


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    import settings_db

    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


def test_spam_settings_defaults():
    settings = spam_core.get_settings(9001)
    assert settings == {
        "limit_with_attachments": 3,
        "limit_without_attachments": 5,
        "time_window_sec": 60,
    }


def test_message_limit_with_attachments():
    settings = spam_core.get_settings(9002)
    assert spam_core.message_limit(settings, True) == 3
    assert spam_core.message_limit(settings, False) == 5


def test_spam_settings_roundtrip():
    spam_core.save_config(
        9003,
        {
            "limit_with_attachments": 2,
            "limit_without_attachments": 4,
            "time_window_sec": 120,
        },
    )
    assert spam_core.get_settings(9003)["time_window_sec"] == 120
