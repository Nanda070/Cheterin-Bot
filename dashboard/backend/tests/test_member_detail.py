import pytest

import settings_db
from dashboard.backend.routes.moderation import routes as moderation_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)


def build(members, stats=None, cases=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator] + members))
    settings_db.put(1, "invites_stats", {"stats": stats or {}})
    settings_db.put(1, "feedback_cases", cases or {})
    return make_moderation_app(bot, [moderation_routes])


@pytest.mark.asyncio
async def test_detail_shape_matches_userinfo(aiohttp_client):
    target = FakeMember(
        50,
        name="target",
        roles=[FakeRole(7, name="VIP", position=3, color_value=0x5865F2)],
    )
    stats = {"50": {"joins": 2, "leaves": 1, "invites": 4}}
    cases = {"c1": {"submitter_id": 50}, "c2": {"submitter_id": 999}}
    client = await aiohttp_client(build([target], stats, cases))
    await force_login(client, 10)

    resp = await client.get("/api/members/50")
    assert resp.status == 200
    body = await resp.json()
    assert body["id"] == "50"
    assert body["created_at"].startswith("2020-06-01")
    assert body["roles"] == [{"id": "7", "name": "VIP", "color": "#5865f2"}]
    assert body["invite_stats"] == {"joins": 2, "leaves": 1, "invites": 4}
    assert body["feedback_case_count"] == 1
    assert body["is_bot"] is False


@pytest.mark.asyncio
async def test_detail_defaults_when_no_stats(aiohttp_client):
    target = FakeMember(51, name="fresh")
    client = await aiohttp_client(build([target]))
    await force_login(client, 10)

    resp = await client.get("/api/members/51")
    body = await resp.json()
    assert body["invite_stats"] == {"joins": 0, "leaves": 0, "invites": 0}
    assert body["feedback_case_count"] == 0


@pytest.mark.asyncio
async def test_detail_404_when_member_absent(aiohttp_client):
    client = await aiohttp_client(build([]))
    await force_login(client, 10)
    resp = await client.get("/api/members/404404")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_detail_400_on_non_numeric_id(aiohttp_client):
    client = await aiohttp_client(build([]))
    await force_login(client, 10)
    resp = await client.get("/api/members/abc")
    assert resp.status == 400
