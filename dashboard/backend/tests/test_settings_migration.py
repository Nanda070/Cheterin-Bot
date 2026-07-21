"""Тесты settings_migration: перенос плоских JSON в settings_db, идемпотентность."""

import json
import os

import pytest

import settings_db
import settings_migration


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def test_migrate_one_moves_data_and_renames_file(tmp_path):
    config_path = tmp_path / "fun_config.json"
    _write_json(config_path, {"enabled": True})

    migrated = settings_migration.migrate_one(404, "fun", str(config_path))

    assert migrated is True
    assert settings_db.get(404, "fun") == {"enabled": True}
    assert not config_path.exists()
    assert (tmp_path / "fun_config.json.migrated.bak").exists()


def test_migrate_one_missing_file_is_noop(tmp_path):
    config_path = tmp_path / "does_not_exist.json"
    migrated = settings_migration.migrate_one(404, "fun", str(config_path))
    assert migrated is False
    assert settings_db.has(404, "fun") is False


def test_migrate_one_skips_when_already_migrated(tmp_path):
    config_path = tmp_path / "fun_config.json"
    settings_db.put(404, "fun", {"enabled": True})  # уже "мигрировано" ранее
    _write_json(config_path, {"enabled": False})  # файл почему-то опять появился

    migrated = settings_migration.migrate_one(404, "fun", str(config_path))

    assert migrated is False
    assert settings_db.get(404, "fun") == {"enabled": True}  # старое значение не тронуто
    assert config_path.exists()  # файл не тронут — не переименован повторно


def test_migrate_one_treats_corrupt_json_as_empty_object(tmp_path):
    config_path = tmp_path / "broken_config.json"
    config_path.write_text("{not valid json", encoding="utf-8")

    migrated = settings_migration.migrate_one(404, "broken", str(config_path))

    assert migrated is True
    assert settings_db.get(404, "broken") == {}
    assert not config_path.exists()


def test_migrate_all_migrates_existing_files_only(tmp_path, monkeypatch):
    fun_path = tmp_path / "fun_config.json"
    economy_path = tmp_path / "economy_config.json"
    missing_path = tmp_path / "missing_config.json"
    _write_json(fun_path, {"enabled": True})
    _write_json(economy_path, {"enabled": False})

    monkeypatch.setattr(settings_migration, "MODULE_FILE_MAP", {
        "fun": str(fun_path),
        "economy": str(economy_path),
        "missing": str(missing_path),
    })

    migrated = settings_migration.migrate_all(404)

    assert set(migrated) == {"fun", "economy"}
    assert settings_db.get(404, "fun") == {"enabled": True}
    assert settings_db.get(404, "economy") == {"enabled": False}
    assert settings_db.has(404, "missing") is False


def test_migrate_all_is_idempotent_across_two_runs(tmp_path, monkeypatch):
    fun_path = tmp_path / "fun_config.json"
    _write_json(fun_path, {"enabled": True})
    monkeypatch.setattr(settings_migration, "MODULE_FILE_MAP", {"fun": str(fun_path)})

    first = settings_migration.migrate_all(404)
    second = settings_migration.migrate_all(404)

    assert first == ["fun"]
    assert second == []
