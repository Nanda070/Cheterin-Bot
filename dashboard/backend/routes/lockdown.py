import discord
from aiohttp import web

import i18n
import lockdown_core
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


async def _log(bot, guild_id: int, title_key: str, color, moderator, lines: dict, errors: list[str] | None = None):
    lang = i18n.lang_for(guild_id)
    embed = discord.Embed(title=i18n.t(title_key, lang), color=color, timestamp=bot.utcnow())
    embed.add_field(
        name=i18n.t("lockdown.dashboard.who", lang),
        value=f"{moderator.name} (`{moderator.id}`)",
        inline=False,
    )
    for name_key, value in lines.items():
        embed.add_field(name=i18n.t(name_key, lang), value=value, inline=True)
    if errors:
        embed.add_field(
            name=i18n.t("lockdown.dashboard.errors", lang),
            value="\n".join(errors[:10]),
            inline=False,
        )
    embed.set_footer(text=i18n.t("lockdown.dashboard.footer", lang))
    await bot.send_log(guild_id, embed)


@routes.get("/api/lockdown/status")
@require_dashboard_access
async def lockdown_status(request: web.Request) -> web.Response:
    active, role_count = lockdown_core.antispam_status(request["guild_id"])
    return web.json_response({"active": active, "role_count": role_count})


@routes.post("/api/lockdown/activate")
@require_dashboard_access
async def lockdown_activate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    lang = i18n.lang_for(request["guild_id"])
    modified_count, errors = await lockdown_core.activate_antispam(
        guild,
        lockdown_core.get_mention_exempt_ids(),
        lockdown_core.get_mentionable_exempt_ids(),
        lang,
    )
    await _log(
        request.app["bot"],
        request["guild_id"],
        "lockdown.dashboard.activate_title",
        discord.Color.red(),
        request["moderator"],
        {"lockdown.dashboard.roles_modified": str(modified_count)},
        errors=errors if errors else None,
    )
    return web.json_response({"ok": True, "modified_count": modified_count, "errors": errors})


@routes.post("/api/lockdown/deactivate")
@require_dashboard_access
async def lockdown_deactivate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    lang = i18n.lang_for(request["guild_id"])
    result = await lockdown_core.deactivate_antispam(guild, lang)
    if result is None:
        return web.json_response({"error": "not_active"}, status=409)

    restored_count, errors = result
    await _log(
        request.app["bot"],
        request["guild_id"],
        "lockdown.dashboard.deactivate_title",
        discord.Color.green(),
        request["moderator"],
        {"lockdown.dashboard.roles_restored": str(restored_count)},
        errors=errors if errors else None,
    )
    return web.json_response({"ok": True, "restored_count": restored_count, "errors": errors})
