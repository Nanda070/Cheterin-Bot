import discord
from aiohttp import web

import reaction_roles
from ..access_middleware import require_dashboard_access

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
        except discord.HTTPException:
            continue

    return web.json_response(serialize_entry(str(message_id), config[str(message_id)]), status=201)
