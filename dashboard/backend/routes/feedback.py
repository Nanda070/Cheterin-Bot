from aiohttp import web

import feedback_core
import feedback_menu
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

VALID_STATUSES = {"pending", "approved", "denied"}


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def serialize_case_summary(case_id: str, case_data: dict, guild) -> dict:
    category_key = case_data["category_key"]
    config = feedback_menu.get_feedback_categories().get(category_key, {})
    submitter_id = case_data["submitter_id"]
    member = guild.get_member(submitter_id) if guild else None
    return {
        "case_id": case_id,
        "category_key": category_key,
        "category_title": config.get("case_title", category_key),
        "submitter_id": str(submitter_id),
        "submitter_display": member.display_name if member else str(submitter_id),
        "status": case_data["status"],
        "created_at": case_data.get("created_at"),
    }


def serialize_case_detail(case_id: str, case_data: dict, guild) -> dict:
    category_key = case_data["category_key"]
    config = feedback_menu.get_feedback_categories().get(category_key, {})
    submitter_id = case_data["submitter_id"]
    member = guild.get_member(submitter_id) if guild else None
    answers = case_data.get("answers", {})
    fields = [
        {"key": f["key"], "label": f["label"], "value": answers.get(f["key"], "—")}
        for f in config.get("fields", [])
    ]
    return {
        "case_id": case_id,
        "category_key": category_key,
        "category_title": config.get("case_title", category_key),
        "submitter_id": str(submitter_id),
        "submitter_display": member.display_name if member else str(submitter_id),
        "status": case_data["status"],
        "created_at": case_data.get("created_at"),
        "fields": fields,
        "public_channel_id": str(case_data["public_channel_id"]) if case_data.get("public_channel_id") else None,
        "public_message_id": str(case_data["public_message_id"]) if case_data.get("public_message_id") else None,
        "thread_id": str(case_data["thread_id"]) if case_data.get("thread_id") else None,
    }


@routes.get("/api/feedback-cases")
@require_dashboard_access
async def list_feedback_cases(request: web.Request) -> web.Response:
    status = request.query.get("status")
    if status and status not in VALID_STATUSES:
        return web.json_response({"error": "invalid_status"}, status=400)

    guild = _get_guild_or_none(request)
    bot = request.app["bot"]
    cases = [
        serialize_case_summary(case_id, case_data, guild)
        for case_id, case_data in bot.feedback_cases.items()
        if status is None or case_data.get("status") == status
    ]
    cases.sort(key=lambda c: c["created_at"] or "", reverse=True)

    return web.json_response({"cases": cases})


@routes.get("/api/feedback-cases/{case_id}")
@require_dashboard_access
async def get_feedback_case(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    case_id = request.match_info["case_id"]
    case_data = bot.feedback_cases.get(case_id)
    if case_data is None:
        return web.json_response({"error": "not_found"}, status=404)

    guild = _get_guild_or_none(request)
    return web.json_response(serialize_case_detail(case_id, case_data, guild))


@routes.post("/api/feedback-cases/{case_id}/decide")
@require_dashboard_access
async def decide_feedback_case(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    bot = request.app["bot"]
    case_id = request.match_info["case_id"]

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    approved = body.get("approved")
    if not isinstance(approved, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    result = await feedback_core.decide_case(
        bot,
        guild,
        case_id,
        approved,
        decided_by_id=moderator.id,
        decided_by_mention=f"<@{moderator.id}>",
    )
    if not result["ok"]:
        status_code = {"not_found": 404, "already_decided": 409}.get(result["error"], 400)
        return web.json_response({"error": result["error"]}, status=status_code)

    return web.json_response({"ok": True})
