from aiohttp import web

import bot.core.timezone_core as timezone_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/timezone")
@require_dashboard_access
async def timezone_get(request: web.Request) -> web.Response:
    return web.json_response(timezone_core.get_settings(request["guild_id"]))


@routes.put("/api/timezone")
@require_dashboard_access
async def timezone_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    code = body.get("code")
    if not isinstance(code, str) or code not in timezone_core.SUPPORTED_TIMEZONES:
        return web.json_response({"error": "invalid_timezone"}, status=400)

    timezone_core.set_timezone(request["guild_id"], code)
    return web.json_response(timezone_core.get_settings(request["guild_id"]))
