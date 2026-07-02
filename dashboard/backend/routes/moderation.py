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
