import asyncio

import pytest

from dashboard.backend import mass_role_jobs
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def clear_jobs():
    mass_role_jobs.JOBS.clear()
    yield
    mass_role_jobs.JOBS.clear()


def build(members=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot_top = FakeRole(900, name="bot-role", position=50)
    me = FakeMember(1, name="bot", top_role=bot_top)
    guild = FakeGuild(members=[moderator] + (members or []), roles=roles or [], me=me)
    return make_moderation_app(FakeBot(guild), [moderation_routes])


async def _wait_for_completion(client, job_id, attempts=50):
    for _ in range(attempts):
        resp = await client.get(f"/api/roles/mass-assign/{job_id}")
        body = await resp.json()
        if body["status"] != "running":
            return body
        await asyncio.sleep(0.01)
    raise AssertionError("job did not complete in time")


@pytest.mark.asyncio
async def test_mass_assign_all_except_bots_completes(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    human = FakeMember(50, name="human", bot=False)
    a_bot = FakeMember(51, name="a-bot", bot=True)
    client = await aiohttp_client(build(members=[human, a_bot], roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all_except_bots"})
    assert resp.status == 202
    job_id = (await resp.json())["job_id"]

    body = await _wait_for_completion(client, job_id)
    assert body["status"] == "completed"
    # build()'s own moderator (FakeMember(10), bot=False) is also a guild member
    # and is non-bot, so "all_except_bots" legitimately includes it too: 2 total.
    assert body["total"] == 2
    assert body["succeeded"] == 2
    assert human.action_calls[0][0] == "add_roles"
    assert a_bot.action_calls == []


@pytest.mark.asyncio
async def test_mass_assign_selected_records_missing_member(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    present = FakeMember(60, name="present")
    client = await aiohttp_client(build(members=[present], roles=[role]))
    await force_login(client, 10)

    resp = await client.post(
        "/api/roles/7/mass-assign",
        json={"target": "selected", "member_ids": ["60", "9999"]},
    )
    assert resp.status == 202
    job_id = (await resp.json())["job_id"]

    body = await _wait_for_completion(client, job_id)
    assert body["total"] == 2
    assert body["succeeded"] == 1
    assert body["failed"] == 1
    assert any("9999" in line for line in body["errors"])


@pytest.mark.asyncio
async def test_mass_assign_selected_requires_member_ids(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "selected", "member_ids": []})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_mass_assign_rejects_role_above_bot(aiohttp_client):
    role = FakeRole(9, name="TooHigh", position=60)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)

    resp = await client.post("/api/roles/9/mass-assign", json={"target": "all"})
    assert resp.status == 403


@pytest.mark.asyncio
async def test_mass_assign_rejects_second_job_while_running(aiohttp_client):
    role = FakeRole(7, name="VIP", position=5)
    client = await aiohttp_client(build(roles=[role]))
    await force_login(client, 10)
    mass_role_jobs.JOBS["already-running"] = mass_role_jobs.MassAssignJob(status="running", total=5)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all"})
    assert resp.status == 409


@pytest.mark.asyncio
async def test_mass_assign_status_404_for_unknown_job(aiohttp_client):
    client = await aiohttp_client(build())
    await force_login(client, 10)
    resp = await client.get("/api/roles/mass-assign/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_mass_assign_requires_auth(aiohttp_client):
    client = await aiohttp_client(build())
    resp = await client.post("/api/roles/7/mass-assign", json={"target": "all"})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_mass_assign_concurrent_requests_only_one_job_starts(aiohttp_client, monkeypatch):
    # Regression test for TOCTOU race: two concurrent mass-assign requests must
    # never both succeed (which would start two simultaneous background jobs
    # mutating live Discord roles) and must never both be rejected.
    #
    # In this in-memory test harness, request bodies are tiny and fully
    # buffered by the time the handler runs, so `await request.json()` on its
    # own does not actually suspend back to the event loop (StreamReader's
    # buffer is already non-empty) and plain asyncio.gather(...) over two
    # client.post(...) calls ends up processing them sequentially end-to-end
    # -- never reproducing the interleaving. To exercise the real race window
    # through the test client's real await points, we gate on an
    # asyncio.Barrier(2) inside Request.json() so both requests are forced to
    # actually be "in flight" past their JSON-parsing await point at the same
    # time -- the exact interleaving a TOCTOU race depends on -- before either
    # is allowed to proceed to the job_already_running check.
    from aiohttp.web_request import Request

    role = FakeRole(7, name="VIP", position=5)
    members = [FakeMember(100 + i, name=f"user{i}") for i in range(20)]
    client = await aiohttp_client(build(members=members, roles=[role]))
    await force_login(client, 10)

    orig_json = Request.json
    barrier = asyncio.Barrier(2)

    async def gated_json(self, *args, **kwargs):
        result = await orig_json(self, *args, **kwargs)
        try:
            await asyncio.wait_for(barrier.wait(), timeout=5)
        except Exception:
            pass
        return result

    monkeypatch.setattr(Request, "json", gated_json)

    resp1, resp2 = await asyncio.gather(
        client.post("/api/roles/7/mass-assign", json={"target": "all"}),
        client.post("/api/roles/7/mass-assign", json={"target": "all"}),
    )

    statuses = sorted([resp1.status, resp2.status])
    assert statuses == [202, 409], (
        f"expected exactly one 202 and one 409, got {resp1.status} and {resp2.status}"
    )


@pytest.mark.asyncio
async def test_mass_assign_job_marked_failed_on_unexpected_exception(aiohttp_client, monkeypatch):
    # Regression test: if run_mass_assign raises something other than
    # discord.HTTPException, the fire-and-forget task must not die silently
    # leaving the job wedged at "running" forever.
    role = FakeRole(7, name="VIP", position=5)
    present = FakeMember(60, name="present")
    client = await aiohttp_client(build(members=[present], roles=[role]))
    await force_login(client, 10)

    async def broken_run_mass_assign(job_id, guild, role, members, moderator, dashboard_reason):
        raise RuntimeError("boom")

    monkeypatch.setattr(mass_role_jobs, "run_mass_assign", broken_run_mass_assign)

    resp = await client.post("/api/roles/7/mass-assign", json={"target": "selected", "member_ids": ["60"]})
    assert resp.status == 202
    job_id = (await resp.json())["job_id"]

    body = await _wait_for_completion(client, job_id)
    assert body["status"] == "failed"
