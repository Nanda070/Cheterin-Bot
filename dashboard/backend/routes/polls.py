from aiohttp import web

import bot.modules.community.polls_db as polls_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _public_poll(poll: dict) -> dict:
    tallies = polls_db.tallies(poll["id"])
    return {
        "id": poll["id"],
        "guild_id": str(poll["guild_id"]),
        "channel_id": str(poll["channel_id"]),
        "message_id": str(poll["message_id"]) if poll.get("message_id") else None,
        "question": poll["question"],
        "options": poll["options"],
        "ends_at": poll["ends_at"],
        "ended": bool(poll["ended"]),
        "created_by": str(poll["created_by"]) if poll.get("created_by") is not None else None,
        "created_at": poll["created_at"],
        "tallies": tallies,
        "total_votes": sum(tallies),
    }


@routes.get("/api/polls")
@require_dashboard_access
async def polls_list(request: web.Request) -> web.Response:
    polls = polls_db.list_for_guild(request["guild_id"], limit=50)
    return web.json_response({"polls": [_public_poll(p) for p in polls]})


@routes.get("/api/polls/{poll_id}")
@require_dashboard_access
async def polls_get(request: web.Request) -> web.Response:
    try:
        poll_id = int(request.match_info["poll_id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)
    poll = polls_db.get(poll_id)
    if poll is None or poll["guild_id"] != request["guild_id"]:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(_public_poll(poll))


@routes.post("/api/polls/{poll_id}/end")
@require_dashboard_access
async def polls_end(request: web.Request) -> web.Response:
    try:
        poll_id = int(request.match_info["poll_id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)
    poll = polls_db.get(poll_id)
    if poll is None or poll["guild_id"] != request["guild_id"]:
        return web.json_response({"error": "not_found"}, status=404)
    if poll["ended"]:
        return web.json_response(_public_poll(poll))

    cog = request.app["bot"].get_cog("PollsCog")
    if cog is not None and hasattr(cog, "end_poll"):
        await cog.end_poll(poll)
    else:
        polls_db.mark_ended(poll_id)

    updated = polls_db.get(poll_id)
    return web.json_response(_public_poll(updated) if updated else {"ok": True})
