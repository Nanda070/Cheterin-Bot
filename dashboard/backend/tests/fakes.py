import asyncio
from datetime import datetime, timezone

from aiohttp import web
from aiohttp_session import new_session

from dashboard.backend.config import DashboardConfig
from dashboard.backend.guild_context import guild_context_middleware
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


class FakeGuildInner:
    def __init__(self, guild_id=1):
        self.id = guild_id


class FakeRole:
    def __init__(self, role_id, name="role", position=1, color_value=0, managed=False, default=False):
        self.id = role_id
        self.name = name
        self.mention = f"<@&{role_id}>"
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
    def __init__(self, administrator=False, mention_everyone=False, manage_guild=False):
        self.administrator = administrator
        self.mention_everyone = mention_everyone
        self.manage_guild = manage_guild


class FakeAsset:
    def __init__(self, url="https://cdn.example/avatar.png", data=b"fake-avatar-bytes"):
        self.url = url
        self._data = data

    def __str__(self):
        return self.url

    def replace(self, **kwargs):
        return self

    async def read(self):
        return self._data


class FakeCustomEmoji:
    def __init__(self, emoji_id, name):
        self.id = emoji_id
        self.name = name
        self.url = f"https://cdn.example/emojis/{emoji_id}.png"

    def __str__(self):
        return f"<:{self.name}:{self.id}>"


class FakeMessage:
    def __init__(self, message_id, embeds=None, components=None, content=None):
        self.id = message_id
        self.content = content
        self.embeds = embeds or []
        self.components = components or []
        self.reaction_calls = []
        self.add_reaction_raises = None
        self.remove_reaction_raises = None
        self.edit_calls = []
        self.edit_raises = None

    @property
    def jump_url(self):
        return f"https://discord.com/channels/0/0/{self.id}"

    async def add_reaction(self, emoji):
        if self.add_reaction_raises:
            raise self.add_reaction_raises
        self.reaction_calls.append(("add", str(emoji)))

    async def remove_reaction(self, emoji, member):
        if self.remove_reaction_raises:
            raise self.remove_reaction_raises
        self.reaction_calls.append(("remove", str(emoji)))

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)
        if "content" in kwargs:
            self.content = kwargs["content"]
        if "embed" in kwargs:
            self.embeds = [kwargs["embed"]] if kwargs["embed"] else []
        if "view" in kwargs:
            self.components = kwargs["view"]

    async def delete(self):
        pass


class FakeComponentRow:
    def __init__(self, children):
        self.children = children


class _FakeChannelType:
    def __init__(self, name):
        self.name = name


class FakeChannel:
    def __init__(self, channel_id, name="channel", messages=None, next_message_id=1000, type_name="text"):
        self.id = channel_id
        self.name = name
        self._messages = messages or {}
        self._next_message_id = next_message_id
        self.type = _FakeChannelType(type_name)
        self.guild = FakeGuildInner(1)
        self.send_calls = []
        self.send_raises = None
        self.purge_calls = []
        self.purge_raises = None
        self.edit_calls = []
        self.edit_raises = None
        self.slowmode_delay = 0

    @property
    def mention(self):
        return f"<#{self.id}>"

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)
        if "slowmode_delay" in kwargs:
            self.slowmode_delay = kwargs["slowmode_delay"]

    async def fetch_message(self, message_id):
        import discord

        message = self._messages.get(message_id)
        if message is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return message

    async def purge(self, limit=100, **kwargs):
        if self.purge_raises:
            raise self.purge_raises
        self.purge_calls.append(limit)
        ordered = sorted(self._messages.values(), key=lambda m: m.id, reverse=True)
        deleted = ordered[:limit]
        for message in deleted:
            self._messages.pop(message.id, None)
        return deleted

    async def send(self, content=None, **kwargs):
        if self.send_raises:
            raise self.send_raises
        if content is not None:
            kwargs["content"] = content
        self.send_calls.append(kwargs)
        message = FakeMessage(
            self._next_message_id,
            embeds=[kwargs["embed"]] if kwargs.get("embed") else [],
            components=kwargs.get("view"),
            content=kwargs.get("content"),
        )
        self._messages[message.id] = message
        self._next_message_id += 1
        return message


