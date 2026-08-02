"""Aggregated module enabled/disabled state for the dashboard sidebar.

Lets DashboardShell hide nav items for modules the guild has switched off,
without each page having to fetch its own settings just to know that.
"""

from aiohttp import web

import auto_reactions_core
import automod_core
import birthdays_core
import bunker_core
import casino_core
import custom_commands_core
import daily_topic_core
import economy_core
import family_core
import fun_core
import mafia_core
import scheduled_messages_core
import starboard_core
import valchecker_core
import xp_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

# moduleKey -> core module exposing get_settings(guild_id)["enabled"].
# Nav items without an entry here (e.g. Members, Audit, Settings) are always shown.
MODULE_SETTINGS_GETTERS = {
    "levels": xp_core.get_settings,
    "economy": economy_core.get_settings,
    "casino": casino_core.get_settings,
    "family": family_core.get_settings,
    "messages": scheduled_messages_core.get_settings,
    "birthdays": birthdays_core.get_settings,
    "starboard": starboard_core.get_settings,
    "autoReactions": auto_reactions_core.get_settings,
    "fun": fun_core.get_settings,
    "dailyTopic": daily_topic_core.get_settings,
    "mafia": mafia_core.get_settings,
    "bunker": bunker_core.get_settings,
    "automod": automod_core.get_settings,
    "customCommands": custom_commands_core.get_settings,
    "valchecker": valchecker_core.get_settings,
}


@routes.get("/api/modules")
@require_dashboard_access
async def modules_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    modules = {}
    for key, get_settings in MODULE_SETTINGS_GETTERS.items():
        try:
            modules[key] = bool(get_settings(guild_id).get("enabled", True))
        except Exception:
            # Settings module hiccup should never break the sidebar — default to shown.
            modules[key] = True
    return web.json_response({"modules": modules})
