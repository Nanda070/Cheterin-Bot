from datetime import datetime, timezone

from aiohttp import web
from aiohttp_session import new_session

from dashboard.backend.config import DashboardConfig
from dashboard.backend.session import setup_session

TEST_CONFIG = DashboardConfig(
    port=8080,
    client_id="test-client-id",
    client_secret="test-client-secret",
    redirect_uri="http://localhost:8080/api/auth/discord/callback",
    session_secret="x" * 32,
    access_role_ids=frozenset({"111"}),
    frontend_url="",
)


class FakeColor:
    def __init__(self, value=0):
        self.value = value


class FakeRole:
    def __init__(self, role_id, name="role", position=1, color_value=0, managed=False, default=False):
        self.id = role_id
        self.name = name
        self.position = position
        self.color = FakeColor(color_value)
        self.managed = managed
        self._default = default
        self.mentionable = False
        self.permissions = FakePermissions()
        self.edit_calls = []
        self.edit_raises = None

    def is_default(self):
        return self._default

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)


class FakePermissions:
    def __init__(self, administrator=False, mention_everyone=False):
        self.administrator = administrator
        self.mention_everyone = mention_everyone


class FakeAsset:
    def __init__(self, url="https://cdn.example/avatar.png"):
        self.url = url

    def __str__(self):
        return self.url


class FakeCustomEmoji:
    def __init__(self, emoji_id, name):
        self.id = emoji_id
        self.name = name
        self.url = f"https://cdn.example/emojis/{emoji_id}.png"

    def __str__(self):
        return f"<:{self.name}:{self.id}>"


class FakeMessage:
    def __init__(self, message_id):
        self.id = message_id
        self.reaction_calls = []
        self.add_reaction_raises = None
        self.remove_reaction_raises = None

    async def add_reaction(self, emoji):
        if self.add_reaction_raises:
            raise self.add_reaction_raises
        self.reaction_calls.append(("add", str(emoji)))

    async def remove_reaction(self, emoji, member):
        if self.remove_reaction_raises:
            raise self.remove_reaction_raises
        self.reaction_calls.append(("remove", str(emoji)))


class FakeChannel:
    def __init__(self, channel_id, name="channel", messages=None):
        self.id = channel_id
        self.name = name
        self._messages = messages or {}

    async def fetch_message(self, message_id):
        import discord

        message = self._messages.get(message_id)
        if message is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return message


class FakeMember:
    def __init__(
        self,
        member_id,
        name="user",
        display_name=None,
        role_ids=(),
        roles=None,
        administrator=False,
        bot=False,
        top_role=None,
    ):
        self.id = member_id
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.bot = bot
        self.joined_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
        self.created_at = datetime(2020, 6, 1, tzinfo=timezone.utc)
        default_role = FakeRole(0, name="@everyone", position=0, default=True)
        self.roles = [default_role] + (roles if roles is not None else [FakeRole(r) for r in role_ids])
        self.guild_permissions = FakePermissions(administrator)
        self.display_avatar = FakeAsset()
        self.top_role = top_role or (self.roles[-1] if len(self.roles) > 1 else default_role)
        self.action_calls = []
        self.action_raises = None

    async def _record(self, action, **kwargs):
        if self.action_raises:
            raise self.action_raises
        self.action_calls.append((action, kwargs))

    async def ban(self, **kwargs):
        await self._record("ban", **kwargs)

    async def kick(self, **kwargs):
        await self._record("kick", **kwargs)

    async def add_roles(self, role, **kwargs):
        await self._record("add_roles", role=role, **kwargs)

    async def remove_roles(self, role, **kwargs):
        await self._record("remove_roles", role=role, **kwargs)


class FakeGuild:
    def __init__(self, members=None, roles=None, me=None, channels=None, emojis=None):
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
        self.channels = channels or []
        self.emojis = emojis or []

    def get_member(self, user_id):
        return next((m for m in self.members if m.id == user_id), None)

    def get_role(self, role_id):
        return next((r for r in self.roles if r.id == role_id), None)

    def get_channel(self, channel_id):
        return next((c for c in self.channels if c.id == channel_id), None)

    async def fetch_member(self, user_id):
        import discord

        member = self.get_member(user_id)
        if member is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return member


class FakeBot:
    def __init__(self, guild, user=None):
        self._guild = guild
        self.user = user or FakeMember(999999, name="ChetBot", bot=True)
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []

    def get_guild(self, guild_id):
        return self._guild

    async def send_log(self, embed):
        self.sent_logs.append(embed)

    def utcnow(self):
        return datetime.now(timezone.utc)


def make_moderation_app(bot, routes_tables, config=TEST_CONFIG):
    app = web.Application()
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = 1
    setup_session(app, config.session_secret)
    for table in routes_tables:
        app.add_routes(table)

    async def test_login(request):
        session = await new_session(request)
        session["discord_user_id"] = request.query["user_id"]
        return web.json_response({"ok": True})

    app.router.add_get("/test/login", test_login)
    return app


async def force_login(client, user_id):
    resp = await client.get(f"/test/login?user_id={user_id}")
    assert resp.status == 200
