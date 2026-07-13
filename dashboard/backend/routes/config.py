from aiohttp import web

import bot_config

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

CHANNEL_FIELDS = [
    "LOG_CHANNEL_ID",
    "TEMPBAN_CHANNEL_ID",
    "SPAM_LOG_CHANNEL_ID",
    "WELCOME_CHANNEL_ID",
    "INVITE_LOG_CHANNEL_ID",
    "ANNOUNCEMENTS_CHANNEL_ID",
    "RULES_CHANNEL_ID",
    "ROLES_CHANNEL_ID",
    "SEARCH_PLAYERS_CHANNEL_ID",
    "CTD_CHANNEL_ID",
    "VOICE_LOBBY_CHANNEL_ID",
    "VOICE_PANEL_CHANNEL_ID",
    "VOICE_LOG_CHANNEL_ID",
    "SUPPLY_VOICE_CHANNEL_ID",
    "SUPPLY_LOG_CHANNEL_ID",
]

ROLE_FIELDS = [
    "SPAM_LOG_ROLE_ID",
    "CTD_ROLE_ID",
    "SUPPLY_ROLE_ID",
]

LIST_CHANNEL_FIELDS = ["SPAM_EXCEPTION_CHANNELS"]
LIST_ROLE_FIELDS = ["BUTTON_CREATE_ALLOWED_ROLES"]

TEXT_FIELDS = ["BUTTON_WEBHOOK_URL", "SERVER_INVITE_LINK", "VOICE_PANEL_THUMB_URL", "SUPPLY_REMINDER_MINUTES"]

ALL_FIELDS = CHANNEL_FIELDS + ROLE_FIELDS + LIST_CHANNEL_FIELDS + LIST_ROLE_FIELDS + TEXT_FIELDS
ALL_LIST_FIELDS = LIST_CHANNEL_FIELDS + LIST_ROLE_FIELDS


@routes.get("/api/config")
@require_dashboard_access
async def get_config(request: web.Request) -> web.Response:
    data = bot_config.load_config()
    result = {}
    for key in ALL_FIELDS:
        if key in ALL_LIST_FIELDS:
            result[key] = [str(v) for v in data.get(key, [])]
        else:
            result[key] = str(data.get(key) or "")
    return web.json_response(result)


def _validate_structure(body: dict) -> str | None:
    for key in CHANNEL_FIELDS + ROLE_FIELDS + TEXT_FIELDS:
        value = body.get(key, "")
        if not isinstance(value, str):
            return f"invalid_{key.lower()}"
    for key in ALL_LIST_FIELDS:
        value = body.get(key, [])
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            return f"invalid_{key.lower()}"
    return None


def _check_channel(guild, key: str, raw_id: str) -> web.Response | None:
    try:
        channel_id = int(raw_id)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_channel(channel_id) is None:
        return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)
    return None


def _check_role(guild, key: str, raw_id: str) -> web.Response | None:
    try:
        role_id = int(raw_id)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if guild.get_role(role_id) is None:
        return web.json_response({"error": f"{key.lower()}_not_found"}, status=404)
    return None


def _validate_relations(body: dict, guild) -> web.Response | None:
    for key in CHANNEL_FIELDS:
        value = body.get(key, "")
        if value:
            error_response = _check_channel(guild, key, value)
            if error_response:
                return error_response

    for key in ROLE_FIELDS:
        value = body.get(key, "")
        if value:
            error_response = _check_role(guild, key, value)
            if error_response:
                return error_response

    for key in LIST_CHANNEL_FIELDS:
        for raw_id in body.get(key, []):
            error_response = _check_channel(guild, key, raw_id)
            if error_response:
                return error_response

    for key in LIST_ROLE_FIELDS:
        for raw_id in body.get(key, []):
            error_response = _check_role(guild, key, raw_id)
            if error_response:
                return error_response

    return None


@routes.put("/api/config")
@require_dashboard_access
async def update_config(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    error = _validate_structure(body)
    if error:
        return web.json_response({"error": error}, status=400)

    error_response = _validate_relations(body, guild)
    if error_response:
        return error_response

    # Обновляем только свои поля, не затирая ключи других разделов
    # (AUTO_ROLE_IDS, WELCOME_CHANNEL_ENABLED и т.п. живут в том же config.json).
    data = bot_config.load_config()
    for key in ALL_FIELDS:
        data[key] = body.get(key, [] if key in ALL_LIST_FIELDS else "")
    bot_config.save_config(data)

    result = {key: (list(data[key]) if key in ALL_LIST_FIELDS else str(data[key] or "")) for key in ALL_FIELDS}
    return web.json_response(result)
