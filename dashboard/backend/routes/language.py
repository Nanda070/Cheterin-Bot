from aiohttp import web

import language_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/language")
@require_dashboard_access
async def language_get(request: web.Request) -> web.Response:
    return web.json_response(language_core.get_settings(request["guild_id"]))


@routes.put("/api/language")
@require_dashboard_access
async def language_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    code = body.get("code")
    if not isinstance(code, str) or code not in language_core.SUPPORTED_LANGUAGES:
        return web.json_response({"error": "invalid_language"}, status=400)

    language_core.set_language(request["guild_id"], code)
    return web.json_response(language_core.get_settings(request["guild_id"]))
