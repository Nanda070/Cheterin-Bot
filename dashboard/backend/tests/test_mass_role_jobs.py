import discord
import pytest

from dashboard.backend.mass_role_jobs import JOBS, MassAssignJob, run_mass_assign
from dashboard.backend.tests.fakes import FakeGuild, FakeMember, FakeRole


class _StubForbidden(discord.Forbidden):
    def __init__(self):
        pass


def _dashboard_reason(reason, moderator):
    return f"Dashboard: {reason} — by {moderator.name} ({moderator.id})"


@pytest.fixture(autouse=True)
def clear_jobs():
    JOBS.clear()
    yield
    JOBS.clear()


@pytest.mark.asyncio
async def test_assigns_role_to_all_members_without_it():
    role = FakeRole(7, name="VIP", position=5)
    members = [FakeMember(100 + i, name=f"m{i}") for i in range(3)]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.status == "completed"
    assert job.succeeded == 3
    assert job.skipped == 0
    assert job.failed == 0
    assert job.processed == 3
    for member in members:
        action, kwargs = member.action_calls[0]
        assert action == "add_roles"
        assert kwargs["role"].id == 7
        assert "Dashboard: массовая выдача роли VIP" in kwargs["reason"]
        assert "(10)" in kwargs["reason"]


@pytest.mark.asyncio
async def test_skips_members_who_already_have_the_role():
    role = FakeRole(7, name="VIP", position=5)
    already_has = FakeMember(100, name="has-it", roles=[FakeRole(7, name="VIP", position=5)])
    needs_it = FakeMember(101, name="needs-it")
    members = [already_has, needs_it]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.skipped == 1
    assert job.succeeded == 1
    assert already_has.action_calls == []
    assert needs_it.action_calls[0][0] == "add_roles"


@pytest.mark.asyncio
async def test_continues_after_one_member_fails():
    role = FakeRole(7, name="VIP", position=5)
    broken = FakeMember(100, name="broken")
    broken.action_raises = _StubForbidden()
    fine = FakeMember(101, name="fine")
    members = [broken, fine]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.status == "completed"
    assert job.failed == 1
    assert job.succeeded == 1
    assert job.processed == 2
    assert len(job.errors) == 1
    assert "broken" in job.errors[0]


@pytest.mark.asyncio
async def test_processed_equals_sum_of_outcomes():
    role = FakeRole(7, name="VIP", position=5)
    members = [FakeMember(100 + i, name=f"m{i}") for i in range(5)]
    guild = FakeGuild(members=members, roles=[role])
    moderator = FakeMember(10, name="mod")

    JOBS["job-1"] = MassAssignJob(status="running", total=len(members))
    await run_mass_assign("job-1", guild, role, members, moderator, _dashboard_reason)

    job = JOBS["job-1"]
    assert job.processed == job.succeeded + job.skipped + job.failed
    assert job.processed == job.total
