import pytest

import bot.modules.games.family_core as family_core
import bot.core.settings_db as settings_db

GUILD_ID = 404


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_settings_defaults_disabled():
    settings = family_core.get_settings(GUILD_ID)
    assert settings["enabled"] is False
    assert settings["roster"]["target_roles"] == []
    assert settings["applications"]["thread_archive_minutes"] == family_core.DEFAULT_THREAD_ARCHIVE_MINUTES
    assert settings["applications"]["staff_role_ids"] == []


def test_save_and_reload_settings():
    family_core.save_config(GUILD_ID, {
        "enabled": True,
        "roster": {"list_channel_id": "500", "target_roles": [{"label": "High", "role_id": "7"}]},
        "applications": {
            "application_channel_id": "600",
            "staff_role_ids": ["1", "2"],
            "thread_archive_minutes": 1440,
        },
        "birthdays": {"channel_id": "700"},
    })
    settings = family_core.get_settings(GUILD_ID)
    assert settings["enabled"] is True
    assert settings["roster"]["target_roles"] == [{"label": "High", "role_id": "7"}]
    assert settings["applications"]["application_channel_id"] == "600"
    assert settings["applications"]["staff_role_ids"] == ["1", "2"]
    assert settings["applications"]["thread_archive_minutes"] == 1440
    assert settings["birthdays"]["channel_id"] == "700"
    assert settings["birthdays"]["list_channel_id"] == ""


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("01.02", (1, 2, "01.02")),
        ("1.2", (1, 2, "01.02")),
        ("01/02/2000", (1, 2, "01.02.2000")),
        ("01-02-99", (1, 2, "01.02.2099")),
        ("1 января", (1, 1, "01.01")),
        ("15 декабря 2001", (15, 12, "15.12.2001")),
    ],
)
def test_parse_birthday_date_valid(raw, expected):
    assert family_core.parse_birthday_date(raw) == expected


@pytest.mark.parametrize("raw", ["", "32.01", "29.13", "not a date", "0.5"])
def test_parse_birthday_date_invalid(raw):
    with pytest.raises(ValueError):
        family_core.parse_birthday_date(raw)


def test_parse_birthday_date_feb29_always_allowed():
    # Оригинал не проверяет високосность конкретного года — 29 фев принимается всегда.
    assert family_core.parse_birthday_date("29.02") == (29, 2, "29.02")


def test_status_color_and_label():
    assert family_core.status_color("open") == 0x5865F2
    assert family_core.status_color("approved") == 0x57F287
    assert family_core.status_color("denied") == 0xED4245
    assert family_core.status_color("closed") == 0xFEE75C
    assert family_core.status_color("unknown") == 0x2B2D31

    assert family_core.status_label("open") == "На рассмотрении"
    assert family_core.status_label("approved") == "Принята"
    assert family_core.status_label("denied") == "Отклонена"
    assert family_core.status_label("closed") == "Закрыта"


class _FakeMember:
    def __init__(self, member_id, mention):
        self.id = member_id
        self.mention = mention


class _FakeGuild:
    def __init__(self, members):
        self._members = {m.id: m for m in members}

    def get_member(self, user_id):
        return self._members.get(user_id)


def test_build_birthday_text_groups_by_month_and_resolves_mentions():
    guild = _FakeGuild([_FakeMember(1, "@Alice")])
    rows = [
        {"user_id": 1, "month": 1, "day": 5, "date_display": "05.01"},
        {"user_id": 999, "month": 1, "day": 10, "date_display": "10.01"},  # покинул сервер
    ]
    text = family_core.build_birthday_text(rows, guild)
    assert "@Alice 05.01" in text
    assert "<@999> 10.01" in text
    assert "1 Январь" in text


class _FakeGuildRef:
    id = GUILD_ID


def test_has_staff_access_admin_bypasses_role_check():
    class Perms:
        administrator = True

    class Member:
        guild_permissions = Perms()
        roles = []
        guild = _FakeGuildRef()

    assert family_core.has_staff_access(Member()) is True


def test_has_staff_access_via_role():
    family_core.save_config(GUILD_ID, {"applications": {"staff_role_ids": ["42"]}})

    class Perms:
        administrator = False

    class Role:
        def __init__(self, rid):
            self.id = rid

    class Member:
        guild_permissions = Perms()
        roles = [Role(42)]
        guild = _FakeGuildRef()

    assert family_core.has_staff_access(Member()) is True

    class MemberNoRole:
        guild_permissions = Perms()
        roles = [Role(1)]
        guild = _FakeGuildRef()

    assert family_core.has_staff_access(MemberNoRole()) is False


def test_can_manage_tickets_requires_configured_role():
    class Perms:
        administrator = False

    class Role:
        def __init__(self, rid):
            self.id = rid

    class Member:
        guild_permissions = Perms()
        roles = [Role(99)]
        guild = _FakeGuildRef()

    # Роль тикет-менеджера не настроена — доступа нет даже с произвольной ролью.
    assert family_core.can_manage_tickets(Member()) is False

    family_core.save_config(GUILD_ID, {"applications": {"ticket_manager_role_id": "99"}})
    assert family_core.can_manage_tickets(Member()) is True
