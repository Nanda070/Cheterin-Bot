from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


@routes.get("/api/auto-roles")
@require_dashboard_access
async def get_auto_roles(request: web.Request) -> web.Response:
    role_ids = bot_config.get("AUTO_ROLE_IDS", [])
    return web.json_response({"role_ids": [str(r) for r in role_ids]})


@routes.put("/api/auto-roles")
@require_dashboard_access
async def update_auto_roles(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    role_ids_raw = body.get("role_ids")
    if not isinstance(role_ids_raw, list):
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        role_ids = [int(r) for r in role_ids_raw]
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)

    data = bot_config.load_config()
    data["AUTO_ROLE_IDS"] = [str(r) for r in role_ids]
    bot_config.save_config(data)

    return web.json_response({"role_ids": [str(r) for r in role_ids]})
