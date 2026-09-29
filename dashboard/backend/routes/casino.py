from aiohttp import web

import bot.modules.games.casino_core as casino_core
import bot.modules.games.casino_db as casino_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/casino")
@require_dashboard_access
async def casino_get(request: web.Request) -> web.Response:
    return web.json_response(casino_core.get_settings(request["guild_id"]))


@routes.put("/api/casino")
@require_dashboard_access
async def casino_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    int_checks = (
        ("house_edge_percent", casino_core.DEFAULT_HOUSE_EDGE_PERCENT, 0, casino_core.HOUSE_EDGE_MAX),
        ("cooldown_sec", casino_core.DEFAULT_COOLDOWN_SEC, 0, casino_core.COOLDOWN_SEC_MAX),
        ("min_bet", casino_core.DEFAULT_MIN_BET, 1, casino_core.BET_LIMIT_MAX),
        ("max_bet", casino_core.DEFAULT_MAX_BET, 0, casino_core.BET_LIMIT_MAX),
    )
    values = {}
    for key, default, lo, hi in int_checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    if values["max_bet"] != 0 and values["max_bet"] < values["min_bet"]:
        return web.json_response({"error": "invalid_max_bet"}, status=400)

    loss_roles = body.get("loss_roles", [])
    if not isinstance(loss_roles, list):
        return web.json_response({"error": "invalid_loss_roles"}, status=400)
    
    valid_roles = []
    for r in loss_roles:
        if not isinstance(r, dict):
            continue
        game = r.get("game")
        if game not in ("slots", "bj", "total"):
            continue
        try:
            threshold = int(r.get("threshold", 0))
            if threshold <= 0:
                continue
            role_id = str(r.get("role_id", "")).strip()
            if not role_id:
                continue
            valid_roles.append({
                "game": game,
                "threshold": threshold,
                "role_id": role_id
            })
        except ValueError:
            continue
    values["loss_roles"] = valid_roles

    guild_id = request["guild_id"]
    casino_core.save_config(guild_id, {"enabled": body["enabled"], **values})
    return web.json_response(casino_core.get_settings(guild_id))


@routes.get("/api/casino/leaderboard")
@require_dashboard_access
async def casino_leaderboard(request: web.Request) -> web.Response:
    mode = request.query.get("mode", "total")
    stat_type = request.query.get("type", "losses")
    if mode not in ("slots", "bj", "total"):
        mode = "total"
    if stat_type not in ("wins", "losses"):
        stat_type = "losses"
        
    try:
        page = int(request.query.get("page", "1"))
    except ValueError:
        page = 1
    page = max(1, page)
    
    guild_id = request["guild_id"]
    limit = 1000
    all_rows = casino_db.leaderboard(guild_id, mode, stat_type, limit)
    
    page_size = 50
    total = len(all_rows)
    start = (page - 1) * page_size
    entries = all_rows[start:start+page_size]
    
    guild = request.app["bot"].get_guild(guild_id)
    
    results = []
    for r in entries:
        member = guild.get_member(r["user_id"]) if guild else None
        results.append({
            "user_id": str(r["user_id"]),
            "username": member.display_name if member else str(r["user_id"]),
            "avatar": member.display_avatar.url if member and member.display_avatar else None,
            "slots_losses": r["slots_losses"],
            "slots_wins": r["slots_wins"],
            "bj_losses": r["bj_losses"],
            "bj_wins": r["bj_wins"],
        })
        
    return web.json_response({
        "entries": results,
        "total": total,
        "page": page,
        "page_size": page_size
    })
