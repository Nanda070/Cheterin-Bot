"""Tests for banner rotation settings + dynamic banner PNG renderer."""

from __future__ import annotations

import io

import pytest
from PIL import Image

import banner_rotation_core
import dynamic_banner
import settings_db


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    monkeypatch.setattr(banner_rotation_core, "ASSETS_ROOT", tmp_path / "banner_assets")
    settings_db.init()


def test_get_settings_defaults_banner_mode_playlist():
    cfg = banner_rotation_core.get_settings(42)
    assert cfg["banner_mode"] == banner_rotation_core.BANNER_MODE_PLAYLIST
    assert cfg["banner_enabled"] is True


def test_save_settings_persists_dynamic_mode():
    cfg = banner_rotation_core.save_settings(
        7,
        enabled=True,
        banner_enabled=True,
        banner_mode="dynamic",
        icon_enabled=False,
        interval_minutes=30,
    )
    assert cfg["enabled"] is True
    assert cfg["banner_mode"] == "dynamic"
    assert cfg["icon_enabled"] is False
    assert cfg["interval_minutes"] == 30
    assert banner_rotation_core.get_settings(7)["banner_mode"] == "dynamic"


def test_both_mode_and_dynamic_window_are_guild_scoped():
    first = banner_rotation_core.save_settings(
        7, enabled=True, banner_mode="both", dynamic_window_days=14
    )
    second = banner_rotation_core.save_settings(
        8, enabled=True, banner_mode="dynamic", dynamic_window_days=999
    )
    assert first["banner_mode"] == "both"
    assert first["dynamic_window_days"] == 14
    assert second["dynamic_window_days"] == banner_rotation_core.DYNAMIC_WINDOW_DAYS_MAX
    assert banner_rotation_core.get_settings(7)["dynamic_window_days"] == 14


def test_normalize_banner_mode_rejects_unknown():
    with pytest.raises(ValueError, match="invalid_banner_mode"):
        banner_rotation_core.normalize_banner_mode("rainbow")


def test_invalid_stored_banner_mode_falls_back_to_playlist():
    settings_db.put(9, banner_rotation_core.MODULE_NAME, {"banner_mode": "nope"})
    assert banner_rotation_core.get_settings(9)["banner_mode"] == "playlist"


def test_render_dynamic_banner_png_dimensions_and_signature():
    raw = dynamic_banner.render_dynamic_banner(
        display_name="Тестер",
        avatar_bytes=None,
        member_count=1234,
        voice_count=7,
        guild_name="Cheterin Test",
        lang="ru",
    )
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")
    img = Image.open(io.BytesIO(raw))
    assert img.size == (dynamic_banner.BANNER_W, dynamic_banner.BANNER_H)
    assert img.mode == "RGB"


def test_render_dynamic_banner_handles_missing_active_user_en():
    raw = dynamic_banner.render_dynamic_banner(
        display_name=None,
        avatar_bytes=None,
        member_count=0,
        voice_count=0,
        lang="en",
    )
    assert len(raw) > 500
    assert Image.open(io.BytesIO(raw)).size == (960, 540)


def test_want_banner_logic_dynamic_without_playlist(tmp_path):
    """Dynamic mode does not require uploaded banners."""
    banner_rotation_core.save_settings(
        11,
        enabled=True,
        banner_enabled=True,
        banner_mode="dynamic",
        icon_enabled=False,
    )
    cfg = banner_rotation_core.get_settings(11)
    assert cfg["banners"] == []
    assert cfg["banner_mode"] == "dynamic"
    assert cfg["banner_enabled"] is True
