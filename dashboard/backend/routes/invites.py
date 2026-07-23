from aiohttp import web

import invites_core
import invites_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/invites")
@require_dashboard_access
async def invites_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    settings = invites_core.get_settings(guild_id)
    return web.json_response({
        **settings,
        "stats": [
            {"inviter_id": str(r["inviter_id"]), "joins": r["joins"]}
            for r in invites_db.inviter_stats(guild_id)
        ],
        "recent_joins": [
            {
                "invitee_id": str(r["invitee_id"]),
                "inviter_id": str(r["inviter_id"]) if r["inviter_id"] is not None else None,
                "code": r["code"],
                "joined_at": r["joined_at"],
            }
            for r in invites_db.recent_joins(guild_id, 50)
        ],
    })


@routes.put("/api/invites")
@require_dashboard_access
async def invites_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    welcome_mention = body.get("welcome_mention", False)
    log_channel_id = body.get("log_channel_id", "")

    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if not isinstance(welcome_mention, bool):
        return web.json_response({"error": "invalid_welcome_mention"}, status=400)
    if not isinstance(log_channel_id, str) or (log_channel_id and not log_channel_id.isdigit()):
        return web.json_response({"error": "invalid_log_channel_id"}, status=400)

    settings = invites_core.save_settings(
        request["guild_id"],
        enabled=enabled,
        welcome_mention=welcome_mention,
        log_channel_id=log_channel_id,
    )
    return web.json_response(settings)
