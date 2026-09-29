"""Guild-scoped idea moderation API."""

from aiohttp import web

import bot.modules.valorant.ideas_core as ideas_core
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _serialize(case: dict, guild) -> dict:
    member = guild.get_member(case["submitter_id"]) if guild else None
    return {**case, "submitter_id": str(case["submitter_id"]), "submitter_display": member.display_name if member else str(case["submitter_id"])}


@routes.get("/api/ideas/settings")
@require_dashboard_access
async def settings_get(request: web.Request) -> web.Response:
    return web.json_response(ideas_core.get_settings(request["guild_id"]))


@routes.put("/api/ideas/settings")
@require_dashboard_access
async def settings_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    guild = request.app["bot"].get_guild(request["guild_id"])
    for key in ("intake_channel_id", "review_channel_id", "channel_id"):
        value = body.get(key, "")
        if not isinstance(value, str) or (value and not value.isdigit()):
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        if value and guild and guild.get_channel(int(value)) is None:
            return web.json_response({"error": "channel_not_found"}, status=404)
    return web.json_response(ideas_core.save_settings(request["guild_id"], body))


@routes.get("/api/ideas/cases")
@require_dashboard_access
async def cases_get(request: web.Request) -> web.Response:
    status = request.query.get("status")
    if status and status not in {"pending", "approved", "denied"}:
        return web.json_response({"error": "invalid_status"}, status=400)
    guild = request.app["bot"].get_guild(request["guild_id"])
    return web.json_response({"cases": [_serialize(case, guild) for case in ideas_core.list_cases(request["guild_id"], status)]})


@routes.post("/api/ideas/cases/{case_id}/decide")
@require_dashboard_access
async def case_decide(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("approved"), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    case = ideas_core.decide_case(request["guild_id"], request.match_info["case_id"], body["approved"], request["moderator"].id)
    if case is None:
        return web.json_response({"error": "not_found_or_decided"}, status=409)
    # Publishing is performed by IdeasCog; its presence is deliberately required
    # so moderation cannot accidentally publish into another guild.
    cog = request.app["bot"].get_cog("IdeasCog")
    if body["approved"] and cog is not None:
        await cog.publish_case(request.app["bot"].get_guild(request["guild_id"]), case)
    return web.json_response({"ok": True})
