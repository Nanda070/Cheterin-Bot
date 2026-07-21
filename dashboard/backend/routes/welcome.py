from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/welcome-settings")
@require_dashboard_access
async def get_welcome_settings(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "channel_enabled": bool(bot_config.get(request["guild_id"], "WELCOME_CHANNEL_ENABLED", True)),
            "dm_enabled": bool(bot_config.get(request["guild_id"], "WELCOME_DM_ENABLED", True)),
        }
    )


@routes.put("/api/welcome-settings")
@require_dashboard_access
async def update_welcome_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_enabled = body.get("channel_enabled")
    dm_enabled = body.get("dm_enabled")
    if not isinstance(channel_enabled, bool) or not isinstance(dm_enabled, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    data = bot_config.load_config(request["guild_id"])
    data["WELCOME_CHANNEL_ENABLED"] = channel_enabled
    data["WELCOME_DM_ENABLED"] = dm_enabled
    bot_config.save_config(request["guild_id"], data)

    return web.json_response({"channel_enabled": channel_enabled, "dm_enabled": dm_enabled})
