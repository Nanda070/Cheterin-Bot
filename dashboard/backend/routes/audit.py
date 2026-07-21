from aiohttp import web

import stats_db

from ..access_middleware import require_dashboard_access

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

    offset = (page - 1) * PAGE_SIZE
    rows = stats_db.audit_list(request["guild_id"], limit=PAGE_SIZE, offset=offset, moderator_id=moderator_id)
    total = stats_db.audit_count(request["guild_id"], moderator_id=moderator_id)

    return web.json_response({
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "entries": [
            {
                "ts": row["ts"],
                "moderator_id": str(row["moderator_id"]),
                "moderator_name": row["moderator_name"],
                "method": row["method"],
                "path": row["path"],
                "action": row["action"],
                "status": row["status"],
                "details": row["details"],
            }
            for row in rows
        ],
    })
