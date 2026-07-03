import pytest

from dashboard.backend.routes.feedback import routes as feedback_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_feedback_categories(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    import feedback_menu

    monkeypatch.setattr(feedback_menu, "_feedback_categories_cache", None)
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
    app_bot.feedback_cases["PR-0001"] = _case(status="pending")
    app_bot.feedback_cases["PR-0002"] = _case(status="approved", created_at="2026-07-02T00:00:00+00:00")

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
    app["bot"].feedback_cases["PR-0001"] = _case(status="pending")
    app["bot"].feedback_cases["PR-0002"] = _case(status="approved")

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
    app["bot"].feedback_cases["PR-0001"] = _case(submitter_id=50)

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
    app["bot"].feedback_cases["PR-0001"] = _case()

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
