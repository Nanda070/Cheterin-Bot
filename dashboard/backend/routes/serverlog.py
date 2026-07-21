from aiohttp import web

import serverlog

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/serverlog")
@require_dashboard_access
async def serverlog_get(request: web.Request) -> web.Response:
    settings = serverlog.get_settings(request["guild_id"])
    return web.json_response({
        "labels": serverlog.EVENT_TYPES,
        "events": settings["events"],
    })


@routes.put("/api/serverlog")
@require_dashboard_access
async def serverlog_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("events"), dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    events = {}
    for event_type in serverlog.EVENT_TYPES:
        entry = body["events"].get(event_type, {})
        if not isinstance(entry, dict):
            return web.json_response({"error": "invalid_request"}, status=400)
        enabled = entry.get("enabled", False)
        channel_id = entry.get("channel_id", "")
        if not isinstance(enabled, bool):
            return web.json_response({"error": f"invalid_{event_type}"}, status=400)
        if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
            return web.json_response({"error": f"invalid_{event_type}"}, status=400)
        if enabled and not channel_id:
            return web.json_response({"error": f"channel_required_{event_type}"}, status=400)
        events[event_type] = {"enabled": enabled, "channel_id": channel_id}

    guild_id = request["guild_id"]
    serverlog.save_config(guild_id, {"events": events})
    return web.json_response({"labels": serverlog.EVENT_TYPES, "events": serverlog.get_settings(guild_id)["events"]})
