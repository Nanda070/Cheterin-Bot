from aiohttp import web

import automod_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

MAX_STORED_DURATION_MINUTES = 525600  # 365 дней — верхняя граница хранения (Discord-лимиты применяются при выполнении)

COMMON_FIELDS = {
    "enabled",
    "delete_message",
    "punishment",
    "duration_minutes",
    "notify_member",
    "notify_channel_id",
    "notify_template",
}

FILTER_EXTRA_FIELDS: dict[str, set[str]] = {
    "links": {"whitelist_domains"},
    "invites": {"allow_own_server"},
    "scam_links": {"blocklist_keywords"},
    "bad_words": {"words"},
    "repeated_text": {"max_repeats", "consecutive_only", "reset_on_trigger"},
    "caps_lock": {"max_percent", "min_length"},
    "emoji_spam": {"max_count"},
    "mentions": {"max_count"},
    "zalgo": {"max_count"},
}


def _is_str_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) for v in value)


def _validate_filter_fields(key: str, body: dict) -> tuple[dict, str | None]:
    allowed = COMMON_FIELDS | FILTER_EXTRA_FIELDS.get(key, set())
    cleaned = {}

    for field, value in body.items():
        if field not in allowed:
            continue

        if field == "enabled" or field == "delete_message" or field == "notify_member":
            if not isinstance(value, bool):
                return {}, f"invalid_{field}"
        elif field == "punishment":
            if value not in automod_core.PUNISHMENTS:
                return {}, "invalid_punishment"
        elif field == "duration_minutes":
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= MAX_STORED_DURATION_MINUTES):
                return {}, "invalid_duration_minutes"
        elif field == "notify_channel_id":
            if not isinstance(value, str) or (value and not value.isdigit()):
                return {}, "invalid_notify_channel_id"
        elif field == "notify_template":
            if not isinstance(value, str) or not value.strip() or len(value) > 1000:
                return {}, "invalid_notify_template"
        elif field in ("whitelist_domains", "blocklist_keywords", "words"):
            if not _is_str_list(value):
                return {}, f"invalid_{field}"
            value = [v.strip() for v in value if v.strip()]
        elif field == "allow_own_server" or field == "consecutive_only" or field == "reset_on_trigger":
            if not isinstance(value, bool):
                return {}, f"invalid_{field}"
        elif field == "max_repeats":
            if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 100):
                return {}, "invalid_max_repeats"
        elif field == "max_percent":
            if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 100):
                return {}, "invalid_max_percent"
        elif field == "min_length":
            if not isinstance(value, int) or isinstance(value, bool) or not (0 <= value <= 2000):
                return {}, "invalid_min_length"
        elif field == "max_count":
            if not isinstance(value, int) or isinstance(value, bool) or not (1 <= value <= 100):
                return {}, "invalid_max_count"

        cleaned[field] = value

    return cleaned, None


@routes.get("/api/automod")
@require_dashboard_access
async def automod_get(request: web.Request) -> web.Response:
    return web.json_response(automod_core.get_settings(request["guild_id"]))


@routes.put("/api/automod")
@require_dashboard_access
async def automod_update_enabled(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    enabled = body.get("enabled") if isinstance(body, dict) else None
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    return web.json_response(automod_core.update_module_enabled(request["guild_id"], enabled))


@routes.put("/api/automod/filters/{filter_key}")
@require_dashboard_access
async def automod_update_filter(request: web.Request) -> web.Response:
    key = request.match_info["filter_key"]
    if key not in automod_core.FILTER_KEYS:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    cleaned, error = _validate_filter_fields(key, body)
    if error:
        return web.json_response({"error": error}, status=400)

    updated = automod_core.update_filter(request["guild_id"], key, cleaned)
    return web.json_response(updated)


@routes.put("/api/automod/manual-warn-duration")
@require_dashboard_access
async def automod_update_manual_warn_duration(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    minutes = body.get("duration_minutes") if isinstance(body, dict) else None
    if not isinstance(minutes, int) or isinstance(minutes, bool) or not (0 <= minutes <= MAX_STORED_DURATION_MINUTES):
        return web.json_response({"error": "invalid_duration_minutes"}, status=400)
    return web.json_response(automod_core.update_manual_warn_duration(request["guild_id"], minutes))


def _validate_escalation_body(body: dict) -> str | None:
    count = body.get("count")
    action = body.get("action")
    duration = body.get("duration_minutes")
    if not isinstance(count, int) or isinstance(count, bool) or count < 1:
        return "invalid_count"
    if action not in automod_core.ESCALATION_ACTIONS:
        return "invalid_action"
    if not isinstance(duration, int) or isinstance(duration, bool) or not (0 <= duration <= MAX_STORED_DURATION_MINUTES):
        return "invalid_duration_minutes"
    return None


@routes.post("/api/automod/escalation")
@require_dashboard_access
async def automod_create_escalation(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    error = _validate_escalation_body(body)
    if error:
        return web.json_response({"error": error}, status=400)

    rule = automod_core.add_escalation_rule(request["guild_id"], body["count"], body["action"], body["duration_minutes"])
    return web.json_response(rule, status=201)


@routes.patch("/api/automod/escalation/{rule_id}")
@require_dashboard_access
async def automod_update_escalation(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    fields = {}
    for key in ("count", "action", "duration_minutes"):
        if key in body:
            fields[key] = body[key]
    if fields:
        merged = {"count": 1, "action": "mute", "duration_minutes": 0, **fields}
        error = _validate_escalation_body(merged)
        if error:
            return web.json_response({"error": error}, status=400)

    updated = automod_core.update_escalation_rule(request["guild_id"], request.match_info["rule_id"], fields)
    if updated is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(updated)


@routes.delete("/api/automod/escalation/{rule_id}")
@require_dashboard_access
async def automod_delete_escalation(request: web.Request) -> web.Response:
    if not automod_core.delete_escalation_rule(request["guild_id"], request.match_info["rule_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
