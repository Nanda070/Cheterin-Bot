"""Тесты SQLite-хранилища согласий верификации."""

import bot.modules.moderation.verification_db as verification_db


def test_record_get_clear_and_list(tmp_path, monkeypatch):
    monkeypatch.setenv("VERIFICATION_DB_PATH", str(tmp_path / "verification.db"))
    verification_db.init()

    row = verification_db.record_consent(1, 20, verified_at="2026-01-01T00:00:00+00:00")
    assert row["guild_id"] == 1
    assert row["user_id"] == 20
    assert row["verified_at"] == "2026-01-01T00:00:00+00:00"

    assert verification_db.get_consent(1, 20)["verified_at"] == "2026-01-01T00:00:00+00:00"
    assert verification_db.get_consent(1, 99) is None

    verification_db.record_consent(1, 21, verified_at="2026-02-01T00:00:00+00:00")
    listed = verification_db.list_consents(1)
    assert [r["user_id"] for r in listed] == [20, 21]

    assert verification_db.clear_consent(1, 20) is True
    assert verification_db.get_consent(1, 20) is None
    assert verification_db.clear_consent(1, 20) is False
