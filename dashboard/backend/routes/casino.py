from aiohttp import web

import casino_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/casino")
@require_dashboard_access
async def casino_get(request: web.Request) -> web.Response:
    return web.json_response(casino_core.get_settings())


@routes.put("/api/casino")
@require_dashboard_access
async def casino_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    int_checks = (
        ("house_edge_percent", casino_core.DEFAULT_HOUSE_EDGE_PERCENT, 0, casino_core.HOUSE_EDGE_MAX),
        ("cooldown_sec", casino_core.DEFAULT_COOLDOWN_SEC, 0, casino_core.COOLDOWN_SEC_MAX),
        ("min_bet", casino_core.DEFAULT_MIN_BET, 1, casino_core.BET_LIMIT_MAX),
        ("max_bet", casino_core.DEFAULT_MAX_BET, 0, casino_core.BET_LIMIT_MAX),
    )
    values = {}
    for key, default, lo, hi in int_checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    if values["max_bet"] != 0 and values["max_bet"] < values["min_bet"]:
        return web.json_response({"error": "invalid_max_bet"}, status=400)

    casino_core.save_config({"enabled": body["enabled"], **values})
    return web.json_response(casino_core.get_settings())
