from aiohttp import web

import bot.core.stats_db as stats_db

from ..access_middleware import require_dashboard_access
from ..audit_middleware import normalize_stored_action

routes = web.RouteTableDef()

PAGE_SIZE = 50


@routes.get("/api/audit")
@require_dashboard_access
async def audit_list(request: web.Request) -> web.Response:
    try:
        page = max(1, int(request.query.get("page", "1")))
    except ValueError:
        page = 1

    moderator_id = None
    raw = request.query.get("moderator", "")
    if raw:
        try:
            moderator_id = int(raw)
        except ValueError:
            return web.json_response({"error": "invalid_request"}, status=400)

    search = (request.query.get("q") or "").strip() or None

    offset = (page - 1) * PAGE_SIZE
    guild_id = request["guild_id"]
    rows = stats_db.audit_list(
        guild_id, limit=PAGE_SIZE, offset=offset, moderator_id=moderator_id, search=search
    )
    total = stats_db.audit_count(guild_id, moderator_id=moderator_id, search=search)
    moderators = stats_db.audit_moderators(guild_id)

    return web.json_response({
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "moderators": [
            {"id": str(row["moderator_id"]), "name": row["moderator_name"]}
            for row in moderators
        ],
        "entries": [
            {
                "ts": row["ts"],
                "moderator_id": str(row["moderator_id"]),
                "moderator_name": row["moderator_name"],
                "method": row["method"],
                "path": row["path"],
                "action": normalize_stored_action(row["action"]),
                "status": row["status"],
                "details": row["details"],
            }
            for row in rows
        ],
    })
