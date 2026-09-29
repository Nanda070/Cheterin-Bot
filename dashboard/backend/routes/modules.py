"""Aggregated module enabled/disabled state for the dashboard sidebar.

Lets DashboardShell hide nav items for modules the guild has switched off,
without each page having to fetch its own settings just to know that.
"""

from aiohttp import web

import bot.modules.community.auto_reactions_core as auto_reactions_core
import bot.modules.moderation.automod_core as automod_core
import bot.modules.community.banner_rotation_core as banner_rotation_core
import bot.modules.valorant.customs_core as customs_core
import bot.modules.community.birthdays_core as birthdays_core
import bot.modules.games.bunker_core as bunker_core
import bot.modules.games.casino_core as casino_core
import bot.modules.utility.custom_commands_core as custom_commands_core
import bot.modules.community.daily_topic_core as daily_topic_core
import bot.modules.games.economy_core as economy_core
import bot.modules.games.family_core as family_core
import bot.modules.games.fun_core as fun_core
import bot.modules.games.mafia_core as mafia_core
import bot.modules.games.relations_core as relations_core
import bot.modules.community.scheduled_messages_core as scheduled_messages_core
import bot.modules.community.starboard_core as starboard_core
import bot.modules.valorant.valchecker_core as valchecker_core
import bot.modules.levels.xp_core as xp_core

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
    "relations": relations_core.get_settings,
    "dailyTopic": daily_topic_core.get_settings,
    "mafia": mafia_core.get_settings,
    "bunker": bunker_core.get_settings,
    "automod": automod_core.get_settings,
    "customCommands": custom_commands_core.get_settings,
    "valchecker": valchecker_core.get_settings,
    "customs": customs_core.get_settings,
    "bannerRotation": banner_rotation_core.get_settings,
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
