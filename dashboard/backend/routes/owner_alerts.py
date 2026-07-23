from aiohttp import web

import owner_alerts_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/owner-alerts")
@require_dashboard_access
async def owner_alerts_get(request: web.Request) -> web.Response:
    return web.json_response(owner_alerts_core.get_settings(request["guild_id"]))


@routes.put("/api/owner-alerts")
@require_dashboard_access
async def owner_alerts_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in (
        "enabled",
        "notify_dm",
        "alert_missing_perms",
        "alert_mass_ban",
        "alert_module_errors",
    ):
        if key in body and not isinstance(body[key], bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    channel_id = body.get("channel_id", "")
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel_id"}, status=400)

    for key in ("mass_ban_threshold", "mass_ban_window_sec", "module_error_threshold"):
        if key in body:
            value = body[key]
            if not isinstance(value, int) or isinstance(value, bool):
                return web.json_response({"error": f"invalid_{key}"}, status=400)

    return web.json_response(owner_alerts_core.save_settings(request["guild_id"], body))
