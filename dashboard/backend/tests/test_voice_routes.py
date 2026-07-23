import pytest

import voice_db
from dashboard.backend.routes.voice import routes as voice_routes
from dashboard.backend.tests.fakes import (
    FakeBot,
    FakeGuild,
    FakeMember,
    force_login,
    make_moderation_app,
)


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_DB_PATH", str(tmp_path / "private_rooms.db"))
    voice_db.user_owned_channels.clear()
    voice_db.db_init()
    yield
    voice_db.user_owned_channels.clear()


class FakeVoiceChannel:
    def __init__(self, channel_id, name="voice", members=None):
        self.id = channel_id
        self.name = name
        self.members = members or []
        self.deleted = False
        self.delete_raises = None

    async def delete(self, reason=None):
        if self.delete_raises:
            raise self.delete_raises
        self.deleted = True


@pytest.fixture(autouse=True)
def voice_channel_isinstance(monkeypatch):
    """Роуты проверяют isinstance(channel, discord.VoiceChannel) — подменяем на утиную проверку."""
    import dashboard.backend.routes.voice as voice_module

    class _FakeDiscord:
        VoiceChannel = FakeVoiceChannel
        HTTPException = voice_module.discord.HTTPException

    monkeypatch.setattr(voice_module, "discord", _FakeDiscord)


def build(channels=None, members=None):
    moderator = FakeMember(10, name="mod", role_ids=[111])
    bot = FakeBot(FakeGuild(members=[moderator] + (members or []), channels=channels or []))
    return bot, make_moderation_app(bot, [voice_routes])


@pytest.mark.asyncio
async def test_rooms_empty(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/voice/rooms")
    assert resp.status == 200
    assert await resp.json() == {"rooms": []}


@pytest.mark.asyncio
async def test_rooms_list(aiohttp_client):
    owner = FakeMember(20, name="owner", display_name="Owner")
    channel = FakeVoiceChannel(700, name="Комната • Owner", members=[owner])
    _, app = build(channels=[channel], members=[owner])

    voice_db.db_upsert_room(1, 700, 20, "Комната • Owner", is_closed=False, user_limit=5)
    voice_db.db_upsert_room(1, 701, 999, "Битая комната", is_closed=True, user_limit=0)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/voice/rooms")
    body = await resp.json()
    rooms = {r["channel_id"]: r for r in body["rooms"]}
    assert rooms["700"]["owner_display"] == "Owner"
    assert rooms["700"]["member_count"] == 1
    assert rooms["700"]["exists"] is True
    assert rooms["700"]["user_limit"] == 5
    assert rooms["701"]["exists"] is False
    assert rooms["701"]["is_closed"] is True
    assert rooms["701"]["owner_display"] == "999"


@pytest.mark.asyncio
async def test_rooms_list_filters_by_active_guild(aiohttp_client):
    owner = FakeMember(20, name="owner", display_name="Owner")
    channel = FakeVoiceChannel(700, name="Комната • Owner", members=[owner])
    _, app = build(channels=[channel], members=[owner])

    voice_db.db_upsert_room(1, 700, 20, "Комната • Owner", is_closed=False, user_limit=5)
    # Room from another guild must not appear for the active dashboard guild.
    voice_db.db_upsert_room(999, 800, 20, "Чужая комната", is_closed=False, user_limit=0)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.get("/api/voice/rooms")
    body = await resp.json()
    assert [r["channel_id"] for r in body["rooms"]] == ["700"]


@pytest.mark.asyncio
async def test_delete_room_rejects_other_guild(aiohttp_client):
    _, app = build()
    voice_db.db_upsert_room(999, 800, 20, "Чужая комната", is_closed=False, user_limit=0)

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/voice/rooms/800")
    assert resp.status == 404
    assert voice_db.db_get_room(800) is not None


@pytest.mark.asyncio
async def test_delete_room(aiohttp_client):
    owner = FakeMember(20, name="owner")
    channel = FakeVoiceChannel(700, members=[owner])
    _, app = build(channels=[channel], members=[owner])

    voice_db.db_upsert_room(1, 700, 20, "room", is_closed=False, user_limit=0)
    voice_db.user_owned_channels[20] = 700

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/voice/rooms/700")
    assert resp.status == 200
    assert channel.deleted is True
    assert voice_db.db_get_room(700) is None
    assert 20 not in voice_db.user_owned_channels


@pytest.mark.asyncio
async def test_delete_room_not_found(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.delete("/api/voice/rooms/12345")
    assert resp.status == 404


@pytest.mark.asyncio
async def test_panel_publish(aiohttp_client):
    class FakePanelCog:
        async def publish_panel(self, guild_id: int):
            self.guild_id = guild_id
            return 42

    bot, app = build()
    cog = FakePanelCog()
    bot.get_cog = lambda name: cog if name == "PanelManager" else None

    client = await aiohttp_client(app)
    await force_login(client, 10)

    resp = await client.post("/api/voice/panel/publish")
    assert resp.status == 200
    assert await resp.json() == {"ok": True, "message_id": "42"}
    assert cog.guild_id == 1


@pytest.mark.asyncio
async def test_requires_auth(aiohttp_client):
    _, app = build()
    client = await aiohttp_client(app)
    resp = await client.get("/api/voice/rooms")
    assert resp.status == 401
