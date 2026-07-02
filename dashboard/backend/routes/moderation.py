import discord
from aiohttp import web

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def serialize_member_summary(member) -> dict:
    return {
        "id": str(member.id),
        "username": member.name,
        "display_name": member.display_name,
        "avatar": str(member.display_avatar.url) if member.display_avatar else None,
        "role_count": max(0, len(member.roles) - 1),  # exclude @everyone
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "is_bot": member.bot,
    }


def _get_guild_or_none(request):
    return request.app["bot"].get_guild(request.app["guild_id"])


@routes.get("/api/members")
@require_dashboard_access
async def list_members(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    search = request.query.get("search", "").strip().lower()
    try:
        page = max(1, int(request.query.get("page", "1")))
        page_size = min(100, max(1, int(request.query.get("page_size", "20"))))
    except ValueError:
        return web.json_response({"error": "invalid_pagination"}, status=400)

    members = list(guild.members)
    if search:
        members = [
            m
            for m in members
            if search in m.name.lower() or search in m.display_name.lower()
        ]

    total = len(members)
    start = (page - 1) * page_size
    page_items = members[start : start + page_size]

    return web.json_response(
        {
            "total": total,
            "page": page,
            "page_size": page_size,
            "members": [serialize_member_summary(m) for m in page_items],
        }
    )


def serialize_member_detail(member, bot) -> dict:
    stats = bot.stats.get(str(member.id), {"joins": 0, "leaves": 0, "invites": 0})
    case_count = sum(
        1 for c in bot.feedback_cases.values() if c.get("submitter_id") == member.id
    )
    roles = [
        {"id": str(r.id), "name": r.name, "color": f"#{r.color.value:06x}"}
        for r in member.roles
        if not r.is_default()
    ]
    return {
        "id": str(member.id),
        "username": member.name,
        "display_name": member.display_name,
        "avatar": str(member.display_avatar.url) if member.display_avatar else None,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat(),
        "roles": roles,
        "invite_stats": {
            "joins": stats.get("joins", 0),
            "leaves": stats.get("leaves", 0),
            "invites": stats.get("invites", 0),
        },
        "feedback_case_count": case_count,
        "is_bot": member.bot,
    }


def _parse_member_id(request):
    try:
        return int(request.match_info["member_id"])
    except ValueError:
        return None


@routes.get("/api/members/{member_id}")
@require_dashboard_access
async def member_detail(request: web.Request) -> web.Response:
    guild = _get_guild_or_none(request)
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    member_id = _parse_member_id(request)
    if member_id is None:
        return web.json_response({"error": "invalid_member_id"}, status=400)

    member = guild.get_member(member_id)
    if member is None:
        return web.json_response({"error": "member_not_found"}, status=404)

    return web.json_response(serialize_member_detail(member, request.app["bot"]))


ALLOWED_DELETE_DAYS = {0, 1, 7}


def dashboard_reason(reason: str, moderator) -> str:
    return f"Dashboard: {reason} — by {moderator.name} ({moderator.id})"


async def _send_action_log(bot, title: str, target, moderator, reason: str, extra: str = ""):
    embed = discord.Embed(title=title, color=discord.Color.red(), timestamp=bot.utcnow())
    embed.add_field(name="Кто", value=f"{moderator.name} (`{moderator.id}`)", inline=False)
    embed.add_field(name="Кого", value=f"{target.name} (`{target.id}`)", inline=False)
    embed.add_field(name="Причина", value=reason, inline=False)
    if extra:
        embed.add_field(name="Дополнительно", value=extra, inline=False)
    embed.set_footer(text="Dashboard · Moderation")
    await bot.send_log(embed)


def _get_target_or_response(request):
    """Returns (member, None) or (None, error Response)."""
    guild = _get_guild_or_none(request)
    if guild is None:
        return None, web.json_response({"error": "service_unavailable"}, status=503)
    member_id = _parse_member_id(request)
    if member_id is None:
        return None, web.json_response({"error": "invalid_member_id"}, status=400)
    member = guild.get_member(member_id)
    if member is None:
        return None, web.json_response({"error": "member_not_found"}, status=404)
    return member, None


def _map_discord_error(exc):
    if isinstance(exc, discord.Forbidden):
        return web.json_response({"error": "forbidden_by_discord"}, status=403)
    if isinstance(exc, discord.NotFound):
        return web.json_response({"error": "member_not_found"}, status=404)
    return web.json_response({"error": "discord_error"}, status=502)


@routes.post("/api/members/{member_id}/ban")
@require_dashboard_access
async def ban_member(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    reason = (body.get("reason") or "").strip()
    days = body.get("delete_message_days", 0)
    if not reason or days not in ALLOWED_DELETE_DAYS:
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    full_reason = dashboard_reason(reason, moderator)
    try:
        await target.ban(reason=full_reason, delete_message_seconds=days * 86400)
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "🔨 Бан через дашборд", target, moderator, reason,
        extra=f"Удаление сообщений: {days} дн.",
    )
    return web.json_response({"ok": True})


@routes.post("/api/members/{member_id}/kick")
@require_dashboard_access
async def kick_member(request: web.Request) -> web.Response:
    target, error = _get_target_or_response(request)
    if error:
        return error

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    reason = (body.get("reason") or "").strip()
    if not reason:
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    try:
        await target.kick(reason=dashboard_reason(reason, moderator))
    except discord.HTTPException as exc:
        return _map_discord_error(exc)

    await _send_action_log(
        request.app["bot"], "👢 Кик через дашборд", target, moderator, reason
    )
    return web.json_response({"ok": True})
