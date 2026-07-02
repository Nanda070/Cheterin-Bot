import functools

from aiohttp import web
from aiohttp_session import get_session

from .access import has_dashboard_access
from .member_lookup import resolve_guild_member


def require_dashboard_access(handler):
    """Guard an aiohttp handler with the Phase 1 session -> member -> role check.

    On success the resolved discord.Member is available as request["moderator"].
    """

    @functools.wraps(handler)
    async def wrapper(request: web.Request) -> web.StreamResponse:
        session = await get_session(request)
        user_id = session.get("discord_user_id")
        if not user_id:
            return web.json_response({"error": "unauthorized"}, status=401)

        config = request.app["dashboard_config"]
        bot = request.app["bot"]
        guild_id = request.app["guild_id"]

        lookup = await resolve_guild_member(bot, guild_id, int(user_id))
        if lookup.service_error:
            return web.json_response({"error": "service_unavailable"}, status=503)
        if lookup.not_found or lookup.member is None:
            return web.json_response({"error": "forbidden"}, status=403)
        if not has_dashboard_access(lookup.member, config.access_role_ids):
            return web.json_response({"error": "forbidden"}, status=403)

        request["moderator"] = lookup.member
        return await handler(request)

    return wrapper
