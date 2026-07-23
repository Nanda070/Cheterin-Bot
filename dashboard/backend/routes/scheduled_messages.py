from aiohttp import web

import scheduled_messages_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/scheduled-messages")
@require_dashboard_access
async def scheduled_messages_get(request: web.Request) -> web.Response:
    return web.json_response(scheduled_messages_core.get_settings(request["guild_id"]))


@routes.put("/api/scheduled-messages/settings")
@require_dashboard_access
async def scheduled_messages_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    return web.json_response(scheduled_messages_core.update_enabled(request["guild_id"], body["enabled"]))


def _validate_message_fields(body: dict, *, partial: bool = False) -> tuple[dict | None, web.Response | None]:
    fields: dict = {}
    if not partial or "channel_id" in body:
        channel_id = body.get("channel_id", "")
        if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
            return None, web.json_response({"error": "invalid_channel_id"}, status=400)
        fields["channel_id"] = channel_id
    if not partial or "content" in body:
        content = body.get("content", "")
        if not isinstance(content, str) or not content.strip() or len(content) > scheduled_messages_core.MAX_CONTENT_LEN:
            return None, web.json_response({"error": "invalid_content"}, status=400)
        fields["content"] = content
    if not partial or "schedule_type" in body:
        schedule_type = body.get("schedule_type", "once")
        if schedule_type not in ("once", "daily"):
            return None, web.json_response({"error": "invalid_schedule_type"}, status=400)
        fields["schedule_type"] = schedule_type
    if not partial or "run_at" in body:
        run_at = body.get("run_at", "")
        if not isinstance(run_at, str):
            return None, web.json_response({"error": "invalid_run_at"}, status=400)
        fields["run_at"] = run_at
    if not partial or "daily_time" in body:
        daily_time = body.get("daily_time", "")
        if not isinstance(daily_time, str) or (daily_time and not scheduled_messages_core.is_valid_time(daily_time)):
            return None, web.json_response({"error": "invalid_daily_time"}, status=400)
        fields["daily_time"] = daily_time
    if "enabled" in body or not partial:
        enabled = body.get("enabled", True)
        if not isinstance(enabled, bool):
            return None, web.json_response({"error": "invalid_enabled"}, status=400)
        fields["enabled"] = enabled
    return fields, None


@routes.post("/api/scheduled-messages")
@require_dashboard_access
async def scheduled_messages_create(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    fields, err = _validate_message_fields(body)
    if err:
        return err
    assert fields is not None
    if fields["schedule_type"] == "once" and not fields.get("run_at"):
        return web.json_response({"error": "run_at_required"}, status=400)
    if fields["schedule_type"] == "daily" and not fields.get("daily_time"):
        return web.json_response({"error": "daily_time_required"}, status=400)
    if not fields.get("channel_id"):
        return web.json_response({"error": "channel_required"}, status=400)

    msg = scheduled_messages_core.add_message(request["guild_id"], **fields)
    if msg is None:
        return web.json_response({"error": "limit_reached"}, status=409)
    return web.json_response(msg, status=201)


@routes.patch("/api/scheduled-messages/{msg_id}")
@require_dashboard_access
async def scheduled_messages_update(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    fields, err = _validate_message_fields(body, partial=True)
    if err:
        return err
    assert fields is not None

    guild_id = request["guild_id"]
    msg_id = request.match_info["msg_id"]
    existing = next(
        (m for m in scheduled_messages_core.get_settings(guild_id)["messages"] if m["id"] == str(msg_id)),
        None,
    )
    if existing is None:
        return web.json_response({"error": "not_found"}, status=404)

    merged = {**existing, **fields}
    if merged.get("schedule_type") == "once" and not merged.get("run_at"):
        return web.json_response({"error": "run_at_required"}, status=400)
    if merged.get("schedule_type") == "daily" and not merged.get("daily_time"):
        return web.json_response({"error": "daily_time_required"}, status=400)

    msg = scheduled_messages_core.update_message(guild_id, msg_id, **fields)
    if msg is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(msg)


@routes.delete("/api/scheduled-messages/{msg_id}")
@require_dashboard_access
async def scheduled_messages_delete(request: web.Request) -> web.Response:
    if not scheduled_messages_core.delete_message(request["guild_id"], request.match_info["msg_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
