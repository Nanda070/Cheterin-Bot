from aiohttp import web

import events
import events_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

VALID_STATUSES = {"open", "closed"}


def _tournament_count(ev: dict) -> int:
    participants = ev.get("participants", [])
    if ev.get("mode") == "team_code":
        teams = set(p.get("team_code") for p in participants if p.get("team_code"))
        return len(teams)
    return len(participants)


def serialize_event_summary(message_id: str, ev: dict) -> dict:
    if ev.get("type") == "tournament":
        count = _tournament_count(ev)
    else:
        count = sum(len(v) for v in ev.get("votes", {}).values())
    return {
        "message_id": message_id,
        "type": ev.get("type"),
        "title": ev.get("title", ""),
        "status": ev.get("status", "open"),
        "channel_id": str(ev.get("channel_id", "")),
        "count": count,
    }


def _serialize_participants(ev: dict) -> list:
    parts = ev.get("participants", [])
    mode = ev.get("mode", "solo")
    if mode == "solo":
        return [{"user_id": str(p["user_id"]), "ign": p.get("ign") or "—"} for p in parts]
    if mode == "team_captain":
        return [
            {"user_id": str(p["user_id"]), "team_name": p.get("team_name", ""), "members": p.get("members", "")}
            for p in parts
        ]
    teams: dict = {}
    for p in parts:
        teams.setdefault(p.get("team_code"), []).append(p)
    result = []
    for code, members in teams.items():
        captain = next((m for m in members if m.get("is_captain")), members[0] if members else None)
        result.append(
            {
                "team_code": code,
                "team_name": captain.get("team_name", "") if captain else "",
                "members": [
                    {
                        "user_id": str(m["user_id"]),
                        "ign": m.get("ign") or "—",
                        "is_captain": bool(m.get("is_captain")),
                    }
                    for m in members
                ],
            }
        )
    return result


def _serialize_poll_options(ev: dict) -> list:
    votes = ev.get("votes", {})
    opts = ev.get("options", [])
    counts = [0] * len(opts)
    total = 0
    for user_votes in votes.values():
        for v in user_votes:
            if v < len(counts):
                counts[v] += 1
                total += 1
    result = []
    for idx, opt in enumerate(opts):
        c = counts[idx]
        pct = int((c / total * 100) if total > 0 else 0)
        result.append({"label": opt, "votes": c, "percent": pct})
    return result


def serialize_event_detail(message_id: str, ev: dict) -> dict:
    base = {
        "message_id": message_id,
        "type": ev.get("type"),
        "title": ev.get("title", ""),
        "description": ev.get("description", ""),
        "status": ev.get("status", "open"),
        "channel_id": str(ev.get("channel_id", "")),
        "role_reward": str(ev["role_reward"]) if ev.get("role_reward") else None,
    }
    if ev.get("type") == "tournament":
        base["mode"] = ev.get("mode", "solo")
        base["max_limit"] = ev.get("max_limit", 0)
        base["team_size"] = ev.get("team_size", 5)
        base["participants"] = _serialize_participants(ev)
    else:
        base["multi_select"] = ev.get("multi_select", False)
        base["options"] = _serialize_poll_options(ev)
    return base


@routes.get("/api/events")
@require_dashboard_access
async def list_events(request: web.Request) -> web.Response:
    status = request.query.get("status", "open")
    if status not in VALID_STATUSES:
        return web.json_response({"error": "invalid_status"}, status=400)

    data = await events.load_events()
    events_list = [
        serialize_event_summary(message_id, ev)
        for message_id, ev in data.get("events", {}).items()
        if ev.get("status", "open") == status
    ]
    return web.json_response({"events": events_list})


@routes.get("/api/events/{message_id}")
@require_dashboard_access
async def get_event(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    data = await events.load_events()
    ev = data.get("events", {}).get(message_id)
    if ev is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(serialize_event_detail(message_id, ev))


@routes.post("/api/events/{message_id}/close")
@require_dashboard_access
async def close_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    bot = request.app["bot"]
    result = await events_core.close_event(bot, message_id)
    if not result["ok"]:
        return web.json_response({"error": result["error"]}, status=404)
    return web.json_response({"ok": True})


@routes.delete("/api/events/{message_id}")
@require_dashboard_access
async def delete_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    result = await events_core.delete_event(bot, guild, message_id)
    if not result["ok"]:
        return web.json_response({"error": result["error"]}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/events/{message_id}/notify")
@require_dashboard_access
async def notify_event_route(request: web.Request) -> web.Response:
    message_id = request.match_info["message_id"]

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        return web.json_response({"error": "invalid_request"}, status=400)

    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    result = await events_core.notify_participants(bot, guild, message_id, message.strip())
    if not result["ok"]:
        status_code = {"not_found": 404, "no_participants": 400}.get(result["error"], 400)
        return web.json_response({"error": result["error"]}, status=status_code)
    return web.json_response({"ok": True, "success": result["success"], "failed": result["failed"]})
