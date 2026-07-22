from aiohttp import web

import tempban_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/tempban-settings")
@require_dashboard_access
async def get_tempban_settings(request: web.Request) -> web.Response:
    return web.json_response(tempban_core.get_settings(request["guild_id"]))


@routes.put("/api/tempban-settings")
@require_dashboard_access
async def update_tempban_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    dm_enabled = body.get("dm_enabled")
    log_enabled = body.get("log_enabled")
    if not isinstance(dm_enabled, bool) or not isinstance(log_enabled, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    guild_id = request["guild_id"]
    tempban_core.save_settings(
        guild_id,
        {
            "dm_enabled": dm_enabled,
            "dm_message": str(body.get("dm_message") or ""),
            "log_enabled": log_enabled,
            "unban_reason": str(body.get("unban_reason") or ""),
        },
    )
    return web.json_response(tempban_core.get_settings(guild_id))
