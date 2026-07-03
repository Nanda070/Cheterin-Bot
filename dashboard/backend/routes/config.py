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
]

ROLE_FIELDS = [
    "SPAM_LOG_ROLE_ID",
    "CTD_ROLE_ID",
]

LIST_CHANNEL_FIELDS = ["SPAM_EXCEPTION_CHANNELS"]
LIST_ROLE_FIELDS = ["BUTTON_CREATE_ALLOWED_ROLES"]

TEXT_FIELDS = ["BUTTON_WEBHOOK_URL", "SERVER_INVITE_LINK"]

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
