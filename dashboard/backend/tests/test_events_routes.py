import pytest

from dashboard.backend.routes.events import routes as events_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)

import bot.modules.community.events as events


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def _tournament_event(status="open", mode="solo", participants=None, **overrides):
    ev = {
        "type": "tournament",
        "channel_id": 500,
        "author_id": 1,
        "title": "Test Tournament",
        "description": "desc",
        "banner_url": "",
        "mode": mode,
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "status": status,
        "participants": participants or [],
        "options": [],
        "multi_select": False,
        "votes": {},
    }
    ev.update(overrides)
    return ev


def _poll_event(status="open", options=None, votes=None, multi_select=False):
    return {
        "type": "poll",
        "channel_id": 500,
        "author_id": 1,
        "title": "Test Poll",
        "description": "desc",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "status": status,
        "participants": [],
        "options": options or ["A", "B"],
        "multi_select": multi_select,
        "votes": votes or {},
    }


def build(channels=None, roles=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], channels=channels or [], roles=roles or [])
    return guild, make_moderation_app(FakeBot(guild), [events_routes])


def _tournament_create_spec(channel_id="500", **overrides):
    spec = {
        "channel_id": channel_id,
        "type": "tournament",
        "title": "Летний турнир",
        "description": "Описание",
        "banner_url": "",
        "ping": "none",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "options": [],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


def _poll_create_spec(channel_id="500", **overrides):
    spec = {
        "channel_id": channel_id,
        "type": "poll",
        "title": "Опрос дня",
        "description": "Описание",
        "banner_url": "",
        "ping": "none",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "options": ["Да", "Нет"],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


@pytest.mark.asyncio
async def test_list_events_defaults_to_open(aiohttp_client):
    events.save_events(1, 
        {"events": {"900": _tournament_event(status="open"), "901": _tournament_event(status="closed")}}
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events")
    assert resp.status == 200
    body = await resp.json()
    assert [e["message_id"] for e in body["events"]] == ["900"]


@pytest.mark.asyncio
async def test_list_events_filters_by_closed(aiohttp_client):
    events.save_events(1, 
        {"events": {"900": _tournament_event(status="open"), "901": _tournament_event(status="closed")}}
    )
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events?status=closed")
    assert resp.status == 200
    body = await resp.json()
    assert [e["message_id"] for e in body["events"]] == ["901"]


@pytest.mark.asyncio
async def test_list_events_rejects_invalid_status(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events?status=bogus")
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_status"


@pytest.mark.asyncio
async def test_list_events_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/events")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_get_event_detail_tournament_solo_shape(aiohttp_client):
    ev = _tournament_event(mode="solo", participants=[{"user_id": 20, "ign": "PlayerOne"}])
    events.save_events(1, {"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    assert resp.status == 200
    body = await resp.json()
    assert body["mode"] == "solo"
    assert body["participants"] == [{"user_id": "20", "ign": "PlayerOne"}]


@pytest.mark.asyncio
async def test_get_event_detail_tournament_team_code_groups_by_team(aiohttp_client):
    participants = [
        {"user_id": 1, "team_code": "ABC123", "team_name": "Alpha", "ign": "cap", "is_captain": True},
        {"user_id": 2, "team_code": "ABC123", "team_name": "Alpha", "ign": "mate", "is_captain": False},
    ]
    ev = _tournament_event(mode="team_code", participants=participants)
    events.save_events(1, {"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    body = await resp.json()
    assert len(body["participants"]) == 1
    team = body["participants"][0]
    assert team["team_code"] == "ABC123"
    assert team["team_name"] == "Alpha"
    assert len(team["members"]) == 2


@pytest.mark.asyncio
async def test_get_event_detail_poll_shape_with_percentages(aiohttp_client):
    ev = _poll_event(options=["Yes", "No"], votes={"1": [0], "2": [0], "3": [1]})
    events.save_events(1, {"events": {"900": ev}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/900")
    body = await resp.json()
    assert body["options"] == [
        {"label": "Yes", "votes": 2, "percent": 66},
        {"label": "No", "votes": 1, "percent": 33},
    ]


@pytest.mark.asyncio
async def test_get_event_detail_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/events/missing")
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_get_event_detail_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/events/900")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_close_event_route_success(aiohttp_client):
    events.save_events(1, {"events": {"900": _tournament_event()}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/close")
    assert resp.status == 200
    assert (await resp.json()) == {"ok": True}
    data = events.load_events(1)
    assert data["events"]["900"]["status"] == "closed"


@pytest.mark.asyncio
async def test_close_event_route_404(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/missing/close")
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_close_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events/900/close")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_delete_event_route_success(aiohttp_client):
    events.save_events(1, {"events": {"900": _tournament_event()}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/events/900")
    assert resp.status == 200
    data = events.load_events(1)
    assert "900" not in data["events"]


@pytest.mark.asyncio
async def test_delete_event_route_404(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/events/missing")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.delete("/api/events/900")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_notify_event_route_success(aiohttp_client):
    ev = _tournament_event(participants=[{"user_id": 20, "ign": "a"}])
    events.save_events(1, {"events": {"900": ev}})
    member = FakeMember(20, name="p1")
    guild = FakeGuild(members=[FakeMember(10, name="mod", role_ids=[111]), member])
    app = make_moderation_app(FakeBot(guild), [events_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={"message": "Hello"})
    assert resp.status == 200
    body = await resp.json()
    assert body == {"ok": True, "success": 1, "failed": 0}


@pytest.mark.asyncio
async def test_notify_event_route_rejects_missing_message(aiohttp_client):
    events.save_events(1, {"events": {"900": _tournament_event(participants=[{"user_id": 20}])}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_notify_event_route_400_when_no_participants(aiohttp_client):
    events.save_events(1, {"events": {"900": _tournament_event(participants=[])}})
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events/900/notify", json={"message": "Hello"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "no_participants"


@pytest.mark.asyncio
async def test_notify_event_route_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events/900/notify", json={"message": "hi"})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_event_tournament_success(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["type"] == "tournament"
    assert body["title"] == "Летний турнир"
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_create_event_poll_success(aiohttp_client):
    channel = FakeChannel(500, name="polls")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_poll_create_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["type"] == "poll"
    assert body["options"] == [
        {"label": "Да", "votes": 0, "percent": 0},
        {"label": "Нет", "votes": 0, "percent": 0},
    ]


@pytest.mark.asyncio
async def test_create_event_checks_structure_before_channel_existence(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(title=""))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_title"


@pytest.mark.asyncio
async def test_create_event_404_when_channel_missing(aiohttp_client):
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_event_404_when_role_reward_missing(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(role_reward="999"))
    assert resp.status == 404
    assert (await resp.json())["error"] == "role_not_found"


@pytest.mark.asyncio
async def test_create_event_rejects_non_numeric_role_reward(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/events", json=_tournament_create_spec(role_reward="not-a-number"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_create_event_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/events", json=_tournament_create_spec())
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_event_round_trips_via_get_detail(aiohttp_client):
    channel = FakeChannel(500, name="tourneys")
    _, app = build(channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    create_resp = await client.post("/api/events", json=_tournament_create_spec())
    message_id = (await create_resp.json())["message_id"]

    get_resp = await client.get(f"/api/events/{message_id}")
    assert get_resp.status == 200
    assert (await get_resp.json())["title"] == "Летний турнир"
