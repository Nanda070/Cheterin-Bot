from aiohttp import web

import starboard_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/starboard")
@require_dashboard_access
async def starboard_get(request: web.Request) -> web.Response:
    return web.json_response(starboard_core.get_settings(request["guild_id"]))


@routes.put("/api/starboard")
@require_dashboard_access
async def starboard_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    channel_id = body.get("channel_id", "")
    ch_err = starboard_core.validate_channel_id(channel_id, required=enabled)
    if ch_err:
        return web.json_response({"error": ch_err}, status=400)

    emoji = starboard_core.validate_emoji(body.get("emoji", starboard_core.DEFAULT_EMOJI))
    if emoji is None:
        return web.json_response({"error": "invalid_emoji"}, status=400)

    threshold = starboard_core.validate_threshold(
        body.get("threshold", starboard_core.DEFAULT_THRESHOLD)
    )
    if threshold is None:
        return web.json_response({"error": "invalid_threshold"}, status=400)

    self_star = body.get("self_star", False)
    ignore_nsfw = body.get("ignore_nsfw", False)
    if not isinstance(self_star, bool):
        return web.json_response({"error": "invalid_self_star"}, status=400)
    if not isinstance(ignore_nsfw, bool):
        return web.json_response({"error": "invalid_ignore_nsfw"}, status=400)

    settings = starboard_core.save_config(request["guild_id"], {
        "enabled": enabled,
        "channel_id": channel_id,
        "emoji": emoji,
        "threshold": threshold,
        "self_star": self_star,
        "ignore_nsfw": ignore_nsfw,
    })
    return web.json_response(settings)
