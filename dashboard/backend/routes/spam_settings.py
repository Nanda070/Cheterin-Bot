from aiohttp import web

import bot.modules.moderation.spam_core as spam_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/spam-settings")
@require_dashboard_access
async def get_spam_settings(request: web.Request) -> web.Response:
    return web.json_response(spam_core.get_settings(request["guild_id"]))


@routes.put("/api/spam-settings")
@require_dashboard_access
async def update_spam_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    checks = (
        ("limit_with_attachments", spam_core.DEFAULT_LIMIT_WITH_ATTACHMENTS),
        ("limit_without_attachments", spam_core.DEFAULT_LIMIT_WITHOUT_ATTACHMENTS),
    )
    values = {}
    for key, default in checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        if not spam_core.LIMIT_MIN <= value <= spam_core.LIMIT_MAX:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    time_window = body.get("time_window_sec", spam_core.DEFAULT_TIME_WINDOW_SEC)
    if not isinstance(time_window, int) or isinstance(time_window, bool):
        return web.json_response({"error": "invalid_time_window_sec"}, status=400)
    if not spam_core.TIME_WINDOW_MIN <= time_window <= spam_core.TIME_WINDOW_MAX:
        return web.json_response({"error": "invalid_time_window_sec"}, status=400)

    guild_id = request["guild_id"]
    spam_core.save_config(
        guild_id,
        {**values, "time_window_sec": time_window},
    )
    return web.json_response(spam_core.get_settings(guild_id))
