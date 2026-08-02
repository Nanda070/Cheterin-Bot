from aiohttp import web

import bot_profile_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _asset_url(asset) -> str | None:
    if asset is None:
        return None
    url = getattr(asset, "url", None)
    if url:
        return str(url)
    try:
        return str(asset)
    except Exception:
        return None


@routes.get("/api/bot-profile")
@require_dashboard_access
async def bot_profile_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    me = guild.me
    if me is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    settings = bot_profile_core.get_settings(guild_id)

    # Prefer guild-specific assets when present.
    guild_avatar = getattr(me, "guild_avatar", None)
    display_avatar = getattr(me, "display_avatar", None)
    avatar = guild_avatar or display_avatar

    guild_banner = getattr(me, "guild_banner", None)
    display_banner = getattr(me, "display_banner", None)
    banner = guild_banner or display_banner

    return web.json_response({
        "nick": me.nick or "",
        "display_name": getattr(me, "display_name", None) or me.name,
        "avatar_url": _asset_url(avatar),
        "banner_url": _asset_url(banner),
        "settings": settings,
    })


@routes.put("/api/bot-profile")
@require_dashboard_access
async def bot_profile_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    guild_id = request["guild_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    fields: dict = {}
    nick_update: str | None = None
    avatar_flag: bool | None = None
    banner_flag: bool | None = None

    if "nick" in body:
        try:
            nick_update = bot_profile_core.normalize_nick(body["nick"])
        except ValueError as exc:
            return web.json_response({"error": str(exc.args[0])}, status=400)
        # Discord: empty / null clears nick
        fields["nick"] = nick_update or None

    if "avatar" in body:
        try:
            payload, _raw = bot_profile_core.parse_image_data_uri(body["avatar"])
        except ValueError as exc:
            return web.json_response({"error": str(exc.args[0])}, status=400)
        fields["avatar"] = payload
        avatar_flag = payload is not None

    if "banner" in body:
        try:
            payload, _raw = bot_profile_core.parse_image_data_uri(body["banner"])
        except ValueError as exc:
            return web.json_response({"error": str(exc.args[0])}, status=400)
        fields["banner"] = payload
        banner_flag = payload is not None

    if not fields:
        return web.json_response({"error": "nothing_to_update"}, status=400)

    try:
        await bot.http.edit_my_member(guild_id, **fields)
    except Exception:
        return web.json_response({"error": "discord_rejected"}, status=502)

    settings = bot_profile_core.save_settings(
        guild_id,
        nick=nick_update if nick_update is not None else None,
        has_custom_avatar=avatar_flag,
        has_custom_banner=banner_flag,
    )

    # Re-read effective profile after edit (cache may lag; return what we know).
    me = guild.me
    guild_avatar = getattr(me, "guild_avatar", None) if me else None
    display_avatar = getattr(me, "display_avatar", None) if me else None
    avatar = guild_avatar or display_avatar
    guild_banner = getattr(me, "guild_banner", None) if me else None
    display_banner = getattr(me, "display_banner", None) if me else None
    banner = guild_banner or display_banner

    effective_nick = fields["nick"] if "nick" in fields else (me.nick if me else "")
    return web.json_response({
        "nick": effective_nick or "",
        "display_name": (getattr(me, "display_name", None) or (me.name if me else "") or ""),
        "avatar_url": _asset_url(avatar),
        "banner_url": _asset_url(banner),
        "settings": settings,
        "ok": True,
    })
