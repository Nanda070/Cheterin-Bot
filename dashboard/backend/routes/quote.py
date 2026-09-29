from aiohttp import web

import bot.modules.utility.quote_core as quote_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/quote")
@require_dashboard_access
async def quote_get(request: web.Request) -> web.Response:
    return web.json_response(quote_core.get_settings(request["guild_id"]))


@routes.put("/api/quote")
@require_dashboard_access
async def quote_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled")
    delete_trigger = body.get("delete_trigger")
    if not isinstance(enabled, bool) or not isinstance(delete_trigger, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    settings = quote_core.save_settings(
        request["guild_id"],
        {
            "enabled": enabled,
            "delete_trigger": delete_trigger,
            "min_length": body.get("min_length", 0),
        },
    )
    return web.json_response(settings)
