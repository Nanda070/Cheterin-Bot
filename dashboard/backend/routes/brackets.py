from aiohttp import web

import brackets
import events
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def serialize_bracket_summary(bracket: dict) -> dict:
    return {
        "id": bracket["id"],
        "title": bracket["title"],
        "source_event_id": bracket.get("source_event_id"),
        "entry_count": len(bracket.get("entries", [])),
        "created_at": bracket["created_at"],
    }


def serialize_bracket_detail(bracket: dict) -> dict:
    return {
        "id": bracket["id"],
        "title": bracket["title"],
        "source_event_id": bracket.get("source_event_id"),
        "entries": bracket.get("entries", []),
        "rounds": bracket.get("rounds", []),
        "share_token": bracket.get("share_token"),
    }


@routes.get("/api/brackets")
@require_dashboard_access
async def list_brackets(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    return web.json_response({"brackets": [serialize_bracket_summary(b) for b in data.values()]})


@routes.post("/api/brackets")
@require_dashboard_access
async def create_bracket_route(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    title = (body.get("title") or "").strip()
    entries = body.get("entries") or []
    source_event_id = body.get("source_event_id")

    if not title:
        return web.json_response({"error": "invalid_request"}, status=400)
    if len(entries) < 2:
        return web.json_response({"error": "not_enough_entries"}, status=400)

    if source_event_id:
        events_data = await events.load_events()
        ev = events_data.get("events", {}).get(str(source_event_id))
        if ev is None or ev.get("type") != "tournament":
            return web.json_response({"error": "event_not_found"}, status=404)
        guild = _get_guild_or_none(request)
        expected = brackets.extract_entries_from_event(ev, guild)
        if sorted(entries) != sorted(expected):
            return web.json_response({"error": "entries_mismatch"}, status=400)

    moderator = request["moderator"]
    bracket = brackets.create_bracket(
        title, entries, str(source_event_id) if source_event_id else None, moderator.id
    )
    data = brackets.load_brackets()
    data[bracket["id"]] = bracket
    brackets.save_brackets(data)
    return web.json_response(serialize_bracket_detail(bracket), status=201)


@routes.get("/api/brackets/entries-from-event/{event_id}")
@require_dashboard_access
async def entries_from_event(request: web.Request) -> web.Response:
    events_data = await events.load_events()
    ev = events_data.get("events", {}).get(request.match_info["event_id"])
    if ev is None or ev.get("type") != "tournament":
        return web.json_response({"error": "event_not_found"}, status=404)
    guild = _get_guild_or_none(request)
    return web.json_response({"entries": brackets.extract_entries_from_event(ev, guild)})


@routes.get("/api/brackets/{id}")
@require_dashboard_access
async def get_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    return web.json_response(serialize_bracket_detail(bracket))


@routes.delete("/api/brackets/{id}")
@require_dashboard_access
async def delete_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets()
    bracket_id = request.match_info["id"]
    if bracket_id not in data:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    del data[bracket_id]
    brackets.save_brackets(data)
    return web.json_response({"ok": True})
