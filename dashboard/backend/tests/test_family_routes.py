import pytest

import family_core
import family_db
import settings_db
from family_tickets import FamilyTicketsCog
from dashboard.backend.routes.family import routes as family_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeChannel,
    FakeGuild,
    FakeMember,
    FakeRole,
    FakeThread,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setenv("FAMILY_DB_PATH", str(tmp_path / "family.db"))
    family_db.init()
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def build(members=None, **guild_kwargs):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    guild = FakeGuild(members=[moderator] + (members or []), **guild_kwargs)
    bot = FakeBot(guild)
    return bot, guild, make_moderation_app(bot, [family_routes])


# ────────────────────────── Настройки ──────────────────────────

@pytest.mark.asyncio
async def test_get_defaults(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/family")
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is False
    assert body["roster"]["target_roles"] == []


@pytest.mark.asyncio
async def test_put_then_get(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = family_core.get_settings(1)
    payload["enabled"] = True
    payload["roster"]["target_roles"] = [{"label": "High", "role_id": "7"}]
    payload["applications"]["staff_role_ids"] = ["1", "2"]

    resp = await client.put("/api/family", json=payload)
    assert resp.status == 200
    body = await resp.json()
    assert body["enabled"] is True
    assert body["roster"]["target_roles"] == [{"label": "High", "role_id": "7"}]

    resp = await client.get("/api/family")
    assert (await resp.json())["applications"]["staff_role_ids"] == ["1", "2"]


@pytest.mark.asyncio
async def test_put_validation(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    payload = family_core.get_settings(1)
    payload["enabled"] = "yes"
    resp = await client.put("/api/family", json=payload)
    assert resp.status == 400

    payload = family_core.get_settings(1)
    payload["applications"]["thread_archive_minutes"] = 5
    resp = await client.put("/api/family", json=payload)
    assert resp.status == 400

    payload = family_core.get_settings(1)
    payload["roster"]["target_roles"] = [{"label": "X", "role_id": "abc"}]
    resp = await client.put("/api/family", json=payload)
    assert resp.status == 400


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/family")
    assert resp.status == 401


# ────────────────────────── Ростер ──────────────────────────

@pytest.mark.asyncio
async def test_roster_preview(aiohttp_client):
    role = FakeRole(7, name="High")
    member = FakeMember(20, name="member", display_name="Member")
    role.members = [member]
    _, _, app = build(roles=[role])

    family_core.save_config(1, {"roster": {"target_roles": [{"label": "Верхушка", "role_id": "7"}]}})

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/family/roster")
    body = await resp.json()
    assert body["groups"][0]["label"] == "Верхушка"
    assert body["groups"][0]["role_found"] is True
    assert body["groups"][0]["members"] == [{"id": "20", "display": "Member"}]


@pytest.mark.asyncio
async def test_roster_preview_missing_role(aiohttp_client):
    _, _, app = build()
    family_core.save_config(1, {"roster": {"target_roles": [{"label": "Ghost", "role_id": "999"}]}})

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/family/roster")
    body = await resp.json()
    assert body["groups"][0]["role_found"] is False
    assert body["groups"][0]["members"] == []


# ────────────────────────── Заявки ──────────────────────────

def _ticket_data(nickname="Nick"):
    return {
        "nickname": nickname, "game_level": "99", "faction_pref": "Gov", "online_timezone": "MSK",
        "real_name": "Ivan", "real_age": "20", "about_text": "about", "why_join": "why",
        "inviter_nickname": None,
    }


@pytest.mark.asyncio
async def test_tickets_list_and_filter(aiohttp_client):
    _, _, app = build()
    family_db.create_ticket_record(20, 1, _ticket_data("Open1"))
    family_db.create_ticket_record(21, 1, _ticket_data("Closed1"))
    family_db.update_ticket_status(1, 21, "closed", handled_by=10)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/family/tickets?status=open")
    body = await resp.json()
    assert body["total"] == 1
    assert body["entries"][0]["nickname"] == "Open1"

    resp = await client.get("/api/family/tickets")
    assert (await resp.json())["total"] == 2

    resp = await client.get("/api/family/tickets?status=bogus")
    assert resp.status == 400


@pytest.mark.asyncio
async def test_ticket_approve_full_flow(aiohttp_client):
    approve_role = FakeRole(50, name="FamilyMember")
    active_role = FakeRole(60, name="Pending")
    app_channel = FakeChannel(700, name="applications")
    applicant = FakeMember(20, name="applicant", display_name="Applicant", roles=[active_role])
    thread = FakeThread(800, name="family-applicant")

    _, guild, app = build(channels=[app_channel], roles=[approve_role, active_role], members=[applicant], threads=[thread])

    family_core.save_config(1, {
        "applications": {
            "application_channel_id": "700",
            "approve_role_ids": ["50"],
            "ticket_active_role_id": "60",
            "ticket_manager_role_id": "111",
        },
    })

    family_db.create_ticket_record(20, 1, _ticket_data())
    family_db.update_ticket_indexes(1, 20, mini_message_id=None, thread_id=800)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    # Wire a real FamilyTicketsCog onto the bot so resolve_ticket runs for real.
    bot_instance = client.app["bot"]
    cog = FamilyTicketsCog(bot_instance)
    bot_instance.get_cog = lambda name: cog if name == "FamilyTicketsCog" else None

    resp = await client.post("/api/family/tickets/20/approve")
    assert resp.status == 200
    assert (await resp.json()) == {"ok": True}

    # FakeMember.add_roles/remove_roles не мутируют .roles — проверяем через action_calls.
    add_calls = [c for c in applicant.action_calls if c[0] == "add_roles"]
    remove_calls = [c for c in applicant.action_calls if c[0] == "remove_roles"]
    assert any(c[1]["role"] is approve_role for c in add_calls)
    assert any(c[1]["role"] is active_role for c in remove_calls)
    assert thread.archived is True
    assert thread.locked is True

    ticket = family_db.get_ticket_by_user(1, 20)
    assert ticket["status"] == "approved"
    assert ticket["handled_by"] == 10


@pytest.mark.asyncio
async def test_ticket_decide_not_open_returns_404(aiohttp_client):
    bot, guild, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    bot_instance = client.app["bot"]
    cog = FamilyTicketsCog(bot_instance)
    bot_instance.get_cog = lambda name: cog if name == "FamilyTicketsCog" else None

    resp = await client.post("/api/family/tickets/999/approve")
    assert resp.status == 404


# ────────────────────────── Дни рождения ──────────────────────────

@pytest.mark.asyncio
async def test_birthdays_crud(aiohttp_client):
    member = FakeMember(20, name="bday", display_name="Bday")
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/family/birthdays", json={"user_id": "20", "date": "05.01"})
    assert resp.status == 200
    assert (await resp.json())["date_display"] == "05.01"

    resp = await client.get("/api/family/birthdays")
    entries = (await resp.json())["entries"]
    assert entries == [{"user_id": "20", "display": "Bday", "day": 5, "month": 1, "date_display": "05.01"}]

    resp = await client.delete("/api/family/birthdays/20")
    assert resp.status == 200
    resp = await client.get("/api/family/birthdays")
    assert (await resp.json())["entries"] == []

    resp = await client.delete("/api/family/birthdays/20")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_birthday_set_invalid_date(aiohttp_client):
    member = FakeMember(20, name="bday")
    _, _, app = build(members=[member])
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/family/birthdays", json={"user_id": "20", "date": "not-a-date"})
    assert resp.status == 400


@pytest.mark.asyncio
async def test_birthday_set_unknown_member(aiohttp_client):
    _, _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/family/birthdays", json={"user_id": "999", "date": "05.01"})
    assert resp.status == 404
