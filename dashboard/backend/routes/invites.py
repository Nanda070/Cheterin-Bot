import asyncio

from aiohttp import web

import bot.modules.community.invites_core as invites_core
import bot.modules.community.invites_db as invites_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

_FETCH_CONCURRENCY = 8


def _cached_display(bot, guild, user_id: int) -> str | None:
    if guild is not None:
        member = guild.get_member(user_id)
        if member is not None:
            return member.display_name
    user = bot.get_user(user_id) if bot else None
    if user is not None:
        return getattr(user, "display_name", None) or getattr(user, "name", None) or str(user_id)
    return None


async def _resolve_displays(bot, guild, user_ids: set[int]) -> dict[int, str]:
    """Resolve display names with cache-first lookup and deduped concurrent fetches."""
    resolved: dict[int, str] = {}
    missing: list[int] = []
    for user_id in user_ids:
        cached = _cached_display(bot, guild, user_id)
        if cached is not None:
            resolved[user_id] = cached
        else:
            missing.append(user_id)

    if missing and bot is not None:
        sem = asyncio.Semaphore(_FETCH_CONCURRENCY)

        async def _fetch_one(uid: int) -> tuple[int, str]:
            async with sem:
                try:
                    fetched = await bot.fetch_user(uid)
                    name = (
                        getattr(fetched, "display_name", None)
                        or getattr(fetched, "name", None)
                        or str(uid)
                    )
                    return uid, name
                except Exception:
                    return uid, str(uid)

        pairs = await asyncio.gather(*(_fetch_one(uid) for uid in missing))
        resolved.update(pairs)

    for user_id in user_ids:
        resolved.setdefault(user_id, str(user_id))
    return resolved


@routes.get("/api/invites")
@require_dashboard_access
async def invites_get(request: web.Request) -> web.Response:
    guild_id = request["guild_id"]
    bot = request.app["bot"]
    guild = bot.get_guild(guild_id)
    settings = invites_core.get_settings(guild_id)

    inviter_rows = list(invites_db.inviter_stats(guild_id))
    join_rows = list(invites_db.recent_joins(guild_id, 50))

    user_ids: set[int] = set()
    for row in inviter_rows:
        user_ids.add(int(row["inviter_id"]))
    for row in join_rows:
        user_ids.add(int(row["invitee_id"]))
        if row["inviter_id"] is not None:
            user_ids.add(int(row["inviter_id"]))

    displays = await _resolve_displays(bot, guild, user_ids)

    stats = [
        {
            "inviter_id": str(int(row["inviter_id"])),
            "inviter_display": displays.get(int(row["inviter_id"]), str(int(row["inviter_id"]))),
            "joins": row["joins"],
        }
        for row in inviter_rows
    ]

    recent_joins = []
    for row in join_rows:
        invitee_id = int(row["invitee_id"])
        inviter_id = int(row["inviter_id"]) if row["inviter_id"] is not None else None
        recent_joins.append(
            {
                "invitee_id": str(invitee_id),
                "invitee_display": displays.get(invitee_id, str(invitee_id)),
                "inviter_id": str(inviter_id) if inviter_id is not None else None,
                "inviter_display": displays.get(inviter_id) if inviter_id is not None else None,
                "code": row["code"],
                "joined_at": row["joined_at"],
            }
        )

    return web.json_response({
        **settings,
        "stats": stats,
        "recent_joins": recent_joins,
    })


@routes.put("/api/invites")
@require_dashboard_access
async def invites_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    welcome_mention = body.get("welcome_mention", False)
    log_channel_id = body.get("log_channel_id", "")

    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if not isinstance(welcome_mention, bool):
        return web.json_response({"error": "invalid_welcome_mention"}, status=400)
    if not isinstance(log_channel_id, str) or (log_channel_id and not log_channel_id.isdigit()):
        return web.json_response({"error": "invalid_log_channel_id"}, status=400)

    settings = invites_core.save_settings(
        request["guild_id"],
        enabled=enabled,
        welcome_mention=welcome_mention,
        log_channel_id=log_channel_id,
    )
    return web.json_response(settings)
