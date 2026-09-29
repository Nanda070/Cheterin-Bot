import secrets

from aiohttp import web

import bot.modules.games.brackets as brackets
import bot.modules.community.events as events
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request["guild_id"])


def serialize_bracket_summary(bracket: dict) -> dict:
    return {
        "id": bracket["id"],
        "title": bracket["title"],
        "format": bracket.get("format", brackets.FORMAT_SINGLE),
        "source_event_id": bracket.get("source_event_id"),
        "entry_count": len(bracket.get("entries", [])),
        "created_at": bracket["created_at"],
    }


def _serialize_de_match(match: dict) -> dict:
    return {
        "slot_a": match["slot_a"],
        "slot_b": match["slot_b"],
        "winner": match["winner"] if not match.get("void") else None,
    }


def serialize_bracket_detail(bracket: dict) -> dict:
    result = {
        "id": bracket["id"],
        "title": bracket["title"],
        "format": bracket.get("format", brackets.FORMAT_SINGLE),
        "source_event_id": bracket.get("source_event_id"),
        "entries": bracket.get("entries", []),
        "rounds": bracket.get("rounds", []),
        "share_token": bracket.get("share_token"),
    }
    if "de" in bracket:
        de = bracket["de"]
        result["de"] = {
            "winners": [[_serialize_de_match(m) for m in rnd] for rnd in de["winners"]],
            "losers": [[_serialize_de_match(m) for m in rnd] for rnd in de["losers"]],
            "final": _serialize_de_match(de["final"]),
        }
    if "rr_rounds" in bracket:
        result["rr_rounds"] = bracket["rr_rounds"]
        result["standings"] = brackets.rr_standings(bracket)
    return result


@routes.get("/api/brackets")
@require_dashboard_access
async def list_brackets(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
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
    bracket_format = body.get("format") or brackets.FORMAT_SINGLE

    if not title:
        return web.json_response({"error": "invalid_request"}, status=400)
    if bracket_format not in brackets.FORMATS:
        return web.json_response({"error": "invalid_format"}, status=400)
    if len(entries) < 2:
        return web.json_response({"error": "not_enough_entries"}, status=400)
    if bracket_format == brackets.FORMAT_ROUND_ROBIN and len(entries) > 20:
        return web.json_response({"error": "too_many_entries"}, status=400)

    if source_event_id:
        events_data = events.load_events(request["guild_id"])
        ev = events_data.get("events", {}).get(str(source_event_id))
        if ev is None or ev.get("type") != "tournament":
            return web.json_response({"error": "event_not_found"}, status=404)
        guild = _get_guild_or_none(request)
        expected = brackets.extract_entries_from_event(ev, guild)
        if sorted(entries) != sorted(expected):
            return web.json_response({"error": "entries_mismatch"}, status=400)

    moderator = request["moderator"]
    bracket = brackets.create_bracket_v2(
        title, entries, str(source_event_id) if source_event_id else None, moderator.id, bracket_format
    )
    data = brackets.load_brackets(request["guild_id"])
    data[bracket["id"]] = bracket
    brackets.save_brackets(request["guild_id"], data)
    return web.json_response(serialize_bracket_detail(bracket), status=201)


@routes.get("/api/brackets/entries-from-event/{event_id}")
@require_dashboard_access
async def entries_from_event(request: web.Request) -> web.Response:
    events_data = events.load_events(request["guild_id"])
    ev = events_data.get("events", {}).get(request.match_info["event_id"])
    if ev is None or ev.get("type") != "tournament":
        return web.json_response({"error": "event_not_found"}, status=404)
    guild = _get_guild_or_none(request)
    return web.json_response({"entries": brackets.extract_entries_from_event(ev, guild)})


@routes.get("/api/brackets/{id}")
@require_dashboard_access
async def get_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    return web.json_response(serialize_bracket_detail(bracket))


@routes.delete("/api/brackets/{id}")
@require_dashboard_access
async def delete_bracket(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
    bracket_id = request.match_info["id"]
    if bracket_id not in data:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    del data[bracket_id]
    brackets.save_brackets(request["guild_id"], data)
    return web.json_response({"ok": True})


@routes.post("/api/brackets/{id}/matches/{round_index}/{match_index}/winner")
@require_dashboard_access
async def set_match_winner(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)

    try:
        round_index = int(request.match_info["round_index"])
        match_index = int(request.match_info["match_index"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    winner = body.get("winner")
    segment = body.get("segment") or "W"
    bracket_format = bracket.get("format", brackets.FORMAT_SINGLE)

    if bracket_format == brackets.FORMAT_ROUND_ROBIN:
        if winner not in ("a", "b", "draw", None):
            return web.json_response({"error": "invalid_request"}, status=400)
        if not brackets.set_winner_rr(bracket, round_index, match_index, winner):
            return web.json_response({"error": "match_not_found"}, status=404)
        brackets.save_brackets(request["guild_id"], data)
        return web.json_response(serialize_bracket_detail(bracket))

    if winner not in ("a", "b"):
        return web.json_response({"error": "invalid_request"}, status=400)

    if bracket_format == brackets.FORMAT_DOUBLE:
        if segment not in ("W", "L", "F"):
            return web.json_response({"error": "invalid_request"}, status=400)
        if not brackets.set_winner_de(bracket, segment, round_index, match_index, winner):
            return web.json_response({"error": "match_not_ready"}, status=400)
        brackets.save_brackets(request["guild_id"], data)
        return web.json_response(serialize_bracket_detail(bracket))

    rounds = bracket.get("rounds", [])
    if round_index < 0 or round_index >= len(rounds):
        return web.json_response({"error": "match_not_found"}, status=404)
    if match_index < 0 or match_index >= len(rounds[round_index]):
        return web.json_response({"error": "match_not_found"}, status=404)

    match = rounds[round_index][match_index]
    if match["slot_a"] is None or match["slot_b"] is None:
        return web.json_response({"error": "match_not_ready"}, status=400)

    brackets.set_winner(bracket, round_index, match_index, winner)
    brackets.save_brackets(request["guild_id"], data)
    return web.json_response(serialize_bracket_detail(bracket))


@routes.post("/api/brackets/{id}/share")
@require_dashboard_access
async def enable_share(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    token = secrets.token_urlsafe(32)
    bracket["share_token"] = token
    brackets.save_brackets(request["guild_id"], data)
    return web.json_response({"share_token": token})


@routes.delete("/api/brackets/{id}/share")
@require_dashboard_access
async def disable_share(request: web.Request) -> web.Response:
    data = brackets.load_brackets(request["guild_id"])
    bracket = data.get(request.match_info["id"])
    if bracket is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    bracket["share_token"] = None
    brackets.save_brackets(request["guild_id"], data)
    return web.json_response({"ok": True})


@routes.get("/api/public/brackets/{token}")
async def get_public_bracket(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    found = brackets.find_by_share_token(token)
    if found is None:
        return web.json_response({"error": "bracket_not_found"}, status=404)
    _guild_id, bracket = found
    return web.json_response(serialize_bracket_detail(bracket))
