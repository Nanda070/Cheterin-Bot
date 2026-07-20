from aiohttp import web

import wordle_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/wordle")
@require_dashboard_access
async def wordle_get(request: web.Request) -> web.Response:
    return web.json_response(wordle_core.get_settings())


@routes.put("/api/wordle")
@require_dashboard_access
async def wordle_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    # Строка, не число: Discord ID (snowflake) превышает Number.MAX_SAFE_INTEGER
    # во фронтенде — числом его передавать нельзя, значение тихо портится при вводе.
    channel_id = body.get("channel_id", "")
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel_id"}, status=400)

    announce_time = body.get("announce_time", wordle_core.DEFAULT_ANNOUNCE_TIME)
    if not isinstance(announce_time, str) or not wordle_core.is_valid_announce_time(announce_time):
        return web.json_response({"error": "invalid_announce_time"}, status=400)

    wordle_core.save_config({
        "enabled": body["enabled"],
        "channel_id": channel_id,
        "announce_time": announce_time,
    })
    return web.json_response(wordle_core.get_settings())
