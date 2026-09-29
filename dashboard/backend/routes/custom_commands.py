from aiohttp import web

import bot.modules.utility.custom_commands_core as custom_commands_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/custom-commands")
@require_dashboard_access
async def custom_commands_get(request: web.Request) -> web.Response:
    return web.json_response(custom_commands_core.get_settings(request["guild_id"]))


@routes.put("/api/custom-commands/settings")
@require_dashboard_access
async def custom_commands_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict) or not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_request"}, status=400)
    return web.json_response(custom_commands_core.update_enabled(request["guild_id"], body["enabled"]))


@routes.post("/api/custom-commands")
@require_dashboard_access
async def custom_commands_create(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    trigger = body.get("trigger", "")
    reply_text = body.get("reply_text", "")
    match = body.get("match", "exact")
    embed = body.get("embed")
    enabled = body.get("enabled", True)

    if not isinstance(trigger, str) or not trigger.strip() or len(trigger) > custom_commands_core.MAX_TRIGGER_LEN:
        return web.json_response({"error": "invalid_trigger"}, status=400)
    if not isinstance(reply_text, str) or len(reply_text) > custom_commands_core.MAX_REPLY_LEN:
        return web.json_response({"error": "invalid_reply_text"}, status=400)
    if match not in ("exact", "contains"):
        return web.json_response({"error": "invalid_match"}, status=400)
    if embed is not None and not isinstance(embed, dict):
        return web.json_response({"error": "invalid_embed"}, status=400)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    cmd = custom_commands_core.add_command(
        request["guild_id"],
        trigger=trigger.strip(),
        match=match,
        reply_text=reply_text,
        embed=embed,
        enabled=enabled,
    )
    if cmd is None:
        return web.json_response({"error": "limit_reached"}, status=409)
    return web.json_response(cmd, status=201)


@routes.patch("/api/custom-commands/{cmd_id}")
@require_dashboard_access
async def custom_commands_update(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    fields = {}
    if "trigger" in body:
        trigger = body["trigger"]
        if not isinstance(trigger, str) or not trigger.strip() or len(trigger) > custom_commands_core.MAX_TRIGGER_LEN:
            return web.json_response({"error": "invalid_trigger"}, status=400)
        fields["trigger"] = trigger.strip()
    if "match" in body:
        if body["match"] not in ("exact", "contains"):
            return web.json_response({"error": "invalid_match"}, status=400)
        fields["match"] = body["match"]
    if "reply_text" in body:
        reply_text = body["reply_text"]
        if not isinstance(reply_text, str) or len(reply_text) > custom_commands_core.MAX_REPLY_LEN:
            return web.json_response({"error": "invalid_reply_text"}, status=400)
        fields["reply_text"] = reply_text
    if "embed" in body:
        if body["embed"] is not None and not isinstance(body["embed"], dict):
            return web.json_response({"error": "invalid_embed"}, status=400)
        fields["embed"] = body["embed"]
    if "enabled" in body:
        if not isinstance(body["enabled"], bool):
            return web.json_response({"error": "invalid_enabled"}, status=400)
        fields["enabled"] = body["enabled"]

    cmd = custom_commands_core.update_command(request["guild_id"], request.match_info["cmd_id"], **fields)
    if cmd is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(cmd)


@routes.delete("/api/custom-commands/{cmd_id}")
@require_dashboard_access
async def custom_commands_delete(request: web.Request) -> web.Response:
    if not custom_commands_core.delete_command(request["guild_id"], request.match_info["cmd_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
