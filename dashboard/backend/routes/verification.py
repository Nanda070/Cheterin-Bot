import discord
from aiohttp import web

import verification
import verification_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/verification")
@require_dashboard_access
async def verification_get(request: web.Request) -> web.Response:
    return web.json_response(verification_core.get_settings(request["guild_id"]))


@routes.put("/api/verification")
@require_dashboard_access
async def verification_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in ("enabled", "rules_consent_enabled", "reverify_enabled"):
        if not isinstance(body.get(key, False), bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    # Строки, не числа: Discord ID (snowflake) превышает Number.MAX_SAFE_INTEGER
    # во фронтенде — числом его передавать нельзя, значение тихо портится при вводе.
    values = {}
    for key in ("unverified_role_id", "verified_role_id"):
        value = body.get(key, "")
        if not isinstance(value, str) or (value and not value.isdigit()):
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        values[key] = value

    welcome_text = body.get("welcome_text", verification_core.DEFAULT_WELCOME_TEXT)
    if not isinstance(welcome_text, str) or not 1 <= len(welcome_text.strip()) <= 1000:
        return web.json_response({"error": "invalid_welcome_text"}, status=400)

    reverify_days = body.get("reverify_days", verification_core.DEFAULT_REVERIFY_DAYS)
    if isinstance(reverify_days, bool) or not isinstance(reverify_days, (int, float)):
        return web.json_response({"error": "invalid_reverify_days"}, status=400)
    reverify_days = int(reverify_days)
    if not (
        verification_core.MIN_REVERIFY_DAYS
        <= reverify_days
        <= verification_core.MAX_REVERIFY_DAYS
    ):
        return web.json_response({"error": "invalid_reverify_days"}, status=400)

    guild_id = request["guild_id"]
    verification_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "welcome_text": welcome_text.strip(),
        "rules_consent_enabled": body.get("rules_consent_enabled", False),
        "reverify_enabled": body.get("reverify_enabled", False),
        "reverify_days": reverify_days,
        **values,
    })
    return web.json_response(verification_core.get_settings(guild_id))


@routes.post("/api/verification/publish")
@require_dashboard_access
async def verification_publish(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild_id = request["guild_id"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    settings = verification_core.get_settings(guild_id)
    if not settings["enabled"]:
        return web.json_response({"error": "module_disabled"}, status=409)
    if not verification_core.is_configured(settings):
        return web.json_response({"error": "not_configured"}, status=409)

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
    if not hasattr(channel, "send"):
        return web.json_response({"error": "channel_not_messageable"}, status=400)

    try:
        message = await verification.publish_verification_panel(bot, channel)
    except discord.Forbidden:
        return web.json_response({"error": "forbidden_by_discord"}, status=403)
    except discord.HTTPException:
        return web.json_response({"error": "publish_failed"}, status=502)
    except Exception:
        return web.json_response({"error": "publish_failed"}, status=500)

    return web.json_response({"ok": True, "message_id": str(message.id)})
