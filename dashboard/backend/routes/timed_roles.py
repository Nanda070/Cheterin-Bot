from aiohttp import web

import bot.modules.community.timed_roles_db as timed_roles_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/timed-roles")
@require_dashboard_access
async def timed_roles_list(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    guild = request.app["bot"].get_guild(guild_id)
    rows = []
    for row in timed_roles_db.list_for_guild(guild_id):
        member = guild.get_member(row["user_id"]) if guild else None
        role = guild.get_role(row["role_id"]) if guild else None
        rows.append({
            "id": row["id"],
            "user_id": str(row["user_id"]),
            "display_name": member.display_name if member else str(row["user_id"]),
            "role_id": str(row["role_id"]),
            "role_name": role.name if role else str(row["role_id"]),
            "expires_at": row["expires_at"],
            "created_at": row["created_at"],
        })
    return web.json_response({"timed_roles": rows})


@routes.delete("/api/timed-roles/{row_id}")
@require_dashboard_access
async def timed_roles_delete(request: web.Request) -> web.Response:
    try:
        row_id = int(request.match_info["row_id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)

    guild_id = request["guild_id"]
    existing = {r["id"]: r for r in timed_roles_db.list_for_guild(guild_id)}
    row = existing.get(row_id)
    if row is None:
        return web.json_response({"error": "not_found"}, status=404)

    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild:
        member = guild.get_member(row["user_id"])
        role = guild.get_role(row["role_id"])
        if member and role and role in member.roles:
            try:
                await member.remove_roles(role, reason="timed role removed via dashboard")
            except Exception:
                pass

    timed_roles_db.remove(row_id)
    return web.json_response({"ok": True})
