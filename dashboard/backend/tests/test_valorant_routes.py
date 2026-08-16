import pytest

import settings_db
from dashboard.backend.routes.valorant import routes as valorant_routes
from dashboard.backend.tests.fakes import FakeBot, FakeGuild, FakeMember, force_login, make_moderation_app


@pytest.fixture(autouse=True)
def isolated_settings_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "test_settings.db"))
    settings_db._cache.clear()
    settings_db.init()


@pytest.mark.asyncio
async def test_panels_settings_are_loaded_for_active_guild(aiohttp_client):
    main_guild = FakeGuild(members=[FakeMember(10, name="mod", role_ids=[111])], guild_id=1)
    selected_guild = FakeGuild(members=[FakeMember(10, name="mod", role_ids=[111])], guild_id=2)
    settings_db.put(2, "valorant_panels", {"enabled": True, "button_label": "Join"})
    app = make_moderation_app(FakeBot(main_guild, guilds=[main_guild, selected_guild]), [valorant_routes])
    client = await aiohttp_client(app)
    await force_login(client, 10, active_guild_id=2)

    response = await client.get("/api/valorant/panels")

    assert response.status == 200
    body = await response.json()
    assert body["settings"]["enabled"] is True
    assert body["settings"]["button_label"] == "Join"
    assert body["catalog"]["servers"]
