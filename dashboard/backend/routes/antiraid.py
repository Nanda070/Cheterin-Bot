from aiohttp import web

import antiraid_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/antiraid")
@require_dashboard_access
async def antiraid_get(request: web.Request) -> web.Response:
    return web.json_response(antiraid_core.get_settings(request["guild_id"]))


@routes.put("/api/antiraid")
@require_dashboard_access
async def antiraid_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in ("enabled", "action_lockdown"):
        if not isinstance(body.get(key, False), bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    int_checks = (
        ("join_window_sec", antiraid_core.DEFAULT_JOIN_WINDOW_SEC, 1, antiraid_core.JOIN_WINDOW_SEC_MAX),
        ("join_threshold", antiraid_core.DEFAULT_JOIN_THRESHOLD, 1, antiraid_core.JOIN_THRESHOLD_MAX),
        ("min_account_age_hours", antiraid_core.DEFAULT_MIN_ACCOUNT_AGE_HOURS, 0, antiraid_core.ACCOUNT_AGE_HOURS_MAX),
        ("action_slowmode_sec", antiraid_core.DEFAULT_ACTION_SLOWMODE_SEC, 0, antiraid_core.SLOWMODE_SEC_MAX),
        ("cooldown_minutes", antiraid_core.DEFAULT_COOLDOWN_MINUTES, 0, antiraid_core.COOLDOWN_MINUTES_MAX),
    )
    values = {}
    for key, default, lo, hi in int_checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    guild_id = request["guild_id"]
    antiraid_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "action_lockdown": body.get("action_lockdown", True),
        **values,
    })
    return web.json_response(antiraid_core.get_settings(guild_id))
