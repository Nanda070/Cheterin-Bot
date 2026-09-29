from aiohttp import web

import bot.modules.community.sticky_roles_core as sticky_roles_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/sticky-roles")
@require_dashboard_access
async def sticky_roles_get(request: web.Request) -> web.Response:
    sticky_roles_core.init()
    return web.json_response(sticky_roles_core.get_settings(request["guild_id"]))


@routes.put("/api/sticky-roles")
@require_dashboard_access
async def sticky_roles_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    tracked = body.get("tracked_role_ids", [])
    ignored = body.get("ignored_role_ids", [])
    if not isinstance(tracked, list) or not all(isinstance(x, str) and x.isdigit() for x in tracked):
        return web.json_response({"error": "invalid_tracked_role_ids"}, status=400)
    if not isinstance(ignored, list) or not all(isinstance(x, str) and x.isdigit() for x in ignored):
        return web.json_response({"error": "invalid_ignored_role_ids"}, status=400)

    guild = request.app["bot"].get_guild(request["guild_id"])
    if guild is not None:
        known = {str(r.id) for r in guild.roles}
        for rid in tracked + ignored:
            if rid not in known:
                return web.json_response({"error": "role_not_found"}, status=404)

    return web.json_response(
        sticky_roles_core.save_settings(
            request["guild_id"],
            enabled=enabled,
            tracked_role_ids=tracked,
            ignored_role_ids=ignored,
        )
    )
