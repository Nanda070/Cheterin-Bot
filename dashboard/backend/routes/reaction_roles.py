import logging

import discord
from aiohttp import web

import reaction_roles
from ..access_middleware import require_dashboard_access

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


def _is_role_assignable(role, guild) -> bool:
    return not role.is_default() and not role.managed and role.position < guild.me.top_role.position


def serialize_entry(message_id: str, entry: dict) -> dict:
    return {"message_id": message_id, "channel_id": entry["channel_id"], "pairs": entry["pairs"]}


@routes.get("/api/reaction-roles")
@require_dashboard_access
async def list_reaction_roles(request: web.Request) -> web.Response:
    config = reaction_roles.load_config()
    return web.json_response(
        {"reaction_roles": [serialize_entry(mid, entry) for mid, entry in config.items()]}
    )


def _validate_pairs_structure(pairs):
    """Checks that don't require Discord data: non-empty, no duplicate emoji,
    well-formed. Returns None on success, or an error web.Response. Must run
    BEFORE any channel/message lookup."""
    if not pairs:
        return web.json_response({"error": "invalid_request"}, status=400)
    if reaction_roles.has_duplicate_emoji(pairs):
        return web.json_response({"error": "duplicate_emoji"}, status=400)
    for pair in pairs:
        if not pair.get("emoji"):
            return web.json_response({"error": "invalid_request"}, status=400)
        try:
            int(pair.get("role_id"))
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_request"}, status=400)
    return None


def _validate_roles_assignable(pairs, guild):
    """Role-hierarchy check. Returns None on success, or an error
    web.Response. Must run AFTER channel/message existence checks."""
    for pair in pairs:
        role = guild.get_role(int(pair["role_id"]))
        if role is None or not _is_role_assignable(role, guild):
            return web.json_response({"error": "role_not_assignable"}, status=403)
    return None


@routes.post("/api/reaction-roles")
@require_dashboard_access
async def create_reaction_role(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    try:
        channel_id = int(body.get("channel_id"))
        message_id = int(body.get("message_id"))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    pairs = body.get("pairs") or []
    error = _validate_pairs_structure(pairs)
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

    error = _validate_roles_assignable(pairs, guild)
    if error:
        return error

    config = reaction_roles.load_config()
    config[str(message_id)] = {"channel_id": str(channel_id), "pairs": pairs}
    reaction_roles.save_config(config)

    for pair in pairs:
        try:
            await message.add_reaction(pair["emoji"])
        except discord.HTTPException as exc:
            logger.warning("Failed to add reaction %s on message %s: %s", pair["emoji"], message_id, exc)
            continue

    return web.json_response(serialize_entry(str(message_id), config[str(message_id)]), status=201)


@routes.put("/api/reaction-roles/{message_id}")
@require_dashboard_access
async def update_reaction_role(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    message_id_raw = request.match_info["message_id"]
    config = reaction_roles.load_config()
    entry = config.get(message_id_raw)
    if entry is None:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    pairs = body.get("pairs") or []
    error = _validate_pairs_structure(pairs)
    if error:
        return error

    channel = guild.get_channel(int(entry["channel_id"]))
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    try:
        message = await channel.fetch_message(int(message_id_raw))
    except discord.NotFound:
        del config[message_id_raw]
        reaction_roles.save_config(config)
        return web.json_response({"error": "message_not_found"}, status=404)
    except discord.HTTPException:
        return web.json_response({"error": "discord_error"}, status=502)

    error = _validate_roles_assignable(pairs, guild)
    if error:
        return error

    old_emojis = {p["emoji"] for p in entry["pairs"]}
    new_emojis = {p["emoji"] for p in pairs}

    for emoji in old_emojis - new_emojis:
        try:
            await message.remove_reaction(emoji, request.app["bot"].user)
        except discord.HTTPException as exc:
            logger.warning("Failed to remove reaction %s on message %s: %s", emoji, message_id_raw, exc)
            continue
    for emoji in new_emojis - old_emojis:
        try:
            await message.add_reaction(emoji)
        except discord.HTTPException as exc:
            logger.warning("Failed to add reaction %s on message %s: %s", emoji, message_id_raw, exc)
            continue

    config[message_id_raw] = {"channel_id": entry["channel_id"], "pairs": pairs}
    reaction_roles.save_config(config)

    return web.json_response(serialize_entry(message_id_raw, config[message_id_raw]))


@routes.delete("/api/reaction-roles/{message_id}")
@require_dashboard_access
async def delete_reaction_role(request: web.Request) -> web.Response:
    message_id_raw = request.match_info["message_id"]
    config = reaction_roles.load_config()
    entry = config.get(message_id_raw)
    if entry is None:
        return web.json_response({"error": "not_found"}, status=404)

    guild = _get_guild_or_none(request)
    if guild is not None:
        channel = guild.get_channel(int(entry["channel_id"]))
        if channel is not None:
            try:
                message = await channel.fetch_message(int(message_id_raw))
                for pair in entry["pairs"]:
                    try:
                        await message.remove_reaction(pair["emoji"], request.app["bot"].user)
                    except discord.HTTPException as exc:
                        logger.warning(
                            "Failed to remove reaction %s on message %s: %s", pair["emoji"], message_id_raw, exc
                        )
                        continue
            except discord.NotFound:
                pass
            except discord.HTTPException:
                pass

    del config[message_id_raw]
    reaction_roles.save_config(config)
    return web.json_response({"ok": True})


@routes.get("/api/emojis")
@require_dashboard_access
async def list_emojis(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    return web.json_response(
        {"emojis": [{"id": str(e.id), "name": e.name, "url": str(e.url)} for e in guild.emojis]}
    )


@routes.get("/api/channels")
@require_dashboard_access
async def list_channels(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)
    return web.json_response(
        {"channels": [{"id": str(c.id), "name": c.name} for c in guild.channels]}
    )
