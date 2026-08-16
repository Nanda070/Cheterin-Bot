from aiohttp import web

import discord

import customs_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/customs/categories")
@require_dashboard_access
async def list_categories(request: web.Request) -> web.Response:
    """Return Discord CategoryChannel objects for voice_category_id pickers."""
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    categories = [
        {"id": str(c.id), "name": c.name}
        for c in guild.categories
    ]
    return web.json_response({"categories": categories})


def _cog(request: web.Request):
    return request.app["bot"].get_cog("CustomsCog")


@routes.get("/api/customs")
@require_dashboard_access
async def customs_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    return web.json_response(customs_core.get_settings(guild_id))


@routes.put("/api/customs")
@require_dashboard_access
async def customs_put(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if "enabled" in body and not isinstance(body["enabled"], bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if "channel_id" in body:
        channel_id = body.get("channel_id") or ""
        if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
            return web.json_response({"error": "invalid_channel_id"}, status=400)
    if "host_role_id" in body:
        host_role_id = body.get("host_role_id") or ""
        if not isinstance(host_role_id, str) or (host_role_id and not host_role_id.isdigit()):
            return web.json_response({"error": "invalid_host_role_id"}, status=400)
    if "voice_category_id" in body:
        voice_category_id = body.get("voice_category_id") or ""
        if not isinstance(voice_category_id, str) or (
            voice_category_id and not voice_category_id.isdigit()
        ):
            return web.json_response({"error": "invalid_voice_category_id"}, status=400)
    if "results_channel_id" in body:
        results_channel_id = body.get("results_channel_id") or ""
        if not isinstance(results_channel_id, str) or (
            results_channel_id and not results_channel_id.isdigit()
        ):
            return web.json_response({"error": "invalid_results_channel_id"}, status=400)
    if "ping_role_id" in body:
        ping_role_id = body.get("ping_role_id") or ""
        if not isinstance(ping_role_id, str) or (ping_role_id and not ping_role_id.isdigit()):
            return web.json_response({"error": "invalid_ping_role_id"}, status=400)
    if "auto_lobby_vc" in body and not isinstance(body["auto_lobby_vc"], bool):
        return web.json_response({"error": "invalid_auto_lobby_vc"}, status=400)
    if "auto_move_on_start" in body and not isinstance(body["auto_move_on_start"], bool):
        return web.json_response({"error": "invalid_auto_move_on_start"}, status=400)
    if "avoid_last_map" in body and not isinstance(body["avoid_last_map"], bool):
        return web.json_response({"error": "invalid_avoid_last_map"}, status=400)
    if "default_mode" in body:
        mode = body.get("default_mode")
        if mode not in (customs_core.JOIN_MODE_SOLO, customs_core.JOIN_MODE_TEAM_CODE):
            return web.json_response({"error": "invalid_mode"}, status=400)
    if "default_ping" in body:
        ping = str(body.get("default_ping") or "")
        if ping not in customs_core.PING_MODES:
            return web.json_response({"error": "invalid_ping"}, status=400)

    settings = customs_core.save_settings(guild_id, body)
    return web.json_response(settings)


@routes.get("/api/customs/lobbies")
@require_dashboard_access
async def customs_lobbies_list(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    status = request.query.get("status", "active")
    if status not in ("active", "open", "checkin", "ready", "live", "finished", "cancelled", "all"):
        return web.json_response({"error": "invalid_status"}, status=400)
    if status == "all":
        lobbies = customs_core.list_lobbies(guild_id)
    elif status == "active":
        lobbies = customs_core.list_lobbies(guild_id, status="active")
    else:
        lobbies = customs_core.list_lobbies(guild_id, status=status)
    return web.json_response(
        {"lobbies": [customs_core.serialize_lobby_summary(lob) for lob in lobbies]}
    )


async def _publish_from_spec(request: web.Request, body: dict) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    cog = _cog(request)
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    settings = customs_core.get_settings(request["guild_id"])
    if not settings.get("enabled"):
        return web.json_response({"error": "disabled"}, status=400)

    if not body.get("channel_id") and settings.get("channel_id"):
        body = {**body, "channel_id": settings["channel_id"]}
    if not body.get("join_mode"):
        body = {**body, "join_mode": settings.get("default_mode") or customs_core.JOIN_MODE_SOLO}
    if not body.get("name"):
        body = {**body, "name": settings.get("default_name") or "Кастомка"}
    if body.get("ping") in (None, ""):
        body = {**body, "ping": settings.get("default_ping") or customs_core.PING_NONE}
    if body.get("signup_minutes") in (None, ""):
        body = {**body, "signup_minutes": settings.get("default_signup_minutes") or 0}

    error = customs_core.validate_create_spec(body)
    if error:
        return web.json_response({"error": error}, status=400)

    channel_id = int(body["channel_id"])
    channel = guild.get_channel(channel_id)
    if not isinstance(channel, discord.TextChannel):
        return web.json_response({"error": "channel_not_found"}, status=404)

    moderator = request["moderator"]
    try:
        signup_minutes = int(body.get("signup_minutes") or 0)
    except (TypeError, ValueError):
        signup_minutes = 0
    lobby = customs_core.create_lobby(
        request["guild_id"],
        host_id=moderator.id,
        name=str(body["name"]).strip(),
        notes=str(body.get("notes") or ""),
        join_mode=str(body.get("join_mode") or customs_core.JOIN_MODE_SOLO),
        ping=str(body.get("ping") or customs_core.PING_NONE),
        signup_minutes=signup_minutes,
        banned_maps=list(body.get("banned_maps") or []),
    )
    ping = str(body.get("ping") or customs_core.PING_NONE)
    message = await cog.publish_lobby(guild, lobby, channel, ping=ping)
    lobby = customs_core.get_lobby(request["guild_id"], lobby["id"]) or lobby
    summary = customs_core.serialize_lobby_summary(lobby)
    summary["jump_url"] = message.jump_url
    return web.json_response(summary, status=201)


@routes.post("/api/customs/lobbies")
@require_dashboard_access
async def customs_lobbies_create(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    return await _publish_from_spec(request, body)


@routes.post("/api/customs/lobbies/{lobby_id}/rematch")
@require_dashboard_access
async def customs_lobby_rematch(request: web.Request) -> web.Response:
    source = customs_core.get_lobby(request["guild_id"], request.match_info["lobby_id"])
    if source is None:
        return web.json_response({"error": "not_found"}, status=404)
    spec = customs_core.rematch_spec(source)
    return await _publish_from_spec(request, spec)


@routes.post("/api/customs/lobbies/{lobby_id}/kick")
@require_dashboard_access
async def customs_lobby_kick(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    user_id = str(body.get("user_id") or "")
    if not user_id.isdigit():
        return web.json_response({"error": "invalid_user_id"}, status=400)

    guild_id = request["guild_id"]
    lobby_id = request.match_info["lobby_id"]
    lobby = customs_core.get_lobby(guild_id, lobby_id)
    if lobby is None:
        return web.json_response({"error": "not_found"}, status=404)

    cog = _cog(request)
    guild = request.app["bot"].get_guild(guild_id)
    if cog is not None and guild is not None:
        result = await cog.kick_and_refresh(guild, lobby_id, int(user_id))
    else:
        result = customs_core.kick_player(guild_id, lobby_id, int(user_id))
    if result != "kicked":
        return web.json_response({"error": result}, status=400)
    lobby = customs_core.get_lobby(guild_id, lobby_id)
    return web.json_response({"ok": True, "lobby": customs_core.serialize_lobby_summary(lobby or {})})


@routes.put("/api/customs/lobbies/{lobby_id}/bans")
@require_dashboard_access
async def customs_lobby_bans(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    map_ids = body.get("map_ids")
    if not isinstance(map_ids, list):
        return web.json_response({"error": "invalid_bans"}, status=400)
    if len(map_ids) > customs_core.MAX_LOBBY_MAP_BANS:
        return web.json_response({"error": "invalid_bans"}, status=400)
    lobby = customs_core.set_lobby_bans(request["guild_id"], request.match_info["lobby_id"], map_ids)
    if lobby is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True, "lobby": customs_core.serialize_lobby_summary(lobby)})


@routes.post("/api/customs/lobbies/{lobby_id}/score")
@require_dashboard_access
async def customs_lobby_score(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    try:
        score_a = int(body.get("score_a"))
        score_b = int(body.get("score_b"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_score"}, status=400)
    if min(score_a, score_b) < 0 or max(score_a, score_b) > 99:
        return web.json_response({"error": "invalid_score"}, status=400)

    guild_id = request["guild_id"]
    lobby_id = request.match_info["lobby_id"]
    lobby = customs_core.get_lobby(guild_id, lobby_id)
    if lobby is None:
        return web.json_response({"error": "not_found"}, status=404)
    if lobby.get("status") != customs_core.STATUS_LIVE:
        return web.json_response({"error": "not_live"}, status=400)

    cog = _cog(request)
    guild = request.app["bot"].get_guild(guild_id)
    if cog is not None and guild is not None:
        ok = await cog.apply_match_score(guild, lobby_id, score_a, score_b)
        if not ok:
            return web.json_response({"error": "not_found"}, status=404)
    else:
        customs_core.set_result(guild_id, lobby_id, score_a, score_b)
    lobby = customs_core.get_lobby(guild_id, lobby_id)
    return web.json_response({"ok": True, "lobby": customs_core.serialize_lobby_summary(lobby or {})})


@routes.post("/api/customs/lobbies/{lobby_id}/cancel")
@require_dashboard_access
async def customs_lobby_cancel(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    lobby_id = request.match_info["lobby_id"]
    lobby = customs_core.cancel_lobby(request["guild_id"], lobby_id)
    if lobby is None:
        return web.json_response({"error": "not_found"}, status=404)
    if guild is not None:
        cog = bot.get_cog("CustomsCog")
        if cog is not None:
            await cog.cleanup_lobby(guild, lobby_id)
            await cog.refresh_lobby_message(guild, lobby_id)
            await cog.finish_vote_message(guild, lobby_id, delete=True)
            await cog.finish_score_message(guild, lobby_id, delete=True)
    return web.json_response({"ok": True, "lobby": customs_core.serialize_lobby_summary(lobby)})


@routes.post("/api/customs/schedules")
@require_dashboard_access
async def customs_schedule_create(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    error = customs_core.validate_schedule_spec(body)
    if error:
        return web.json_response({"error": error}, status=400)
    sch = customs_core.upsert_schedule(request["guild_id"], body)
    if sch is None:
        return web.json_response({"error": "invalid_schedule"}, status=400)
    return web.json_response(sch, status=201)


@routes.delete("/api/customs/schedules/{schedule_id}")
@require_dashboard_access
async def customs_schedule_delete(request: web.Request) -> web.Response:
    ok = customs_core.delete_schedule(request["guild_id"], request.match_info["schedule_id"])
    if not ok:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


@routes.get("/api/customs/leaderboard")
@require_dashboard_access
async def customs_leaderboard(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    return web.json_response({"leaderboard": customs_core.leaderboard(guild_id)})
