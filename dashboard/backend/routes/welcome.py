from aiohttp import web

import bot_config
import embed_builder
import welcome_core
from message_template_core import normalize_embed_spec

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _serialize_messages(guild_id: int) -> dict:
    return welcome_core.get_settings(guild_id)


def _validate_messages_payload(body: dict) -> str | None:
    mode = body.get("channel_mode")
    if mode not in ("text", "embed"):
        return "invalid_channel_mode"

    # Channel embed is only required/validated in embed mode; text mode may send an empty stub.
    if mode == "embed":
        err = embed_builder.validate_embed_spec(normalize_embed_spec(body.get("channel_embed")))
        if err:
            return err

    # DM embed is optional: empty means "use built-in Server 404 defaults" at send time.
    dm_embed = normalize_embed_spec(body.get("dm_embed"))
    dm_content = str(body.get("dm_content") or "")
    if not embed_builder.is_embed_spec_empty(dm_embed) or dm_content.strip():
        err = embed_builder.validate_embed_spec(dm_embed, dm_content)
        if err:
            return err
    return None


@routes.get("/api/welcome-settings")
@require_dashboard_access
async def get_welcome_settings(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    return web.json_response(
        {
            "channel_enabled": bool(bot_config.get(guild_id, "WELCOME_CHANNEL_ENABLED", True)),
            "dm_enabled": bool(bot_config.get(guild_id, "WELCOME_DM_ENABLED", True)),
            "goodbye_channel_enabled": bool(bot_config.get(guild_id, "GOODBYE_CHANNEL_ENABLED", False)),
            "goodbye_channel_id": str(bot_config.get(guild_id, "GOODBYE_CHANNEL_ID") or ""),
            "messages": _serialize_messages(guild_id),
        }
    )


@routes.put("/api/welcome-settings")
@require_dashboard_access
async def update_welcome_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    channel_enabled = body.get("channel_enabled")
    dm_enabled = body.get("dm_enabled")
    goodbye_channel_enabled = body.get("goodbye_channel_enabled")
    goodbye_channel_id = body.get("goodbye_channel_id", "")
    messages = body.get("messages")
    if (
        not isinstance(channel_enabled, bool)
        or not isinstance(dm_enabled, bool)
        or not isinstance(goodbye_channel_enabled, bool)
        or not isinstance(goodbye_channel_id, str)
    ):
        return web.json_response({"error": "invalid_request"}, status=400)

    if messages is not None:
        if not isinstance(messages, dict):
            return web.json_response({"error": "invalid_request"}, status=400)
        err = _validate_messages_payload(messages)
        if err:
            return web.json_response({"error": err}, status=400)

    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if goodbye_channel_id and guild is not None:
        try:
            channel_id = int(goodbye_channel_id)
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
        if guild.get_channel(channel_id) is None:
            return web.json_response({"error": "goodbye_channel_id_not_found"}, status=404)

    guild_id = request["guild_id"]
    data = bot_config.load_config(guild_id)
    data["WELCOME_CHANNEL_ENABLED"] = channel_enabled
    data["WELCOME_DM_ENABLED"] = dm_enabled
    data["GOODBYE_CHANNEL_ENABLED"] = goodbye_channel_enabled
    data["GOODBYE_CHANNEL_ID"] = goodbye_channel_id
    bot_config.save_config(guild_id, data)

    if isinstance(messages, dict):
        welcome_core.save_settings(
            guild_id,
            {
                "channel_mode": messages.get("channel_mode") or "text",
                "channel_text": str(messages.get("channel_text") or ""),
                "channel_embed": normalize_embed_spec(messages.get("channel_embed")),
                "dm_content": str(messages.get("dm_content") or ""),
                "dm_embed": normalize_embed_spec(messages.get("dm_embed")),
                "dm_thumbnail_url": str(messages.get("dm_thumbnail_url") or ""),
                "dm_fallback_thumbnail_url": str(messages.get("dm_fallback_thumbnail_url") or ""),
                "dm_footer_text": str(messages.get("dm_footer_text") or ""),
                "dm_use_guild_icon": bool(messages.get("dm_use_guild_icon", True)),
                "goodbye_text": str(messages.get("goodbye_text") or ""),
            },
        )

    return web.json_response(
        {
            "channel_enabled": channel_enabled,
            "dm_enabled": dm_enabled,
            "goodbye_channel_enabled": goodbye_channel_enabled,
            "goodbye_channel_id": goodbye_channel_id,
            "messages": _serialize_messages(guild_id),
        }
    )