class FakeThread:
    def __init__(self, thread_id, name="thread", messages=None, next_message_id=2000):
        self.id = thread_id
        self.name = name
        self.mention = f"<#{thread_id}>"
        self._messages = messages or {}
        self._next_message_id = next_message_id
        self.send_calls = []
        self.send_raises = None
        self.edit_calls = []
        self.edit_raises = None
        self.archived = False
        self.locked = False

    async def fetch_message(self, message_id):
        import discord

        message = self._messages.get(message_id)
        if message is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return message

    async def send(self, content=None, **kwargs):
        if self.send_raises:
            raise self.send_raises
        if content is not None:
            kwargs["content"] = content
        self.send_calls.append(kwargs)
        message = FakeMessage(
            self._next_message_id,
            embeds=[kwargs["embed"]] if kwargs.get("embed") else [],
            components=kwargs.get("view"),
            content=kwargs.get("content"),
        )
        self._messages[message.id] = message
        self._next_message_id += 1
        return message

    async def edit(self, **kwargs):
        if self.edit_raises:
            raise self.edit_raises
        self.edit_calls.append(kwargs)
        if "archived" in kwargs:
            self.archived = kwargs["archived"]
        if "locked" in kwargs:
            self.locked = kwargs["locked"]


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
        manage_guild=False,
    ):
        self.id = member_id
        self.name = name
        self.display_name = display_name if display_name is not None else name
        self.nick = display_name
        self.mention = f"<@{member_id}>"
        self.bot = bot
        self.joined_at = datetime(2025, 1, 15, tzinfo=timezone.utc)
        self.created_at = datetime(2020, 6, 1, tzinfo=timezone.utc)
        default_role = FakeRole(0, name="@everyone", position=0, default=True)
        self.roles = [default_role] + (roles if roles is not None else [FakeRole(r) for r in role_ids])
        self.guild_permissions = FakePermissions(administrator, manage_guild=manage_guild)
        self.display_avatar = FakeAsset()
        self.top_role = top_role or (self.roles[-1] if len(self.roles) > 1 else default_role)
        self.action_calls = []
        self.action_raises = None
        self.send_calls = []
        self.send_raises = None
        self._timed_out_until = None

    def __str__(self) -> str:
        return self.name

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

    async def timeout(self, duration, **kwargs):
        await self._record("timeout", duration=duration, **kwargs)
        self._timed_out_until = duration

    def is_timed_out(self) -> bool:
        return self._timed_out_until is not None

    @property
    def timed_out_until(self):
        return self._timed_out_until

    async def remove_roles(self, role, **kwargs):
        await self._record("remove_roles", role=role, **kwargs)

    async def send(self, **kwargs):
        if self.send_raises:
            raise self.send_raises
        self.send_calls.append(kwargs)


class FakeVoiceChannel:
    def __init__(self, channel_id, name="voice"):
        self.id = channel_id
        self.name = name
        self.mention = f"<#{channel_id}>"
        self.deleted = False
        self.delete_reason = None

    async def delete(self, reason=None):
        self.deleted = True
        self.delete_reason = reason


class FakeAuditLogExtra:
    def __init__(self, channel=None):
        self.channel = channel


class FakeAuditLogEntry:
    """Одна запись аудита для guild.audit_logs() — только то, что нужно
    serverlog.py._recent_audit_entry(): action/target/user/reason/created_at,
    плюс extra.channel для voice move/disconnect."""

    def __init__(self, user, action=None, reason=None, target=None, created_at=None, channel=None):
        self.user = user
        self.action = action
        self.reason = reason
        self.target = target
        self.created_at = created_at if created_at is not None else datetime.now(timezone.utc)
        self.extra = FakeAuditLogExtra(channel=channel)


