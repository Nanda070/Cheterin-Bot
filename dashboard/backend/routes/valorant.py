"""Guild-scoped dashboard routes for Premier and VALORANT role panels."""

from aiohttp import web

import bot.modules.valorant.valorant_features_core as core
import bot.modules.valorant.valorant_panels as valorant_panels
import bot.core.settings_db as settings_db
from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _guild(request: web.Request):
    return request.app["bot"].get_guild(request["guild_id"])


@routes.get("/api/valorant/premier")
@require_dashboard_access
async def premier_get(request: web.Request) -> web.Response:
    return web.json_response({**core.get_premier_settings(request["guild_id"]), "faq_url": core.FAQ_URL})


@routes.put("/api/valorant/premier")
@require_dashboard_access
async def premier_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("enabled"), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    channel_id = body.get("channel_id", "")
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel_id"}, status=400)
    guild = _guild(request)
    if channel_id and guild and guild.get_channel(int(channel_id)) is None:
        return web.json_response({"error": "channel_not_found"}, status=404)
    return web.json_response({**core.save_premier_settings(request["guild_id"], body), "faq_url": core.FAQ_URL})


@routes.get("/api/valorant/panels")
@require_dashboard_access
async def panels_get(request: web.Request) -> web.Response:
    return web.json_response({"settings": core.get_panel_settings(request["guild_id"]), "catalog": core.panel_catalog()})


@routes.put("/api/valorant/panels")
@require_dashboard_access
async def panels_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)
    guild = _guild(request)
    for map_key in ("agent_roles", "playstyle_roles", "notification_roles", "server_roles", "notification_channels"):
        values = body.get(map_key)
        if values is not None and not isinstance(values, dict):
            return web.json_response({"error": "invalid_request"}, status=400)
        if isinstance(values, dict):
            for value in values.values():
                if not isinstance(value, str) or (value and not value.isdigit()):
                    return web.json_response({"error": "invalid_id"}, status=400)
    button_role_id = body.get("button_role_id", "")
    if not isinstance(button_role_id, str) or (button_role_id and not button_role_id.isdigit()):
        return web.json_response({"error": "invalid_button_role_id"}, status=400)
    if button_role_id and guild and guild.get_role(int(button_role_id)) is None:
        return web.json_response({"error": "role_not_found"}, status=404)
    return web.json_response({"settings": core.save_panel_settings(request["guild_id"], body), "catalog": core.panel_catalog()})


@routes.post("/api/valorant/panels/publish")
@require_dashboard_access
async def panels_publish(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or body.get("kind") not in {"agents", "playstyles", "notifications", "servers"}:
        return web.json_response({"error": "invalid_request"}, status=400)
    channel_id = body.get("channel_id")
    guild = _guild(request)
    channel = guild.get_channel(int(channel_id)) if guild and isinstance(channel_id, str) and channel_id.isdigit() else None
    if channel is None or not hasattr(channel, "send"):
        return web.json_response({"error": "channel_not_found"}, status=404)
    message = await valorant_panels.publish_panel(channel, body["kind"])
    return web.json_response({"ok": True, "message_id": str(message.id)})


@routes.get("/api/valorant/commands")
@require_dashboard_access
async def commands_get(request: web.Request) -> web.Response:
    return web.json_response({"enabled": bool(settings_db.get(request["guild_id"], "valorant_random", {}).get("enabled", True))})


@routes.put("/api/valorant/commands")
@require_dashboard_access
async def commands_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("enabled"), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    settings_db.put(request["guild_id"], "valorant_random", {"enabled": body["enabled"]})
    return web.json_response({"enabled": body["enabled"]})
