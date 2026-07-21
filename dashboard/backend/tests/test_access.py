"""Тесты модели доступа Фазы 2.3 (Manage Server / main-guild / OAuth-фильтр серверов)."""

from dashboard.backend import access


class _Perms:
    def __init__(self, administrator=False, manage_guild=False):
        self.administrator = administrator
        self.manage_guild = manage_guild


class _Role:
    def __init__(self, role_id):
        self.id = role_id


class _Member:
    def __init__(self, administrator=False, manage_guild=False, role_ids=()):
        self.guild_permissions = _Perms(administrator, manage_guild)
        self.roles = [_Role(r) for r in role_ids]


class _FakeBot:
    def __init__(self, present_guild_ids):
        self._present = set(present_guild_ids)

    def get_guild(self, guild_id):
        return object() if guild_id in self._present else None


def test_has_manage_server_true_for_manage_guild():
    assert access.has_manage_server(_Member(manage_guild=True)) is True


def test_has_manage_server_true_for_administrator():
    assert access.has_manage_server(_Member(administrator=True)) is True


def test_has_manage_server_false_for_plain_member():
    assert access.has_manage_server(_Member()) is False


def test_can_manage_guild_permissions_bitmask():
    assert access.can_manage_guild_permissions(access.PERMISSION_MANAGE_GUILD) is True
    assert access.can_manage_guild_permissions(access.PERMISSION_ADMINISTRATOR) is True
    assert access.can_manage_guild_permissions(0) is False
    assert access.can_manage_guild_permissions(0x400) is False  # какой-то другой бит


def test_manageable_guilds_filters_and_annotates_has_bot():
    guilds = [
        {"id": "1", "name": "Managed+Bot", "permissions": str(access.PERMISSION_MANAGE_GUILD)},
        {"id": "2", "name": "Managed-NoBot", "permissions": str(access.PERMISSION_ADMINISTRATOR)},
        {"id": "3", "name": "NoPerms", "permissions": "0"},
        {"id": "4", "name": "Owner", "permissions": "0", "owner": True},
    ]
    result = access.manageable_guilds(guilds, _FakeBot(present_guild_ids={1}))

    by_id = {g["id"]: g for g in result}
    assert set(by_id) == {"1", "2", "4"}  # сервер без прав отфильтрован
    assert by_id["1"]["has_bot"] is True
    assert by_id["2"]["has_bot"] is False
    assert by_id["4"]["has_bot"] is False


def test_super_admin_by_role_membership():
    role_id = int(next(iter(access.SUPER_ADMIN_ROLE_IDS)))
    assert access.has_super_admin_access(_Member(role_ids=[role_id])) is True
    assert access.has_super_admin_access(_Member(role_ids=[123])) is False


def test_main_guild_id_is_int():
    assert isinstance(access.MAIN_GUILD_ID, int)
