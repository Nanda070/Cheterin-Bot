import logging

import discord
from aiohttp import web

import embed_builder
from ..access_middleware import require_dashboard_access

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

MAX_ROLE_BUTTONS = 5


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


def _validate_role_ids_structure(role_ids_raw):
    """Checks that don't require Discord data: count and int-parseability.
    Returns (parsed_role_ids, None) on success, or ([], error_response)."""
    if len(role_ids_raw) > MAX_ROLE_BUTTONS:
        return [], web.json_response({"error": "too_many_roles"}, status=400)
    try:
        role_ids = [int(r) for r in role_ids_raw]
    except (TypeError, ValueError):
        return [], web.json_response({"error": "invalid_request"}, status=400)
    return role_ids, None


def _validate_role_ids_assignable(role_ids: list[int], guild):
    """Role-hierarchy check. Returns None on success, or an error
    web.Response. Must run AFTER channel/message existence checks."""
    for role_id in role_ids:
        role = guild.get_role(role_id)
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)
    return None


async def _parse_body(request):
    try:
        body = await request.json()
    except ValueError:
        return None, web.json_response({"error": "invalid_request"}, status=400)
    return body, None


@routes.post("/api/embed-messages")
@require_dashboard_access
async def create_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    body, error = await _parse_body(request)
    if error:
        return error

    try:
        channel_id = int(body.get("channel_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    spec = body.get("embed") or {}
    error_code = embed_builder.validate_embed_spec(spec)
    if error_code:
        return web.json_response({"error": error_code}, status=400)

    role_ids, error = _validate_role_ids_structure(body.get("role_ids") or [])
    if error:
        return error

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    error = _validate_role_ids_assignable(role_ids, guild)
    if error:
        return error

    content = body.get("content") or None
    embed = embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        message = await channel.send(content=content, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to send embed message to channel %s: %s", channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message.id), "channel_id": str(channel_id)}, status=201)


@routes.get("/api/embed-messages/{channel_id}/{message_id}")
@require_dashboard_access
async def get_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel_id = int(request.match_info["channel_id"])
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    spec = embed_builder.embed_to_spec(message.embeds[0]) if message.embeds else {}
    role_ids = embed_builder.parse_role_button_ids(message)

    return web.json_response(
        {"content": message.content, "embed": spec, "role_ids": [str(r) for r in role_ids]}
    )


@routes.put("/api/embed-messages/{channel_id}/{message_id}")
@require_dashboard_access
async def update_embed_message(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        channel_id = int(request.match_info["channel_id"])
        message_id = int(request.match_info["message_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    body, error = await _parse_body(request)
    if error:
        return error

    spec = body.get("embed") or {}
    error_code = embed_builder.validate_embed_spec(spec)
    if error_code:
        return web.json_response({"error": error_code}, status=400)

    role_ids, error = _validate_role_ids_structure(body.get("role_ids") or [])
    if error:
        return error

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(message_id)
    except discord.NotFound:
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    error = _validate_role_ids_assignable(role_ids, guild)
    if error:
        return error

    content = body.get("content") or None
    embed = embed_builder.build_embed(spec)
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None

    try:
        await message.edit(content=content, embed=embed, view=view)
    except discord.HTTPException as exc:
        logger.warning("Failed to edit embed message %s in channel %s: %s", message_id, channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response({"message_id": str(message_id), "channel_id": str(channel_id)})
