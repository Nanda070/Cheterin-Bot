from aiohttp import web

import feedback_categories
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
        status_code = {"not_found": 404, "already_decided": 409, "category_deleted": 409}.get(result["error"], 400)
        return web.json_response({"error": result["error"]}, status=status_code)

    return web.json_response({"ok": True})


def _validate_category_relations(spec: dict, guild) -> web.Response | None:
    """Discord-existence checks. Must run AFTER validate_category_spec."""
    try:
        channel_id = int(spec.get("channel_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_channel(channel_id) is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    for role_id_raw in spec.get("review_role_ids") or []:
        try:
            role_id = int(role_id_raw)
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
        if guild.get_role(role_id) is None:
            return web.json_response({"error": "role_not_found"}, status=404)
    return None


def serialize_category(key: str, entry: dict) -> dict:
    return {"key": key, **entry}


@routes.get("/api/feedback-categories")
@require_dashboard_access
async def list_feedback_categories(request: web.Request) -> web.Response:
    categories = feedback_categories.load_categories()
    return web.json_response(
        {"categories": [serialize_category(key, entry) for key, entry in categories.items()]}
    )


@routes.post("/api/feedback-categories")
@require_dashboard_access
async def create_feedback_category(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    categories = feedback_categories.load_categories()
    error = feedback_categories.validate_category_spec(body, categories, existing_key=None)
    if error:
        status_code = 409 if error in ("key_taken", "case_prefix_taken") else 400
        return web.json_response({"error": error}, status=status_code)

    error_response = _validate_category_relations(body, guild)
    if error_response:
        return error_response

    key = body["key"]
    entry = {k: v for k, v in body.items() if k != "key"}
    categories[key] = entry
    feedback_categories.save_categories(categories)

    return web.json_response(serialize_category(key, entry), status=201)


@routes.put("/api/feedback-categories/{category_key}")
@require_dashboard_access
async def update_feedback_category(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    category_key = request.match_info["category_key"]
    categories = feedback_categories.load_categories()
    if category_key not in categories:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    spec = {**body, "key": category_key}
    error = feedback_categories.validate_category_spec(spec, categories, existing_key=category_key)
    if error:
        status_code = 409 if error in ("key_taken", "case_prefix_taken") else 400
        return web.json_response({"error": error}, status=status_code)

    error_response = _validate_category_relations(spec, guild)
    if error_response:
        return error_response

    entry = {k: v for k, v in body.items() if k != "key"}
    categories[category_key] = entry
    feedback_categories.save_categories(categories)

    return web.json_response(serialize_category(category_key, entry))


@routes.delete("/api/feedback-categories/{category_key}")
@require_dashboard_access
async def delete_feedback_category(request: web.Request) -> web.Response:
    category_key = request.match_info["category_key"]
    categories = feedback_categories.load_categories()
    if category_key not in categories:
        return web.json_response({"error": "not_found"}, status=404)

    del categories[category_key]
    feedback_categories.save_categories(categories)

    bot = request.app["bot"]
    removed_case_ids = [
        case_id
        for case_id, case_data in bot.feedback_cases.items()
        if case_data.get("category_key") == category_key and case_data.get("status") == "pending"
    ]
    if removed_case_ids:
        for case_id in removed_case_ids:
            del bot.feedback_cases[case_id]
        await bot.update_file()

    return web.json_response({"ok": True})


@routes.post("/api/feedback-panel/publish")
@require_dashboard_access
async def publish_feedback_panel_route(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_id_raw = body.get("channel_id")
    if not isinstance(channel_id_raw, str) or not channel_id_raw:
        return web.json_response({"error": "invalid_request"}, status=400)
    try:
        channel_id = int(channel_id_raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    bot = request.app["bot"]
    moderator = request["moderator"]
    message = await feedback_core.publish_feedback_panel(
        bot, channel, published_by_id=moderator.id, published_by_mention=f"<@{moderator.id}>"
    )
    return web.json_response({"ok": True, "message_id": str(message.id)})
