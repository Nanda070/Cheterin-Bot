import pytest

import discord

import bot.modules.feedback.feedback_core as feedback_core
from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, FakeChannel, FakeMessage, FakeThread, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_feedback_categories(tmp_path, monkeypatch):
    import bot.core.feedback_categories as feedback_categories
    import bot.core.settings_db as settings_db

    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setenv("GUILD_ID", "1")
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()
    feedback_categories.save_categories(1, {
            "players": {
                "title": "Жалоба на участника",
                "button_label": "Жалоба на участника",
                "channel_id": "500",
                "case_prefix": "PR",
                "case_title": "Жалоба на участника",
                "thread_name": "player-report",
                "review_role_ids": ["111"],
                "review_user_ids": [],
                "approved_text": "Участник наказан.",
                "denied_text": "Жалоба отклонена.",
                "modal_title": "Жалоба на участника",
                "fields": [
                    {
                        "key": "offender",
                        "label": "Ник / ID участника",
                        "style": "short",
                        "required": True,
                        "max_length": 120,
                    },
                    {
                        "key": "complaint",
                        "label": "Суть жалобы",
                        "style": "paragraph",
                        "required": True,
                        "max_length": 1000,
                    },
                    {
                        "key": "datetime",
                        "label": "Дата и время ситуации",
                        "style": "short",
                        "required": False,
                        "max_length": 120,
                    },
                    {
                        "key": "proof",
                        "label": "Доказательства",
                        "style": "paragraph",
                        "required": False,
                        "max_length": 1000,
                    },
                ],
                "mini_summary_key": "offender",
            },
        }
    )
    yield


def _case(status="pending", submitter_id=50, created_at="2026-07-03T00:00:00+00:00"):
    return {
        "case_id": "PR-0001",
        "category_key": "players",
        "submitter_id": submitter_id,
        "public_channel_id": 500,
        "public_message_id": 900,
        "thread_id": 700,
        "decision_message_id": 901,
        "status": status,
        "created_at": created_at,
        "answers": {"offender": "SomePlayer", "complaint": "Grief"},
    }


def build(members=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    submitter = FakeMember(50, name="submitter")
    guild = FakeGuild(members=[moderator, submitter] + (members or []))
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_list_feedback_cases_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases")
    assert resp.status == 200
    assert (await resp.json()) == {"cases": []}


@pytest.mark.asyncio
async def test_list_feedback_cases_returns_all_by_default(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    app_bot = app["bot"]
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0002"] = _case(status="approved", created_at="2026-07-02T00:00:00+00:00")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.get("/api/feedback-cases")
    assert resp.status == 200
    body = await resp.json()
    assert len(body["cases"]) == 2
    # newest first
    assert body["cases"][0]["case_id"] == "PR-0001"


@pytest.mark.asyncio
async def test_list_feedback_cases_filters_by_status(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0002"] = _case(status="approved")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.get("/api/feedback-cases?status=pending")
    assert resp.status == 200
    body = await resp.json()
    assert [c["case_id"] for c in body["cases"]] == ["PR-0001"]


@pytest.mark.asyncio
async def test_list_feedback_cases_rejects_invalid_status(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases?status=bogus")
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_status"


@pytest.mark.asyncio
async def test_list_feedback_cases_resolves_submitter_display_name(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(submitter_id=50)
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.get("/api/feedback-cases")
    body = await resp.json()
    assert body["cases"][0]["submitter_display"] == "submitter"


@pytest.mark.asyncio
async def test_list_feedback_cases_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-cases")
    assert resp.status == 401


@pytest.mark.asyncio
async def test_get_feedback_case_returns_full_detail_with_answers(aiohttp_client):
    guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case()
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.get("/api/feedback-cases/PR-0001")
    assert resp.status == 200
    body = await resp.json()
    assert body["case_id"] == "PR-0001"
    assert body["status"] == "pending"
    field_by_key = {f["key"]: f["value"] for f in body["fields"]}
    assert field_by_key["offender"] == "SomePlayer"
    assert field_by_key["complaint"] == "Grief"
    assert field_by_key["datetime"] == "—"  # not submitted, config field exists


@pytest.mark.asyncio
async def test_get_feedback_case_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/feedback-cases/MISSING")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_get_feedback_case_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/feedback-cases/PR-0001")
    assert resp.status == 401


def build_with_channels():
    moderator = FakeMember(10, name="mod", role_ids=[111])
    submitter = FakeMember(50, name="submitter")
    public_message = FakeMessage(900, embeds=[discord.Embed(title="Case")])
    channel = FakeChannel(500, messages={900: public_message})
    decision_message = FakeMessage(901, embeds=[discord.Embed(title="Case")])
    thread = FakeThread(700, messages={901: decision_message})
    guild = FakeGuild(members=[moderator, submitter], channels=[channel], threads=[thread])
    return guild, make_moderation_app(FakeBot(guild), [feedback_routes])


@pytest.mark.asyncio
async def test_decide_feedback_case_approves_and_persists(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 200
    assert (await resp.json()) == {"ok": True}
    assert settings_db.get(1, "feedback_cases", {})["PR-0001"]["status"] == "approved"
    assert settings_db.get(1, "feedback_cases", {})["PR-0001"]["reviewed_by"] == 10


@pytest.mark.asyncio
async def test_decide_feedback_case_404_when_unknown(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/feedback-cases/MISSING/decide", json={"approved": True})
    assert resp.status == 404
    assert (await resp.json())["error"] == "not_found"


@pytest.mark.asyncio
async def test_decide_feedback_case_409_when_already_decided(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="approved")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 409
    assert (await resp.json())["error"] == "already_decided"


@pytest.mark.asyncio
async def test_decide_feedback_case_409_when_category_deleted(aiohttp_client):
    import bot.core.feedback_categories as feedback_categories

    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)

    # Category "players" is deleted from the categories config after the case was created.
    feedback_categories.save_categories(1, {})

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 409
    assert (await resp.json()) == {"error": "category_deleted"}


@pytest.mark.asyncio
async def test_decide_feedback_case_rejects_non_boolean_approved(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": "yes"})
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_decide_feedback_case_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 401


@pytest.mark.asyncio
async def test_decide_feedback_case_rejects_non_dict_body(aiohttp_client):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json=[1, 2, 3])
    assert resp.status == 400
    assert (await resp.json())["error"] == "invalid_request"


@pytest.mark.asyncio
async def test_decide_feedback_case_unknown_error_maps_to_400(aiohttp_client, monkeypatch):
    guild, app = build_with_channels()
    client = await aiohttp_client(app)
    await force_login(client, 10)
    import bot.core.settings_db as settings_db
    cases = settings_db.get(1, "feedback_cases", {})
    cases["PR-0001"] = _case(status="pending")
    settings_db.put(1, "feedback_cases", cases)

    async def fake_decide_case(*args, **kwargs):
        return {"ok": False, "error": "some_future_error"}

    monkeypatch.setattr(feedback_core, "decide_case", fake_decide_case)

    resp = await client.post("/api/feedback-cases/PR-0001/decide", json={"approved": True})
    assert resp.status == 400
