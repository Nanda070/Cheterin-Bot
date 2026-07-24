import discord
from aiohttp import web

import birthdays_core
import birthdays_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/birthdays")
@require_dashboard_access
async def birthdays_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    settings = birthdays_core.get_settings(guild_id)
    guild = request.app["bot"].get_guild(guild_id)
    entries = []
    for row in birthdays_db.list_birthdays(guild_id):
        member = guild.get_member(row["user_id"]) if guild else None
        entries.append({
            "user_id": str(row["user_id"]),
            "display_name": member.display_name if member else str(row["user_id"]),
            "mm_dd": row["mm_dd"],
        })
    return web.json_response({**settings, "birthdays": entries})


@routes.put("/api/birthdays/settings")
@require_dashboard_access
async def birthdays_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    channel_id = body.get("channel_id", "")
    ping_role_id = body.get("ping_role_id", "")

    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel_id"}, status=400)
    if not isinstance(ping_role_id, str) or (ping_role_id and not ping_role_id.isdigit()):
        return web.json_response({"error": "invalid_ping_role_id"}, status=400)
    if enabled and not channel_id:
        return web.json_response({"error": "channel_required"}, status=400)

    return web.json_response(
        birthdays_core.save_settings(
            request["guild_id"],
            enabled=enabled,
            channel_id=channel_id,
            ping_role_id=ping_role_id,
        )
    )


@routes.put("/api/birthdays/{user_id}")
@require_dashboard_access
async def birthdays_set(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    user_id = request.match_info["user_id"]
    if not user_id.isdigit():
        return web.json_response({"error": "invalid_user_id"}, status=400)
    mm_dd = body.get("mm_dd", "")
    if not isinstance(mm_dd, str) or not birthdays_db.is_valid_mm_dd(mm_dd):
        return web.json_response({"error": "invalid_mm_dd"}, status=400)

    entry = birthdays_db.set_birthday(request["guild_id"], int(user_id), mm_dd)
    return web.json_response({"user_id": str(entry["user_id"]), "mm_dd": entry["mm_dd"]})


@routes.delete("/api/birthdays/{user_id}")
@require_dashboard_access
async def birthdays_delete(request: web.Request) -> web.Response:
    user_id = request.match_info["user_id"]
    if not user_id.isdigit():
        return web.json_response({"error": "invalid_user_id"}, status=400)
    if not birthdays_db.delete_birthday(request["guild_id"], int(user_id)):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/birthdays/test")
@require_dashboard_access
async def birthdays_test(request: web.Request) -> web.Response:
    """Send a test birthday announcement to the configured channel (does not mark announced)."""
    import i18n

    guild_id = request["guild_id"]
    settings = birthdays_core.get_settings(guild_id)
    if not settings["channel_id"]:
        return web.json_response({"error": "channel_not_configured"}, status=409)

    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "guild_unavailable"}, status=503)
    channel = guild.get_channel(int(settings["channel_id"]))
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)
    # Match announce_loop: only discord.TextChannel (skip voice/forum/etc.).
    if not isinstance(channel, discord.TextChannel):
        return web.json_response({"error": "channel_not_text"}, status=409)

    lang = i18n.lang_for(guild_id)
    ping = ""
    if settings["ping_role_id"]:
        ping = f"<@&{settings['ping_role_id']}> "
    sample = guild.me.mention if guild.me else "@member"
    text = (
        "🧪 "
        + ping
        + i18n.t("birthdays.announce", lang, members=sample)
    )
    try:
        await channel.send(text)
    except Exception:
        return web.json_response({"error": "send_failed"}, status=502)
    return web.json_response({"ok": True})
