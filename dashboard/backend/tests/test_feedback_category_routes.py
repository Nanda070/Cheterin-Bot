import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
    force_login,
    make_moderation_app,
)

import feedback_categories


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))


def _spec(key="players", case_prefix="PR", channel_id="500", role_id="111"):
    return {
        "key": key,
        "title": "Жалоба на участника",
        "button_label": "Жалоба на участника",
        "channel_id": channel_id,
        "case_prefix": case_prefix,
        "case_title": "Жалоба на участника",
        "thread_name": "player-report",
        "review_role_ids": [role_id],
        "approved_text": "Участник наказан.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на участника",
        "fields": [
            {"key": "offender", "label": "Ник участника", "style": "short", "required": True, "max_length": 120},
        ],
        "mini_summary_key": "offender",
    }


def build(roles=None, channels=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator], roles=roles or [], channels=channels or [])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_list_feedback_categories_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-categories")
    assert resp.status == 200
    assert (await resp.json()) == {"categories": []}


@pytest.mark.asyncio
async def test_create_feedback_category_success(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 201
    body = await resp.json()
    assert body["key"] == "players"
    assert body["case_prefix"] == "PR"
    assert feedback_categories.load_categories()["players"]["channel_id"] == "500"


@pytest.mark.asyncio
async def test_create_feedback_category_rejects_invalid_key(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec(key="Bad Key"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_key"


@pytest.mark.asyncio
async def test_create_feedback_category_rejects_duplicate_key(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 409
    assert (await resp.json())["error"] == "key_taken"


@pytest.mark.asyncio
async def test_create_feedback_category_checks_structure_before_channel_existence(aiohttp_client):
    # Invalid key AND a channel that doesn't exist -- must get the structural
    # 400, not a 404, proving structural checks run first.
    _, app = build(channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec(key="Bad Key"))
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_key"


@pytest.mark.asyncio
async def test_create_feedback_category_404_when_channel_missing(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    _, app = build(roles=[role], channels=[])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "channel_not_found"


@pytest.mark.asyncio
async def test_create_feedback_category_404_when_role_missing(aiohttp_client):
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-categories", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "role_not_found"


@pytest.mark.asyncio
async def test_list_feedback_categories_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-categories")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_update_feedback_category_success(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    updated = _spec()
    updated["title"] = "Обновлённая жалоба"

    resp = await client.put("/api/feedback-categories/players", json=updated)
    assert resp.status == 200
    body = await resp.json()
    assert body["title"] == "Обновлённая жалоба"
    assert feedback_categories.load_categories()["players"]["title"] == "Обновлённая жалоба"


@pytest.mark.asyncio
async def test_update_feedback_category_404_when_unknown(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.put("/api/feedback-categories/missing", json=_spec())
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_update_feedback_category_keeps_own_case_prefix(aiohttp_client):
    # Editing a category and re-submitting its own unchanged case_prefix must
    # NOT be rejected as a duplicate against itself.
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.put("/api/feedback-categories/players", json=_spec())
    assert resp.status == 200


@pytest.mark.asyncio
async def test_delete_feedback_category_removes_it(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")
    assert resp.status == 200
    assert feedback_categories.load_categories() == {}


@pytest.mark.asyncio
async def test_delete_feedback_category_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/feedback-categories/missing")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_delete_feedback_category_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.delete("/api/feedback-categories/players")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_delete_feedback_category_removes_pending_cases(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    bot = app["bot"]
    bot.feedback_cases["PR-0001"] = {"case_id": "PR-0001", "category_key": "players", "status": "pending"}
    bot.feedback_cases["PR-0002"] = {"case_id": "PR-0002", "category_key": "players", "status": "approved"}
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")

    assert resp.status == 200
    assert "PR-0001" not in bot.feedback_cases
    assert "PR-0002" in bot.feedback_cases
    assert bot.update_file_calls == 1


@pytest.mark.asyncio
async def test_delete_feedback_category_no_update_file_call_when_no_pending_cases(aiohttp_client):
    role = FakeRole(111, name="Reviewers")
    channel = FakeChannel(500, name="reports")
    _, app = build(roles=[role], channels=[channel])
    bot = app["bot"]
    client = await aiohttp_client(app)
    await force_login(client, 10)

    await client.post("/api/feedback-categories", json=_spec())
    resp = await client.delete("/api/feedback-categories/players")

    assert resp.status == 200
    assert bot.update_file_calls == 0
