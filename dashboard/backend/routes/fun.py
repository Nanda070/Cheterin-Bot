from aiohttp import web

import fun_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/fun")
@require_dashboard_access
async def fun_get(request: web.Request) -> web.Response:
    return web.json_response(fun_core.get_settings())


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

    fun_core.save_config({
        "enabled": body["enabled"],
        "roulette_timeout_minutes": timeout_minutes,
        "roulette_cooldown_sec": cooldown_sec,
    })
    return web.json_response(fun_core.get_settings())
