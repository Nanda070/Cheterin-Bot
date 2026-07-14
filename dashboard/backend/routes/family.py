from aiohttp import web

import family_core
import family_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

PAGE_SIZE = 25
VALID_STATUSES = {"open", "approved", "denied", "closed"}


def _is_id(value) -> bool:
    return isinstance(value, str) and (value == "" or value.isdigit())


def _is_id_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v.isdigit() for v in value)


def _display_name(guild, user_id: int) -> str:
    member = guild.get_member(user_id) if guild else None
    return member.display_name if member else str(user_id)


# ────────────────────────── Настройки ──────────────────────────

@routes.get("/api/family")
@require_dashboard_access
async def family_get(request: web.Request) -> web.Response:
    return web.json_response(family_core.get_settings())


@routes.put("/api/family")
@require_dashboard_access
async def family_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    roster = body.get("roster", {})
    if not isinstance(roster, dict) or not _is_id(roster.get("list_channel_id", "")):
        return web.json_response({"error": "invalid_roster"}, status=400)
    target_roles = roster.get("target_roles", [])
    if not isinstance(target_roles, list):
        return web.json_response({"error": "invalid_roster_target_roles"}, status=400)
    for entry in target_roles:
        if not isinstance(entry, dict) or not isinstance(entry.get("label", ""), str) or not _is_id(entry.get("role_id", "")):
            return web.json_response({"error": "invalid_roster_target_roles"}, status=400)

    applications = body.get("applications", {})
    if not isinstance(applications, dict):
        return web.json_response({"error": "invalid_applications"}, status=400)
    for key in ("application_channel_id", "log_channel_id", "ticket_manager_role_id", "notify_role_id", "ticket_active_role_id", "yes_emoji_id", "no_emoji_id"):
        if not _is_id(applications.get(key, "")):
            return web.json_response({"error": f"invalid_{key}"}, status=400)
    if not _is_id_list(applications.get("staff_role_ids", [])):
        return web.json_response({"error": "invalid_staff_role_ids"}, status=400)
    if not _is_id_list(applications.get("approve_role_ids", [])):
        return web.json_response({"error": "invalid_approve_role_ids"}, status=400)
    archive_minutes = applications.get("thread_archive_minutes", 10080)
    if not isinstance(archive_minutes, int) or not 60 <= archive_minutes <= 10080:
        return web.json_response({"error": "invalid_thread_archive_minutes"}, status=400)

    birthdays = body.get("birthdays", {})
    if not isinstance(birthdays, dict) or not _is_id(birthdays.get("channel_id", "")) or not _is_id(birthdays.get("list_channel_id", "")):
        return web.json_response({"error": "invalid_birthdays"}, status=400)

    family_core.save_config({
        "enabled": body["enabled"],
        "roster": {
            "list_channel_id": roster.get("list_channel_id", ""),
            "target_roles": [
                {"label": e.get("label", ""), "role_id": e.get("role_id", "")} for e in target_roles
            ],
        },
        "applications": {
            "application_channel_id": applications.get("application_channel_id", ""),
            "log_channel_id": applications.get("log_channel_id", ""),
            "staff_role_ids": applications.get("staff_role_ids", []),
            "ticket_manager_role_id": applications.get("ticket_manager_role_id", ""),
            "notify_role_id": applications.get("notify_role_id", ""),
            "ticket_active_role_id": applications.get("ticket_active_role_id", ""),
            "approve_role_ids": applications.get("approve_role_ids", []),
            "yes_emoji_id": applications.get("yes_emoji_id", ""),
            "no_emoji_id": applications.get("no_emoji_id", ""),
            "thread_archive_minutes": archive_minutes,
        },
        "birthdays": {
            "channel_id": birthdays.get("channel_id", ""),
            "list_channel_id": birthdays.get("list_channel_id", ""),
        },
    })
    return web.json_response(family_core.get_settings())


# ────────────────────────── Ростер ──────────────────────────

