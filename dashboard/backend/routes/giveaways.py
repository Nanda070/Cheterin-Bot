from aiohttp import web

import giveaway_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _display_name(guild, user_id: str) -> str:
    member = guild.get_member(int(user_id)) if guild else None
    return member.display_name if member else user_id


def _serialize_giveaway(giveaway: dict, guild) -> dict:
    return {
        "id": giveaway["id"],
        "initiator_id": giveaway["initiator_id"],
        "initiator_display": _display_name(guild, giveaway["initiator_id"]),
        "prize": giveaway["prize"],
        "winners_count": giveaway["winners_count"],
        "duration_str": giveaway["duration_str"],
        "target_ts": giveaway["target_ts"],
        "status": giveaway["status"],
        "entrants": [{"id": uid, "display": _display_name(guild, uid)} for uid in giveaway["entrants"]],
        "winners": [{"id": uid, "display": _display_name(guild, uid)} for uid in giveaway["winners"]],
        "channel_id": giveaway["channel_id"],
        "created_at": giveaway["created_at"],
        "closed_at": giveaway["closed_at"],
    }


@routes.get("/api/giveaways")
@require_dashboard_access
async def giveaways_overview(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    guild = request.app["bot"].get_guild(guild_id)
    active = [_serialize_giveaway(g, guild) for g in giveaway_core.list_active(guild_id)]
    history = [_serialize_giveaway(g, guild) for g in giveaway_core.list_history(guild_id)]
    return web.json_response({"active": active, "history": history})


@routes.post("/api/giveaways")
@require_dashboard_access
async def giveaways_create(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    cog = bot.get_cog("GiveawayCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    prize = body.get("prize")
    duration_str = body.get("duration_str")
    winners_count = body.get("winners_count")
    channel_raw = body.get("channel_id")

    if not isinstance(prize, str) or not prize.strip():
        return web.json_response({"error": "invalid_prize"}, status=400)
    if not isinstance(duration_str, str):
        return web.json_response({"error": "invalid_duration"}, status=400)
    try:
        giveaway_core.parse_duration(duration_str)
    except ValueError:
        return web.json_response({"error": "invalid_duration"}, status=400)
    if not isinstance(winners_count, int) or isinstance(winners_count, bool) or not 1 <= winners_count <= 20:
        return web.json_response({"error": "invalid_winners_count"}, status=400)
    try:
        channel_id = int(channel_raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_channel"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)
    if not hasattr(channel, "send"):
        return web.json_response({"error": "channel_not_messageable"}, status=400)

    moderator = request["moderator"]
    giveaway = await cog.publish_giveaway(request["guild_id"], channel, moderator.id, prize.strip(), duration_str, winners_count)
    return web.json_response(_serialize_giveaway(giveaway, guild), status=201)


@routes.post("/api/giveaways/{giveaway_id}/reroll")
@require_dashboard_access
async def giveaways_reroll(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("GiveawayCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    giveaway_id = request.match_info["giveaway_id"]
    winners = await cog.reroll_and_announce(request["guild_id"], giveaway_id)
    if winners is None:
        return web.json_response({"error": "not_finished"}, status=409)
    return web.json_response({"ok": True, "winners": winners})


@routes.post("/api/giveaways/{giveaway_id}/end")
@require_dashboard_access
async def giveaways_end(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("GiveawayCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    guild_id = request["guild_id"]
    giveaway_id = request.match_info["giveaway_id"]
    if giveaway_core.get_giveaway(guild_id, giveaway_id) is None:
        return web.json_response({"error": "not_found"}, status=404)

    ok = await cog.finalize_giveaway(guild_id, giveaway_id)
    if not ok:
        return web.json_response({"error": "not_active"}, status=409)
    return web.json_response({"ok": True})
