from dashboard.backend.access import has_dashboard_access


class FakeRole:
    def __init__(self, role_id):
        self.id = role_id


class FakePermissions:
    def __init__(self, administrator):
        self.administrator = administrator


class FakeMember:
    def __init__(self, role_ids, administrator=False):
        self.roles = [FakeRole(r) for r in role_ids]
        self.guild_permissions = FakePermissions(administrator)


ALLOWED = frozenset({"1324239354209632357", "1324239354209632358"})


def test_member_with_allowed_role_has_access():
    member = FakeMember([1324239354209632358])
    assert has_dashboard_access(member, ALLOWED) is True


def test_member_without_allowed_role_denied():
    member = FakeMember([999])
    assert has_dashboard_access(member, ALLOWED) is False


def test_administrator_always_has_access():
    member = FakeMember([999], administrator=True)
    assert has_dashboard_access(member, ALLOWED) is True


def test_member_with_no_roles_denied():
    member = FakeMember([])
    assert has_dashboard_access(member, ALLOWED) is False