@routes.get("/api/family/roster")
@require_dashboard_access
async def family_roster(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    groups = []
    for entry in family_core.get_settings()["roster"]["target_roles"]:
        role = guild.get_role(int(entry["role_id"])) if entry["role_id"] else None
        groups.append({
            "label": entry["label"] or (role.name if role else entry["role_id"]),
            "role_id": entry["role_id"],
            "role_found": role is not None,
            "members": [
                {"id": str(m.id), "display": m.display_name} for m in (role.members if role else [])
            ],
        })
    return web.json_response({"groups": groups})


# ────────────────────────── Заявки ──────────────────────────

def _serialize_ticket(row: dict, guild) -> dict:
    return {
        "user_id": str(row["user_id"]),
        "display": _display_name(guild, row["user_id"]),
        "status": row["status"],
        "nickname": row["nickname"],
        "game_level": row["game_level"],
        "faction_pref": row["faction_pref"],
        "online_timezone": row["online_timezone"],
        "real_name": row["real_name"],
        "real_age": row["real_age"],
        "about_text": row["about_text"],
        "why_join": row["why_join"],
        "inviter_nickname": row["inviter_nickname"],
        "created_at": row["created_at"],
        "handled_by": str(row["handled_by"]) if row["handled_by"] else None,
        "thread_id": str(row["thread_id"]) if row["thread_id"] else None,
    }


@routes.get("/api/family/tickets")
@require_dashboard_access
async def family_tickets_list(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])

    status = request.query.get("status") or None
    if status and status not in VALID_STATUSES:
        return web.json_response({"error": "invalid_status"}, status=400)
    try:
        page = max(1, int(request.query.get("page", "1")))
    except ValueError:
        page = 1
    offset = (page - 1) * PAGE_SIZE

    rows = family_db.list_tickets(status=status, limit=PAGE_SIZE, offset=offset)
    total = family_db.count_tickets(status=status)
    return web.json_response({
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "entries": [_serialize_ticket(r, guild) for r in rows],
    })


async def _decide_ticket(request: web.Request, status: str) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    cog = bot.get_cog("FamilyTicketsCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    moderator = request["moderator"]
    result = await cog.resolve_ticket_by_user(guild, user_id, status, moderator)
    if not result.ok:
        code = 404 if result.error in ("not_open", "thread_not_found", "member_not_found") else 400
        return web.json_response({"error": result.error}, status=code)
    return web.json_response({"ok": True})


@routes.post("/api/family/tickets/{user_id}/approve")
@require_dashboard_access
async def family_ticket_approve(request: web.Request) -> web.Response:
    return await _decide_ticket(request, "approved")


@routes.post("/api/family/tickets/{user_id}/deny")
@require_dashboard_access
async def family_ticket_deny(request: web.Request) -> web.Response:
    return await _decide_ticket(request, "denied")


@routes.post("/api/family/tickets/{user_id}/close")
@require_dashboard_access
async def family_ticket_close(request: web.Request) -> web.Response:
    return await _decide_ticket(request, "closed")


# ────────────────────────── Дни рождения ──────────────────────────

@routes.get("/api/family/birthdays")
@require_dashboard_access
async def family_birthdays_list(request: web.Request) -> web.Response:
    guild = request.app["bot"].get_guild(request.app["guild_id"])
    rows = family_db.get_all_birthdays(request.app["guild_id"])
    return web.json_response({
        "entries": [
            {
                "user_id": str(r["user_id"]),
                "display": _display_name(guild, r["user_id"]),
                "day": r["day"],
                "month": r["month"],
                "date_display": r["date_display"],
            }
            for r in rows
        ],
    })


@routes.post("/api/family/birthdays")
@require_dashboard_access
async def family_birthday_set(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
        user_id = int(body["user_id"])
        date_str = body["date"]
    except (ValueError, KeyError, TypeError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(date_str, str):
        return web.json_response({"error": "invalid_request"}, status=400)

    if guild.get_member(user_id) is None:
        return web.json_response({"error": "member_not_found"}, status=404)

    try:
        day, month, display = family_core.parse_birthday_date(date_str)
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    family_db.save_birthday(user_id, request.app["guild_id"], day, month, display)

    cog = bot.get_cog("BirthdayCog")
    if cog is not None:
        await cog.update_birthday_message(guild)

    return web.json_response({"ok": True, "date_display": display})


@routes.delete("/api/family/birthdays/{user_id}")
@require_dashboard_access
async def family_birthday_delete(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request.app["guild_id"])
    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    deleted = family_db.delete_birthday(user_id)
    if not deleted:
        return web.json_response({"error": "not_found"}, status=404)

    cog = bot.get_cog("BirthdayCog") if bot else None
    if cog is not None and guild is not None:
        await cog.update_birthday_message(guild)

    return web.json_response({"ok": True})
