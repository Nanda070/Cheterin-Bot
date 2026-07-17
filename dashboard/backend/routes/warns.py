from aiohttp import web

import automod_core
import warns_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

MAX_REASON_LENGTH = 500


@routes.get("/api/members/{member_id}/warns")
@require_dashboard_access
async def member_warns_list(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    member_id_raw = request.match_info["member_id"]
    if not member_id_raw.isdigit():
        return web.json_response({"error": "invalid_member_id"}, status=400)
    member_id = int(member_id_raw)

    warns = warns_core.get_warns(guild.id, member_id)
    return web.json_response({
        "warns": warns,
        "active_count": warns_core.get_active_warn_count(guild.id, member_id),
    })


@routes.post("/api/members/{member_id}/warns")
@require_dashboard_access
async def member_warns_create(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    member_id_raw = request.match_info["member_id"]
    if not member_id_raw.isdigit():
        return web.json_response({"error": "invalid_member_id"}, status=400)
    member_id = int(member_id_raw)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    reason = body.get("reason") if isinstance(body, dict) else None
    if not isinstance(reason, str) or not reason.strip() or len(reason) > MAX_REASON_LENGTH:
        return web.json_response({"error": "invalid_reason"}, status=400)

    moderator = request["moderator"]
    settings = automod_core.get_settings()
    warn = warns_core.add_warn(
        guild.id,
        member_id,
        reason.strip(),
        moderator.id,
        source="manual",
        duration_minutes=settings["manual_warn_duration_minutes"],
    )

    cog = request.app["bot"].get_cog("AutoMod")
    member = guild.get_member(member_id)
    if cog is not None and member is not None:
        await cog.apply_escalation_if_needed(guild, member)

    return web.json_response({
        "warn": warn,
        "active_count": warns_core.get_active_warn_count(guild.id, member_id),
    }, status=201)


@routes.delete("/api/warns/{warn_id}")
@require_dashboard_access
async def warn_delete(request: web.Request) -> web.Response:
    try:
        warn_id = int(request.match_info["warn_id"])
    except ValueError:
        return web.json_response({"error": "invalid_warn_id"}, status=400)

    moderator = request["moderator"]
    if not warns_core.remove_warn(warn_id, moderator.id):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
