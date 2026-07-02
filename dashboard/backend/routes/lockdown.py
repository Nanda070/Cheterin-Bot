import discord
from aiohttp import web

import lockdown_core
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


async def _log(bot, title: str, color, moderator, lines: dict):
    embed = discord.Embed(title=title, color=color, timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    for name, value in lines.items():
        embed.add_field(name=name, value=value, inline=True)
    embed.set_footer(text="Dashboard · Lockdown")
    await bot.send_log(embed)


@routes.get("/api/lockdown/status")
@require_dashboard_access
async def lockdown_status(request: web.Request) -> web.Response:
    active, role_count = lockdown_core.antispam_status()
    return web.json_response({"active": active, "role_count": role_count})


@routes.post("/api/lockdown/activate")
@require_dashboard_access
async def lockdown_activate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    modified_count, errors = await lockdown_core.activate_antispam(
        guild,
        lockdown_core.get_mention_exempt_ids(),
        lockdown_core.get_mentionable_exempt_ids(),
    )
    await _log(
        request.app["bot"], "🛡️ Антиспам ВКЛЮЧЁН (дашборд)", discord.Color.red(),
        request["moderator"], {"Изменено ролей": str(modified_count)},
    )
    return web.json_response({"ok": True, "modified_count": modified_count, "errors": errors})


@routes.post("/api/lockdown/deactivate")
@require_dashboard_access
async def lockdown_deactivate(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    result = await lockdown_core.deactivate_antispam(guild)
    if result is None:
        return web.json_response({"error": "not_active"}, status=409)

    restored_count, errors = result
    await _log(
        request.app["bot"], "🟢 Антиспам ВЫКЛЮЧЕН (дашборд)", discord.Color.green(),
        request["moderator"], {"Восстановлено ролей": str(restored_count)},
    )
    return web.json_response({"ok": True, "restored_count": restored_count, "errors": errors})
