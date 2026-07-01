import discord
import pytest

from dashboard.backend.member_lookup import resolve_guild_member


class _StubNotFound(discord.NotFound):
    def __init__(self):
        pass  # bypass real HTTPException.__init__, we don't need a real HTTP response


class _StubHTTPException(discord.HTTPException):
    def __init__(self):
        pass


class FakeGuild:
    def __init__(self, cached_member=None, fetch_result=None, fetch_raises=None):
        self._cached_member = cached_member
        self._fetch_result = fetch_result
        self._fetch_raises = fetch_raises

    def get_member(self, user_id):
        return self._cached_member

    async def fetch_member(self, user_id):
        if self._fetch_raises:
            raise self._fetch_raises
        return self._fetch_result


class FakeBot:
    def __init__(self, guild):
        self._guild = guild

    def get_guild(self, guild_id):
        return self._guild


@pytest.mark.asyncio
async def test_returns_cached_member_without_fetching():
    guild = FakeGuild(cached_member="member-from-cache")
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member == "member-from-cache"
    assert result.not_found is False
    assert result.service_error is False


@pytest.mark.asyncio
async def test_falls_back_to_fetch_when_not_cached():
    guild = FakeGuild(cached_member=None, fetch_result="member-from-fetch")
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member == "member-from-fetch"


@pytest.mark.asyncio
async def test_not_found_when_fetch_raises_notfound():
    guild = FakeGuild(cached_member=None, fetch_raises=_StubNotFound())
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member is None
    assert result.not_found is True
    assert result.service_error is False


@pytest.mark.asyncio
async def test_service_error_when_fetch_raises_http_exception():
    guild = FakeGuild(cached_member=None, fetch_raises=_StubHTTPException())
    bot = FakeBot(guild)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.member is None
    assert result.service_error is True


@pytest.mark.asyncio
async def test_service_error_when_guild_missing():
    bot = FakeBot(guild=None)
    result = await resolve_guild_member(bot, 1, 42)
    assert result.service_error is True
