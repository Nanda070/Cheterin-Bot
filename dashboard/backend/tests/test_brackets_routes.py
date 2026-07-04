import pytest

import brackets
import events
from dashboard.backend.routes.brackets import routes as brackets_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_files(tmp_path, monkeypatch):
    monkeypatch.setattr(brackets, "BRACKETS_FILE", str(tmp_path / "brackets_data.json"))
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def build():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator])
    return make_moderation_app(FakeBot(guild), [brackets_routes])


def _tournament_event(mode="solo", participants=None, **overrides):
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
        "status": "open",
        "participants": participants or [],
        "options": [],
        "multi_select": False,
        "votes": {},
    }
    ev.update(overrides)
    return ev


@pytest.mark.asyncio
async def test_list_brackets_returns_summaries(aiohttp_client):
    data = {"b1": brackets.create_bracket("T1", ["A", "B"], None, 10)}
    brackets.save_brackets(data)
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets")
    assert resp.status == 200
    body = await resp.json()
    assert body["brackets"][0]["title"] == "T1"
    assert body["brackets"][0]["entry_count"] == 2


@pytest.mark.asyncio
async def test_list_brackets_requires_auth(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/brackets")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_create_bracket_manual(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "Manual", "entries": ["X", "Y", "Z"]}
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["title"] == "Manual"
    assert body["entries"] == ["X", "Y", "Z"]
    assert len(body["rounds"]) == 2

    stored = brackets.load_brackets()
    assert len(stored) == 1


@pytest.mark.asyncio
async def test_create_bracket_rejects_fewer_than_two_entries(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets", json={"title": "Manual", "entries": ["X"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "not_enough_entries"


@pytest.mark.asyncio
async def test_create_bracket_rejects_blank_title(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets", json={"title": "  ", "entries": ["X", "Y"]})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_create_bracket_from_event(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="solo", participants=[{"user_id": 1, "ign": "A"}, {"user_id": 2, "ign": "B"}]
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "From Event", "source_event_id": "900", "entries": ["B", "A"]}
    )
    assert resp.status == 201
    body = await resp.json()
    assert body["source_event_id"] == "900"
    assert body["entries"] == ["B", "A"]


@pytest.mark.asyncio
async def test_create_bracket_from_event_rejects_tampered_entries(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="solo", participants=[{"user_id": 1, "ign": "A"}, {"user_id": 2, "ign": "B"}]
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets",
        json={"title": "From Event", "source_event_id": "900", "entries": ["A", "Hacker"]},
    )
    assert resp.status == 400
    assert (await resp.json())["error"] == "entries_mismatch"


@pytest.mark.asyncio
async def test_create_bracket_from_missing_event_404s(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post(
        "/api/brackets", json={"title": "From Event", "source_event_id": "999", "entries": ["A", "B"]}
    )
    assert resp.status == 404
    assert (await resp.json())["error"] == "event_not_found"


@pytest.mark.asyncio
async def test_get_bracket_detail(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get(f"/api/brackets/{bracket['id']}")
    assert resp.status == 200
    assert (await resp.json())["title"] == "T1"


@pytest.mark.asyncio
async def test_get_bracket_detail_404_when_missing(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets/does-not-exist")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_bracket(aiohttp_client):
    bracket = brackets.create_bracket("T1", ["A", "B"], None, 10)
    brackets.save_brackets({bracket["id"]: bracket})
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete(f"/api/brackets/{bracket['id']}")
    assert resp.status == 200
    assert brackets.load_brackets() == {}


@pytest.mark.asyncio
async def test_entries_from_event_preview(aiohttp_client):
    await events.save_events(
        {
            "events": {
                "900": _tournament_event(
                    mode="team_captain",
                    participants=[
                        {"user_id": 1, "team_name": "Alpha", "members": ""},
                        {"user_id": 2, "team_name": "Beta", "members": ""},
                    ],
                )
            }
        }
    )
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/brackets/entries-from-event/900")
    assert resp.status == 200
    assert (await resp.json())["entries"] == ["Alpha", "Beta"]


@pytest.mark.asyncio
async def test_create_bracket_rejects_non_dict_json_body(aiohttp_client):
    app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/brackets", data="[]", headers={"Content-Type": "application/json"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"
