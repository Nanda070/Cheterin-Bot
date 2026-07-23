from aiohttp import web

import sticky_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/sticky")
@require_dashboard_access
async def sticky_get(request: web.Request) -> web.Response:
    return web.json_response(sticky_core.get_settings(request["guild_id"]))


@routes.put("/api/sticky/settings")
@require_dashboard_access
async def sticky_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    return web.json_response(sticky_core.update_enabled(request["guild_id"], body["enabled"]))


@routes.post("/api/sticky")
@require_dashboard_access
async def sticky_upsert(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_id = body.get("channel_id", "")
    content = body.get("content", "")
    enabled = body.get("enabled", True)
    sticky_id = body.get("id")

    if not isinstance(channel_id, str) or not channel_id.isdigit():
        return web.json_response({"error": "invalid_channel_id"}, status=400)
    if not isinstance(content, str) or not content.strip() or len(content) > sticky_core.MAX_CONTENT_LEN:
        return web.json_response({"error": "invalid_content"}, status=400)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if sticky_id is not None and not isinstance(sticky_id, str):
        return web.json_response({"error": "invalid_id"}, status=400)

    result = sticky_core.upsert_sticky(
        request["guild_id"],
        channel_id=channel_id,
        content=content.strip(),
        enabled=enabled,
        sticky_id=sticky_id,
    )
    if result is None:
        if sticky_id:
            return web.json_response({"error": "not_found"}, status=404)
        return web.json_response({"error": "limit_reached"}, status=409)
    return web.json_response(result, status=201 if not sticky_id else 200)


@routes.delete("/api/sticky/{sticky_id}")
@require_dashboard_access
async def sticky_delete(request: web.Request) -> web.Response:
    if not sticky_core.delete_sticky(request["guild_id"], request.match_info["sticky_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/sticky/{sticky_id}/test")
@require_dashboard_access
async def sticky_test(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    sticky = sticky_core.get_sticky(guild_id, request.match_info["sticky_id"])
    if sticky is None:
        return web.json_response({"error": "not_found"}, status=404)
    if not sticky["enabled"]:
        return web.json_response({"error": "sticky_disabled"}, status=400)

    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel = guild.get_channel(int(sticky["channel_id"]))
    except (TypeError, ValueError):
        channel = None
    if channel is None or not hasattr(channel, "send"):
        return web.json_response({"error": "channel_not_found"}, status=404)

    cog = bot.get_cog("StickyCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        ok = await cog.refresh_sticky(channel, sticky)
    except Exception:
        return web.json_response({"error": "send_failed"}, status=502)
    if not ok:
        return web.json_response({"error": "send_failed"}, status=502)
    return web.json_response({"ok": True})
