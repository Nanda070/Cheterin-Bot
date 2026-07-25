from aiohttp import web

import verification_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/verification")
@require_dashboard_access
async def verification_get(request: web.Request) -> web.Response:
    return web.json_response(verification_core.get_settings(request["guild_id"]))


@routes.put("/api/verification")
@require_dashboard_access
async def verification_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in ("enabled", "rules_consent_enabled", "reverify_enabled"):
        if not isinstance(body.get(key, False), bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    # Строки, не числа: Discord ID (snowflake) превышает Number.MAX_SAFE_INTEGER
    # во фронтенде — числом его передавать нельзя, значение тихо портится при вводе.
    values = {}
    for key in ("unverified_role_id", "verified_role_id"):
        value = body.get(key, "")
        if not isinstance(value, str) or (value and not value.isdigit()):
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    welcome_text = body.get("welcome_text", verification_core.DEFAULT_WELCOME_TEXT)
    if not isinstance(welcome_text, str) or not 1 <= len(welcome_text.strip()) <= 1000:
        return web.json_response({"error": "invalid_welcome_text"}, status=400)

    reverify_days = body.get("reverify_days", verification_core.DEFAULT_REVERIFY_DAYS)
    if isinstance(reverify_days, bool) or not isinstance(reverify_days, (int, float)):
        return web.json_response({"error": "invalid_reverify_days"}, status=400)
    reverify_days = int(reverify_days)
    if not (
        verification_core.MIN_REVERIFY_DAYS
        <= reverify_days
        <= verification_core.MAX_REVERIFY_DAYS
    ):
        return web.json_response({"error": "invalid_reverify_days"}, status=400)

    guild_id = request["guild_id"]
    verification_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "welcome_text": welcome_text.strip(),
        "rules_consent_enabled": body.get("rules_consent_enabled", False),
        "reverify_enabled": body.get("reverify_enabled", False),
        "reverify_days": reverify_days,
        **values,
    })
    return web.json_response(verification_core.get_settings(guild_id))
