import discord
from aiohttp import web

import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.modules.moderation.lockdown_core as lockdown_core
import bot.core.moderation_embed_core as moderation_embed_core
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


async def _log(bot, guild_id: int, title_key: str, color, moderator, lines: dict, errors: list[str] | None = None):
    lang = i18n.lang_for(guild_id)
    guild = bot.get_guild(guild_id)
    extra_parts = [f"{i18n.t(name_key, lang)}: {value}" for name_key, value in lines.items()]
    if errors:
        extra_parts.append(
            f"{i18n.t('lockdown.dashboard.errors', lang)}:\n" + "\n".join(errors[:10])
        )
    embed = moderation_embed_core.build_user_action_embed(
        lang,
        title=i18n.t(title_key, lang),
        actor=moderator,
        target_name=guild.name if guild else str(guild_id),
        target_id=guild_id,
        reason="",
        extra="\n".join(extra_parts),
        color=color,
        footer_key="lockdown.dashboard.footer",
        timestamp=bot.utcnow(),
    )
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
        lockdown_core.get_mention_exempt_ids(request["guild_id"]),
        lockdown_core.get_mentionable_exempt_ids(request["guild_id"]),
        lang,
    )
    await _log(
        request.app["bot"],
        request["guild_id"],
        "lockdown.dashboard.activate_title",
        embed_style.DANGER,
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
        embed_style.SUCCESS,
        request["moderator"],
        {"lockdown.dashboard.roles_restored": str(restored_count)},
        errors=errors if errors else None,
    )
    return web.json_response({"ok": True, "restored_count": restored_count, "errors": errors})


@routes.get("/api/lockdown/exempt")
@require_dashboard_access
async def lockdown_exempt_get(request: web.Request) -> web.Response:
    return web.json_response(lockdown_core.get_exempt_settings(request["guild_id"]))


@routes.put("/api/lockdown/exempt")
@require_dashboard_access
async def lockdown_exempt_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    return web.json_response(lockdown_core.save_exempt_settings(request["guild_id"], body))
