from aiohttp import web

import bot.modules.valorant.valchecker_core as valchecker_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/valchecker")
@require_dashboard_access
async def valchecker_get(request: web.Request) -> web.Response:
    return web.json_response(valchecker_core.get_settings(request["guild_id"]))


@routes.put("/api/valchecker")
@require_dashboard_access
async def valchecker_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    match_channel_id = body.get("match_channel_id", "")
    if not isinstance(match_channel_id, str):
        return web.json_response({"error": "invalid_channel"}, status=400)
    ch_err = valchecker_core.validate_channel_id(match_channel_id, required=False)
    if ch_err:
        return web.json_response({"error": ch_err}, status=400)

    alert_channel_id = body.get("alert_channel_id", "")
    if not isinstance(alert_channel_id, str):
        return web.json_response({"error": "invalid_channel"}, status=400)
    alert_err = valchecker_core.validate_channel_id(alert_channel_id, required=False)
    if alert_err:
        return web.json_response({"error": alert_err}, status=400)

    poll = body.get("poll_interval_sec", valchecker_core.DEFAULT_POLL_INTERVAL_SEC)
    validated = valchecker_core.validate_poll_interval(poll)
    if validated is None:
        return web.json_response({"error": "invalid_poll_interval"}, status=400)

    settings = valchecker_core.save_settings(request["guild_id"], {
        "enabled": enabled,
        "match_channel_id": match_channel_id,
        "alert_channel_id": alert_channel_id,
        "poll_interval_sec": validated,
    })
    return web.json_response(settings)
