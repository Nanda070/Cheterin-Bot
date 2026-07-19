"""Тесты ядра антирейда: настройки (выключен по умолчанию), детект свежих
аккаунтов, скользящее окно входов."""

from datetime import datetime, timedelta, timezone

import pytest

import antiraid_core


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(antiraid_core, "CONFIG_FILE", str(tmp_path / "antiraid_config.json"))
    monkeypatch.setattr(antiraid_core, "_cache", None, raising=False)
    monkeypatch.setattr(antiraid_core, "_cache_mtime", None, raising=False)


def test_settings_disabled_by_default():
    settings = antiraid_core.get_settings()
    assert settings["enabled"] is False
    assert settings["join_window_sec"] == 10
    assert settings["join_threshold"] == 5
    assert settings["min_account_age_hours"] == 24
    assert settings["action_lockdown"] is True
    assert settings["action_slowmode_sec"] == 0
    assert settings["cooldown_minutes"] == 30


def test_settings_roundtrip():
    antiraid_core.save_config({"enabled": True, "join_threshold": 10, "action_slowmode_sec": 30})
    settings = antiraid_core.get_settings()
    assert settings["enabled"] is True
    assert settings["join_threshold"] == 10
    assert settings["action_slowmode_sec"] == 30


# ────────────────────────── is_suspicious_account ──────────────────────────

def test_fresh_account_is_suspicious():
    created = datetime(2026, 1, 1, tzinfo=timezone.utc)
    joined = created + timedelta(hours=1)
    assert antiraid_core.is_suspicious_account(created, joined, min_age_hours=24) is True


def test_old_account_is_not_suspicious():
    created = datetime(2020, 1, 1, tzinfo=timezone.utc)
    joined = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert antiraid_core.is_suspicious_account(created, joined, min_age_hours=24) is False


def test_zero_min_age_treats_everyone_as_suspicious():
    created = datetime(2020, 1, 1, tzinfo=timezone.utc)
    joined = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert antiraid_core.is_suspicious_account(created, joined, min_age_hours=0) is True


# ────────────────────────── JoinTracker ──────────────────────────

def test_tracker_counts_within_window():
    tracker = antiraid_core.JoinTracker(window_sec=10)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert tracker.register(base) == 1
    assert tracker.register(base + timedelta(seconds=5)) == 2
    assert tracker.register(base + timedelta(seconds=9)) == 3


def test_tracker_evicts_entries_outside_window():
    tracker = antiraid_core.JoinTracker(window_sec=10)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tracker.register(base)
    tracker.register(base + timedelta(seconds=5))
    count = tracker.register(base + timedelta(seconds=15))  # первый вход выпал из окна
    assert count == 2


def test_tracker_reset_clears_all():
    tracker = antiraid_core.JoinTracker(window_sec=10)
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    tracker.register(base)
    tracker.register(base)
    tracker.reset()
    assert tracker.register(base) == 1
