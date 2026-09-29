from aiohttp import web

import bot.modules.utility.owner_alerts_core as owner_alerts_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/owner-alerts")
@require_dashboard_access
async def owner_alerts_get(request: web.Request) -> web.Response:
    return web.json_response(owner_alerts_core.get_settings(request["guild_id"]))


@routes.put("/api/owner-alerts")
@require_dashboard_access
async def owner_alerts_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in (
        "enabled",
        "notify_dm",
        "alert_missing_perms",
        "alert_mass_ban",
        "alert_module_errors",
        "weekly_digest_enabled",
    ):
        if key in body and not isinstance(body[key], bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    channel_id = body.get("channel_id", "")
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel_id"}, status=400)

    digest_channel_id = body.get("weekly_digest_channel_id", "")
    if not isinstance(digest_channel_id, str) or (digest_channel_id and not digest_channel_id.isdigit()):
        return web.json_response({"error": "invalid_weekly_digest_channel_id"}, status=400)

    for key in ("mass_ban_threshold", "mass_ban_window_sec", "module_error_threshold"):
        if key in body:
            value = body[key]
            if not isinstance(value, int) or isinstance(value, bool):
                return web.json_response({"error": f"invalid_{key}"}, status=400)

    return web.json_response(owner_alerts_core.save_settings(request["guild_id"], body))


@routes.get("/api/setup-health")
@require_dashboard_access
async def setup_health_get(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "guild_unavailable"}, status=503)
    me = guild.me
    if me is None:
        return web.json_response({"error": "bot_member_unavailable"}, status=503)
    missing = owner_alerts_core.critical_perms_missing(me.guild_permissions)
    module_issues = owner_alerts_core.check_module_health(guild)
    return web.json_response(
        {
            "ok": len(missing) == 0 and len(module_issues) == 0,
            "missing_permissions": missing,
            "module_issues": module_issues,
            "guild_id": str(guild.id),
            "guild_name": guild.name,
        }
    )


@routes.post("/api/owner-alerts/test")
@require_dashboard_access
async def owner_alerts_test(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "guild_unavailable"}, status=503)
    cog = bot.get_cog("OwnerAlertsCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    delivered = await cog.send_alert(guild, "module_error", "Dashboard test ping", force=True)
    if not delivered:
        return web.json_response({"error": "not_delivered"}, status=502)
    return web.json_response({"ok": True})
