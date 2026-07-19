from aiohttp import web

import verification_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/verification")
@require_dashboard_access
async def verification_get(request: web.Request) -> web.Response:
    return web.json_response(verification_core.get_settings())


@routes.put("/api/verification")
@require_dashboard_access
async def verification_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    values = {}
    for key in ("unverified_role_id", "verified_role_id"):
        value = body.get(key, 0)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    welcome_text = body.get("welcome_text", verification_core.DEFAULT_WELCOME_TEXT)
    if not isinstance(welcome_text, str) or not 1 <= len(welcome_text.strip()) <= 1000:
        return web.json_response({"error": "invalid_welcome_text"}, status=400)

    verification_core.save_config({
        "enabled": body["enabled"],
        "welcome_text": welcome_text.strip(),
        **values,
    })
    return web.json_response(verification_core.get_settings())
