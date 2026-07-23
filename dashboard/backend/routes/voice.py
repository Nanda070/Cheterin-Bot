import discord
from aiohttp import web

import voice_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/voice/rooms")
@require_dashboard_access
async def voice_rooms_list(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild_id = request["guild_id"]
    guild = bot.get_guild(guild_id)

    rooms = []
    for row in voice_db.db_get_rooms_for_guild(guild_id):
        channel = guild.get_channel(row["channel_id"]) if guild else None
        owner = guild.get_member(row["owner_id"]) if guild else None
        rooms.append({
            "channel_id": str(row["channel_id"]),
            "name": channel.name if channel else row["room_name"],
            "owner_id": str(row["owner_id"]),
            "owner_display": owner.display_name if owner else str(row["owner_id"]),
            "is_closed": bool(row["is_closed"]),
            "user_limit": row["user_limit"],
            "member_count": len(channel.members) if isinstance(channel, discord.VoiceChannel) else 0,
            "exists": isinstance(channel, discord.VoiceChannel),
        })
    return web.json_response({"rooms": rooms})


@routes.delete("/api/voice/rooms/{channel_id}")
@require_dashboard_access
async def voice_room_delete(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild_id = request["guild_id"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel_id = int(request.match_info["channel_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    room = voice_db.db_get_room(channel_id)
    if room is None:
        return web.json_response({"error": "not_found"}, status=404)
    if int(room["guild_id"]) != int(guild_id):
        return web.json_response({"error": "not_found"}, status=404)

    channel = guild.get_channel(channel_id)
    if isinstance(channel, discord.VoiceChannel):
        moderator = request["moderator"]
        try:
            await channel.delete(reason=f"Удалено через дашборд ({moderator.display_name})")
        except discord.HTTPException:
            return web.json_response({"error": "delete_failed"}, status=502)

    voice_db.db_delete_room(channel_id)
    # Убираем владельца из кэша, только если он всё ещё привязан к этой комнате
    ownership_key = (room["guild_id"], room["owner_id"])
    if voice_db.user_owned_channels.get(ownership_key) == channel_id:
        voice_db.user_owned_channels.pop(ownership_key, None)
    return web.json_response({"ok": True})


@routes.post("/api/voice/panel/publish")
@require_dashboard_access
async def voice_panel_publish(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("PanelManager")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    message_id = await cog.publish_panel(request["guild_id"])
    if message_id is None:
        return web.json_response({"error": "panel_channel_not_configured"}, status=409)
    return web.json_response({"ok": True, "message_id": str(message_id)})
