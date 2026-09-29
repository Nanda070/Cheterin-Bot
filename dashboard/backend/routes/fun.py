from aiohttp import web

import bot.modules.games.fun_core as fun_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/fun")
@require_dashboard_access
async def fun_get(request: web.Request) -> web.Response:
    return web.json_response(fun_core.get_settings(request["guild_id"]))


@routes.put("/api/fun")
@require_dashboard_access
async def fun_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    timeout_minutes = body.get("roulette_timeout_minutes", fun_core.DEFAULT_ROULETTE_TIMEOUT_MINUTES)
    if (
        not isinstance(timeout_minutes, int)
        or isinstance(timeout_minutes, bool)
        or not 0 <= timeout_minutes <= fun_core.TIMEOUT_MINUTES_MAX
    ):
        return web.json_response({"error": "invalid_roulette_timeout_minutes"}, status=400)

    cooldown_sec = body.get("roulette_cooldown_sec", fun_core.DEFAULT_ROULETTE_COOLDOWN_SEC)
    if (
        not isinstance(cooldown_sec, int)
        or isinstance(cooldown_sec, bool)
        or not 0 <= cooldown_sec <= fun_core.COOLDOWN_SEC_MAX
    ):
        return web.json_response({"error": "invalid_roulette_cooldown_sec"}, status=400)

    if not isinstance(body.get("auto_emoji_enabled", False), bool):
        return web.json_response({"error": "invalid_auto_emoji_enabled"}, status=400)

    auto_emoji_checks = (
        ("auto_emoji_chance_percent", fun_core.DEFAULT_AUTO_EMOJI_CHANCE_PERCENT, 1, 100),
        ("auto_emoji_min_interval_sec", fun_core.DEFAULT_AUTO_EMOJI_MIN_INTERVAL_SEC, 0, fun_core.AUTO_EMOJI_MIN_INTERVAL_MAX),
        ("auto_emoji_remove_after_sec", fun_core.DEFAULT_AUTO_EMOJI_REMOVE_AFTER_SEC, 0, fun_core.AUTO_EMOJI_REMOVE_AFTER_MAX),
    )
    auto_emoji_values = {}
    for key, default, lo, hi in auto_emoji_checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        auto_emoji_values[key] = value

    guild_id = request["guild_id"]
    fun_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "roulette_timeout_minutes": timeout_minutes,
        "roulette_cooldown_sec": cooldown_sec,
        "auto_emoji_enabled": body.get("auto_emoji_enabled", False),
        **auto_emoji_values,
    })
    return web.json_response(fun_core.get_settings(guild_id))
