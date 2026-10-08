import logging

import discord
from aiohttp import web

import bot.core.embed_builder as embed_builder
from ..access_middleware import require_dashboard_access

logger = logging.getLogger(__name__)

routes = web.RouteTableDef()

MAX_ROLE_BUTTONS = 5


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request["guild_id"])


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


def _parse_embeds_and_content(body):
    """Embed specs (`embeds`, or legacy `embed`) + content of a request body.
    Returns (specs, content, None) on success, or ([], "", error_response)."""
    specs = embed_builder.specs_from_body(body)
    content = body.get("content") or ""
    if specs is None or not isinstance(content, str):
        return [], "", web.json_response({"error": "invalid_request"}, status=400)
    error_code = embed_builder.validate_embed_specs(specs, content)
    if error_code:
        return [], "", web.json_response({"error": error_code}, status=400)
    return specs, content, None


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

    specs, content, error = _parse_embeds_and_content(body)
    if error:
        return error

    role_ids, error = _validate_role_ids_structure(body.get("role_ids") or [])
    if error:
        return error

    channel = guild.get_channel(channel_id)
    if channel is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    error = _validate_role_ids_assignable(role_ids, guild)
    if error:
        return error

    embeds = [embed_builder.build_embed(spec) for spec in specs]
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None
    components_version = body.get("components_version")
    if components_version is None:
        components_version = embed_builder.get_components_version(request["guild_id"])
    else:
        components_version = embed_builder.set_components_version(request["guild_id"], str(components_version))

    import bot.core.components_v2 as components_v2

    try:
        message = await components_v2.send_message(
            channel,
            version=components_version,
            content=content or None,
            embeds=embeds,
            view=view,
            detach_layout=True,
            enforce_limits=True,
        )
    except components_v2.LayoutTooLargeError:
        return web.json_response({"error": "v2_too_large"}, status=400)
    except discord.HTTPException as exc:
        logger.warning("Failed to send embed message to channel %s: %s", channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response(
        {
            "message_id": str(message.id),
            "channel_id": str(channel_id),
            "components_version": components_v2.normalize_version(components_version),
        },
        status=201,
    )


@routes.get("/api/embed-templates")
@require_dashboard_access
async def list_embed_templates(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    return web.json_response(
        {
            "templates": embed_builder.list_templates(guild_id),
            "components_version": embed_builder.get_components_version(guild_id),
        }
    )


@routes.put("/api/embed-templates/components-version")
@require_dashboard_access
async def put_embed_components_version(request: web.Request) -> web.Response:
    body, error = await _parse_body(request)
    if error:
        return error
    version = embed_builder.set_components_version(request["guild_id"], str(body.get("components_version") or "v1"))
    return web.json_response({"components_version": version})


@routes.post("/api/embed-templates")
@require_dashboard_access
async def create_embed_template(request: web.Request) -> web.Response:
    body, error = await _parse_body(request)
    if error:
        return error

    name = body.get("name", "")
    if not isinstance(name, str) or not name.strip() or len(name) > 60:
        return web.json_response({"error": "invalid_name"}, status=400)

    spec = body.get("embed") or {}
    content = body.get("content") or ""
    error_code = embed_builder.validate_embed_spec(spec, content)
    if error_code:
        return web.json_response({"error": error_code}, status=400)

    role_ids_raw = body.get("role_ids") or []
    _, error = _validate_role_ids_structure(role_ids_raw)
    if error:
        return error

    result = embed_builder.save_template(request["guild_id"], name.strip(), content, spec, [str(r) for r in role_ids_raw])
    if isinstance(result, str):
        return web.json_response({"error": result}, status=409 if result == "duplicate_name" else 400)
    return web.json_response(result, status=201)


@routes.delete("/api/embed-templates/{template_id}")
@require_dashboard_access
async def delete_embed_template(request: web.Request) -> web.Response:
    if not embed_builder.delete_template(request["guild_id"], request.match_info["template_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


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

    try:
        payload = embed_builder.message_to_editor_payload(message)
    except Exception:
        logger.exception("Failed to parse embed message %s in channel %s", message_id, channel_id)
        is_v2 = bool(getattr(getattr(message, "flags", None), "components_v2", False))
        payload = {
            "content": getattr(message, "content", None) or "",
            "embeds": [],
            "embed": embed_builder.empty_embed_spec(),
            "role_ids": [],
            "components_version": "v2" if is_v2 else "v1",
        }

    return web.json_response(payload)


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

    specs, content, error = _parse_embeds_and_content(body)
    if error:
        return error

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

    embeds = [embed_builder.build_embed(spec) for spec in specs]
    view = embed_builder.build_role_button_view(guild, role_ids) if role_ids else None
    components_version = body.get("components_version")
    if components_version is None:
        # Prefer flag already on the message; else guild default.
        if getattr(getattr(message, "flags", None), "components_v2", False):
            components_version = "v2"
        else:
            components_version = embed_builder.get_components_version(request["guild_id"])
    else:
        components_version = embed_builder.set_components_version(request["guild_id"], str(components_version))

    import bot.core.components_v2 as components_v2

    try:
        await components_v2.edit_message(
            message,
            version=components_version,
            content=content or None,
            embeds=embeds,
            view=view,
            detach_layout=True,
            enforce_limits=True,
        )
    except components_v2.LayoutTooLargeError:
        return web.json_response({"error": "v2_too_large"}, status=400)
    except discord.HTTPException as exc:
        logger.warning("Failed to edit embed message %s in channel %s: %s", message_id, channel_id, exc)
        return web.json_response({"error": "discord_error"}, status=502)

    return web.json_response(
        {
            "message_id": str(message_id),
            "channel_id": str(channel_id),
            "components_version": components_v2.normalize_version(components_version),
        }
    )