class FakeGuild:
    def __init__(
        self, members=None, roles=None, me=None, channels=None, emojis=None, fetchable_members=None, threads=None,
        guild_id=1, name="Test Guild", icon=None, member_count=None, owner_id=None,
    ):
        self.id = guild_id  # По умолчанию 1 — совпадает с app["guild_id"] в make_moderation_app.
        self.name = name
        self.icon = icon
        self.member_count = member_count if member_count is not None else len(members or [])
        self.owner_id = owner_id
        self.members = members or []
        self.roles = roles or []
        self.me = me or FakeMember(1, name="bot", top_role=FakeRole(900, name="bot-role", position=50))
        # Как в discord.py: у каждого Member есть обратная ссылка на его guild —
        # многие *_core.py читают настройки по member.guild.id / interaction.guild.id.
        for _member in self.members:
            _member.guild = self
        self.me.guild = self
        self.channels = channels or []
        self.emojis = emojis or []
        self._fetchable_members = fetchable_members or []
        self.threads = threads or []
        self.default_role = FakeRole(0, name="@everyone", position=0, default=True)
        self.created_voice_channels = []
        self._next_voice_channel_id = 9000
        self.create_voice_channel_raises = None
        self._ban_entries: dict[int, object] = {}
        self.ban_calls = []
        self.unban_calls = []
        self.ban_raises = None
        self.unban_raises = None
        self.audit_log_entries: list = []
        self.audit_logs_raises = None

    def audit_logs(self, action=None, limit=100):
        raises = self.audit_logs_raises
        entries = [e for e in self.audit_log_entries if action is None or e.action is None or e.action == action]
        entries = entries[:limit]

        async def _iterator():
            if raises:
                raise raises
            for entry in entries:
                yield entry

        return _iterator()

    def get_member(self, user_id):
        return next((m for m in self.members if m.id == user_id), None)

    def get_role(self, role_id):
        return next((r for r in self.roles if r.id == role_id), None)

    def get_channel(self, channel_id):
        return next((c for c in self.channels if c.id == channel_id), None)

    @property
    def text_channels(self):
        return list(self.channels)

    async def ban(self, user, reason=None, **kwargs):
        if self.ban_raises:
            raise self.ban_raises
        self.ban_calls.append({"user": user, "reason": reason})
        self._ban_entries[user.id] = user
        self.members = [m for m in self.members if m.id != user.id]

    async def unban(self, user, reason=None, **kwargs):
        import discord

        if self.unban_raises:
            raise self.unban_raises
        user_id = user.id if hasattr(user, "id") else int(user)
        if user_id not in self._ban_entries:
            raise discord.NotFound.__new__(discord.NotFound)
        del self._ban_entries[user_id]
        self.unban_calls.append({"user_id": user_id, "reason": reason})

    async def fetch_ban(self, user):
        import discord

        user_id = user.id if hasattr(user, "id") else int(user)
        banned_user = self._ban_entries.get(user_id)
        if banned_user is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return type("FakeBanEntry", (), {"reason": None, "user": banned_user})()

    async def create_voice_channel(self, name, **kwargs):
        if self.create_voice_channel_raises:
            raise self.create_voice_channel_raises
        voice_channel = FakeVoiceChannel(self._next_voice_channel_id, name=name)
        self._next_voice_channel_id += 1
        self.created_voice_channels.append(voice_channel)
        self.channels.append(voice_channel)
        return voice_channel

    async def fetch_member(self, user_id):
        import discord

        member = self.get_member(user_id)
        if member is None:
            member = next((m for m in self._fetchable_members if m.id == user_id), None)
        if member is None:
            raise discord.NotFound.__new__(discord.NotFound)
        return member

    async def invites(self):
        return list(getattr(self, "_invites", []))


class FakeBot:
    def __init__(self, guild, user=None, fetchable_users=None, guilds=None):
        self._guild = guild
        self.guilds = guilds if guilds is not None else [guild]
        self.user = user or FakeMember(999999, name="ChetBot", bot=True)
        self.cogs = {}  # имя кога → ког (как bot.cogs в discord.py)
        self.stats = {}
        self.feedback_cases = {}
        self.sent_logs = []
        self._fetchable_users = fetchable_users or []
        self.update_file_calls = 0

    @property
    def loop(self):
        return asyncio.get_event_loop()

    def get_guild(self, guild_id):
        return self._guild

    def get_cog(self, name):
        # Тесты, которым нужен конкретный ког, переопределяют этот метод (bot.get_cog = ...).
        return None

    def get_channel(self, channel_id):
        found = self._guild.get_channel(channel_id)
        if found is not None:
            return found
        return next((t for t in self._guild.threads if t.id == channel_id), None)

    def get_user(self, user_id):
        return self._guild.get_member(user_id)

    async def fetch_user(self, user_id):
        import discord

        member = self._guild.get_member(user_id)
        if member is not None:
            return member
        found = next((u for u in self._fetchable_users if u.id == user_id), None)
        if found is not None:
            return found
        raise discord.NotFound.__new__(discord.NotFound)

    async def update_file(self):
        self.update_file_calls += 1

    async def send_log(self, guild_id, embed):
        self.sent_logs.append(embed)

    def utcnow(self):
        return datetime.now(timezone.utc)


def make_moderation_app(bot, routes_tables, config=TEST_CONFIG):
    app = web.Application(middlewares=[guild_context_middleware])
    app["bot"] = bot
    app["dashboard_config"] = config
    app["guild_id"] = 1
    setup_session(app, config.session_secret)
    for table in routes_tables:
        app.add_routes(table)

    async def test_login(request):
        session = await new_session(request)
        session["discord_user_id"] = request.query["user_id"]
        active_guild_id = request.query.get("active_guild_id")
        if active_guild_id:
            session["active_guild_id"] = active_guild_id
        return web.json_response({"ok": True})

    app.router.add_get("/test/login", test_login)
    return app


async def force_login(client, user_id, active_guild_id=1):
    """Log in for dashboard tests. Default active guild is 1 (app main).

    Pass ``active_guild_id=None`` to leave the session without a selected guild
    (exercises ``no_guild_selected``).
    """
    url = f"/test/login?user_id={user_id}"
    if active_guild_id is not None:
        url += f"&active_guild_id={active_guild_id}"
    resp = await client.get(url)
    assert resp.status == 200
