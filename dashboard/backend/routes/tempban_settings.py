from aiohttp import web

import bot_config
import tempban
import tempban_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/tempban-settings")
@require_dashboard_access
async def get_tempban_settings(request: web.Request) -> web.Response:
    return web.json_response(tempban_core.get_settings(request["guild_id"]))


@routes.put("/api/tempban-settings")
@require_dashboard_access
async def update_tempban_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    dm_enabled = body.get("dm_enabled")
    log_enabled = body.get("log_enabled")
    if not isinstance(dm_enabled, bool) or not isinstance(log_enabled, bool):
        return web.json_response({"error": "invalid_request"}, status=400)

    guild_id = request["guild_id"]
    existing = tempban_core.get_settings(guild_id)
    payload = {
        "dm_enabled": dm_enabled,
        "dm_message": str(body.get("dm_message") or ""),
        "log_enabled": log_enabled,
        "log_message": str(body.get("log_message") or ""),
        "unban_reason": str(body.get("unban_reason") or ""),
        "warning_message": str(body.get("warning_message") or ""),
        "warning_thumbnail_url": str(body.get("warning_thumbnail_url") or ""),
        # Preserve runtime fields
        "ban_count": existing.get("ban_count", 0),
        "warning_message_id": existing.get("warning_message_id") or "",
    }
    # Only overwrite action when the client sends it; omit → save_settings keeps stored mode.
    if "action" in body:
        action = str(body.get("action") or "").strip().lower()
        if action not in tempban_core.ACTION_MODES:
            return web.json_response({"error": "invalid_action"}, status=400)
        payload["action"] = action

    tempban_core.save_settings(guild_id, payload)
    return web.json_response(tempban_core.get_settings(guild_id))


@routes.post("/api/tempban-settings/publish-warning")
@require_dashboard_access
async def publish_tempban_warning(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    if not bot_config.get(guild_id, "TEMPBAN_CHANNEL_ID"):
        return web.json_response({"error": "trap_channel_not_set"}, status=400)

    try:
        message = await tempban.publish_warning_panel(bot, guild)
    except ValueError as exc:
        code = str(exc) or "publish_failed"
        status = 404 if code == "channel_not_found" else 400
        return web.json_response({"error": code}, status=status)
    except Exception:
        return web.json_response({"error": "publish_failed"}, status=500)

    settings = tempban_core.get_settings(guild_id)
    return web.json_response({
        "ok": True,
        "message_id": str(message.id),
        "ban_count": settings.get("ban_count", 0),
        "warning_message_id": settings.get("warning_message_id") or str(message.id),
    })
