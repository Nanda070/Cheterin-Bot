from aiohttp import web

import supply_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _display_name(guild, user_id: str) -> str:
    member = guild.get_member(int(user_id)) if guild else None
    return member.display_name if member else user_id


def _serialize_supply(supply: dict, guild) -> dict:
    return {
        "id": supply["id"],
        "initiator_id": supply["initiator_id"],
        "initiator_display": _display_name(guild, supply["initiator_id"]),
        "opponent": supply["opponent"],
        "limit": supply["limit"],
        "time_str": supply["time_str"],
        "target_ts": supply["target_ts"],
        "status": supply["status"],
        "participants": [
            {"id": uid, "display": _display_name(guild, uid)} for uid in supply["participants"]
        ],
        "reserve": [
            {"id": uid, "display": _display_name(guild, uid)} for uid in supply.get("reserve", [])
        ],
        "channel_id": supply["channel_id"],
        "created_at": supply["created_at"],
        "closed_at": supply["closed_at"],
    }


@routes.get("/api/supply")
@require_dashboard_access
async def supply_overview(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    guild = request.app["bot"].get_guild(guild_id)
    active = [_serialize_supply(s, guild) for s in supply_core.list_active(guild_id)]
    history = [_serialize_supply(s, guild) for s in supply_core.list_history(guild_id)]
    stats = [
        {"user_id": row["user_id"], "display": _display_name(guild, row["user_id"]), "count": row["count"]}
        for row in supply_core.get_stats(guild_id)
    ]
    return web.json_response({"active": active, "history": history, "stats": stats})


@routes.post("/api/supply")
@require_dashboard_access
async def supply_create(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    cog = bot.get_cog("SupplyCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    opponent = body.get("opponent")
    time_str = body.get("time_str")
    limit = body.get("limit")
    channel_raw = body.get("channel_id")

    if not isinstance(opponent, str) or not opponent.strip():
        return web.json_response({"error": "invalid_opponent"}, status=400)
    if not isinstance(time_str, str) or not supply_core.is_valid_time(time_str):
        return web.json_response({"error": "invalid_time"}, status=400)
    if not isinstance(limit, int) or limit < 1 or limit > 99:
        return web.json_response({"error": "invalid_limit"}, status=400)
    try:
        channel_id = int(channel_raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_channel"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)
    if not hasattr(channel, "send"):
        # Категории и форумы не принимают обычные сообщения
        return web.json_response({"error": "channel_not_messageable"}, status=400)

    moderator = request["moderator"]
    supply = await cog.publish_supply(request["guild_id"], channel, moderator.id, opponent.strip(), limit, time_str)
    return web.json_response(_serialize_supply(supply, guild), status=201)


async def _finalize(request: web.Request, status: str, reason: str) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("SupplyCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    guild_id = request["guild_id"]
    supply_id = request.match_info["supply_id"]
    if supply_core.get_supply(guild_id, supply_id) is None:
        return web.json_response({"error": "not_found"}, status=404)

    moderator = request["moderator"]
    ok = await cog.finalize_supply(guild_id, supply_id, reason=f"{reason} через дашборд ({moderator.display_name})", status=status)
    if not ok:
        return web.json_response({"error": "not_active"}, status=409)
    return web.json_response({"ok": True})


@routes.post("/api/supply/{supply_id}/close")
@require_dashboard_access
async def supply_close(request: web.Request) -> web.Response:
    return await _finalize(request, "finished", "закрыт")


@routes.post("/api/supply/{supply_id}/cancel")
@require_dashboard_access
async def supply_cancel(request: web.Request) -> web.Response:
    return await _finalize(request, "cancelled", "отменён")
