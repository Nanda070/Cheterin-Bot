"""CTD (тикеты) — привилегия основного сервера (Фаза 2b MULTIGUILD_PLAN.md).

Настройки CTD (роль поддержки + канал панели) вынесены из общего `/api/config`
в отдельный роут, доступный только когда активный сервер == мейн-сервер приложения
(`request.app["guild_id"]`). Так CTD не показывается и не редактируется на обычных
серверах. Доступ — Manage Server на мейне (через require_dashboard_access).
"""

from aiohttp import web

import bot.config as bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

CTD_ROLE_KEYS = ["CTD_ROLE_ID"]
CTD_CHANNEL_KEYS = ["CTD_CHANNEL_ID"]
CTD_KEYS = CTD_ROLE_KEYS + CTD_CHANNEL_KEYS


def _require_main_guild(request: web.Request) -> web.Response | None:
    if request["guild_id"] != request.app.get("guild_id"):
        return web.json_response({"error": "not_main_guild"}, status=403)
    return None


@routes.get("/api/ctd")
@require_dashboard_access
async def get_ctd(request: web.Request) -> web.Response:
    guard = _require_main_guild(request)
    if guard is not None:
        return guard
    data = bot_config.load_config(request["guild_id"])
    return web.json_response({key: str(data.get(key) or "") for key in CTD_KEYS})


@routes.put("/api/ctd")
@require_dashboard_access
async def put_ctd(request: web.Request) -> web.Response:
    guard = _require_main_guild(request)
    if guard is not None:
        return guard

    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in CTD_KEYS:
        value = body.get(key, "")
        if not isinstance(value, str):
            return web.json_response({"error": f"invalid_{key.lower()}"}, status=400)

    for key in CTD_ROLE_KEYS:
        raw = body.get(key, "")
        if raw:
            if not raw.isdigit():
                return web.json_response({"error": "invalid_request"}, status=400)
            if guild.get_role(int(raw)) is None:
                return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)

    for key in CTD_CHANNEL_KEYS:
        raw = body.get(key, "")
        if raw:
            if not raw.isdigit():
                return web.json_response({"error": "invalid_request"}, status=400)
            if guild.get_channel(int(raw)) is None:
                return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)

    data = bot_config.load_config(request["guild_id"])
    for key in CTD_KEYS:
        data[key] = body.get(key, "")
    bot_config.save_config(request["guild_id"], data)
    return web.json_response({key: str(data.get(key) or "") for key in CTD_KEYS})
