import os

from aiohttp import web

import i18n
import stats_db
import xp_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

MAX_BG_SIZE = 5 * 1024 * 1024
PAGE_SIZE = 25


def _is_id_list(value) -> bool:
    return isinstance(value, list) and all(isinstance(v, str) and v.isdigit() for v in value)


def _int_in(value, lo, hi) -> bool:
    return isinstance(value, int) and lo <= value <= hi


def _serialize_row(row, guild, rank: int) -> dict:
    member = guild.get_member(row["user_id"]) if guild else None
    level, into, step = xp_core.level_progress(row["xp"])
    return {
        "user_id": str(row["user_id"]),
        "display": member.display_name if member else str(row["user_id"]),
        "avatar": str(member.display_avatar.url) if member else None,
        "on_server": member is not None,
        "xp": row["xp"],
        "level": level,
        "xp_into_level": into,
        "xp_step": step,
        "messages": row["messages"],
        "voice_seconds": row["voice_seconds"],
        "voice_time_text": xp_core.format_voice_time(row["voice_seconds"]),
        "rank": rank,
    }


# ────────────────── Настройки ──────────────────

@routes.get("/api/xp")
@require_dashboard_access
async def xp_get(request: web.Request) -> web.Response:
    return web.json_response({
        "settings": xp_core.get_settings(request["guild_id"]),
        "member_count": stats_db.xp_member_count(request["guild_id"]),
        "has_card_bg": os.path.exists(xp_core.get_card_bg_path(request["guild_id"])),
    })


@routes.put("/api/xp")
@require_dashboard_access
async def xp_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for flag in ("enabled", "public_leaderboard", "reset_on_leave"):
        if not isinstance(body.get(flag, False), bool):
            return web.json_response({"error": f"invalid_{flag}"}, status=400)

    for scope_name in ("text", "voice"):
        scope = body.get(scope_name, {})
        if not isinstance(scope, dict):
            return web.json_response({"error": f"invalid_{scope_name}"}, status=400)
        if not isinstance(scope.get("enabled", True), bool):
            return web.json_response({"error": f"invalid_{scope_name}"}, status=400)
        for list_key in ("ignored_roles", "target_channels", "ignored_channels"):
            if not _is_id_list(scope.get(list_key, [])):
                return web.json_response({"error": f"invalid_{scope_name}_{list_key}"}, status=400)
        if not _int_in(scope.get("multiplier", 100), 0, 1000):
            return web.json_response({"error": f"invalid_{scope_name}_multiplier"}, status=400)
    if not _int_in(body.get("voice", {}).get("max_count", 5), 0, 99):
        return web.json_response({"error": "invalid_voice_max_count"}, status=400)
    if not _int_in(body.get("voice", {}).get("base_per_minute", xp_core.VOICE_XP_PER_ACTIVE_MINUTE), 1, 100):
        return web.json_response({"error": "invalid_voice_base_per_minute"}, status=400)
    member_multipliers = body.get("voice", {}).get("member_multipliers", {})
    if not isinstance(member_multipliers, dict):
        return web.json_response({"error": "invalid_voice_member_multipliers"}, status=400)
    for user_id, mult in member_multipliers.items():
        if not isinstance(user_id, str) or not user_id.isdigit() or not _int_in(mult, 0, 1000):
            return web.json_response({"error": "invalid_voice_member_multipliers"}, status=400)

    announce = body.get("announce", {})
    if not isinstance(announce, dict) or not isinstance(announce.get("enabled", True), bool):
        return web.json_response({"error": "invalid_announce"}, status=400)
    channel_id = announce.get("channel_id", "")
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_announce_channel"}, status=400)
    if not isinstance(announce.get("template", ""), str) or len(announce.get("template", "")) > 1500:
        return web.json_response({"error": "invalid_announce_template"}, status=400)
    if not _int_in(announce.get("delete_after", 0), 0, 3600):
        return web.json_response({"error": "invalid_announce_delete_after"}, status=400)

    level_rewards = body.get("level_rewards", [])
    if not isinstance(level_rewards, list):
        return web.json_response({"error": "invalid_level_rewards"}, status=400)
    seen_levels = set()
    for reward in level_rewards:
        if not isinstance(reward, dict) or not _int_in(reward.get("level"), 1, xp_core.MAX_LEVEL) or not _is_id_list(reward.get("role_ids", [])):
            return web.json_response({"error": "invalid_level_rewards"}, status=400)
        if reward["level"] in seen_levels:
            return web.json_response({"error": "duplicate_level_reward"}, status=400)
        seen_levels.add(reward["level"])

    voice_rewards = body.get("voice_rewards", [])
    if not isinstance(voice_rewards, list):
        return web.json_response({"error": "invalid_voice_rewards"}, status=400)
    seen_minutes = set()
    for reward in voice_rewards:
        if not isinstance(reward, dict) or not _int_in(reward.get("minutes"), 1, 10_000_000) or not _is_id_list(reward.get("role_ids", [])):
            return web.json_response({"error": "invalid_voice_rewards"}, status=400)
        if reward["minutes"] in seen_minutes:
            return web.json_response({"error": "duplicate_voice_reward"}, status=400)
        seen_minutes.add(reward["minutes"])

    guild_id = request["guild_id"]
    xp_core.save_config(guild_id, {
        "enabled": body.get("enabled", False),
        "public_leaderboard": body.get("public_leaderboard", False),
        "reset_on_leave": body.get("reset_on_leave", False),
        "text": {
            "enabled": body["text"].get("enabled", True),
            "ignored_roles": body["text"].get("ignored_roles", []),
            "target_channels": body["text"].get("target_channels", []),
            "ignored_channels": body["text"].get("ignored_channels", []),
            "multiplier": body["text"].get("multiplier", 100),
        },
        "voice": {
            "enabled": body["voice"].get("enabled", True),
            "ignored_roles": body["voice"].get("ignored_roles", []),
            "target_channels": body["voice"].get("target_channels", []),
            "ignored_channels": body["voice"].get("ignored_channels", []),
            "multiplier": body["voice"].get("multiplier", 100),
            "max_count": body["voice"].get("max_count", 5),
            "base_per_minute": body["voice"].get("base_per_minute", xp_core.VOICE_XP_PER_ACTIVE_MINUTE),
            "member_multipliers": member_multipliers,
        },
        "announce": {
            "enabled": announce.get("enabled", True),
            "channel_id": channel_id,
            "template": announce.get("template", xp_core.DEFAULT_ANNOUNCE_TEMPLATE),
            "delete_after": announce.get("delete_after", 0),
        },
        "level_rewards": sorted(level_rewards, key=lambda r: r["level"]),
        "voice_rewards": sorted(voice_rewards, key=lambda r: r["minutes"]),
    })
    return web.json_response({"settings": xp_core.get_settings(guild_id)})


# ────────────────── Лидерборд и участники ──────────────────

@routes.get("/api/xp/leaderboard")
@require_dashboard_access
async def xp_leaderboard(request: web.Request) -> web.Response:
    """Вкладка «Участники» дашборда: весь ростер гильдии, а не только те,
    кто уже где-то отметился — иначе большая часть сервера невидима админу.
    Публичный топ (/api/public/leaderboard) не трогаем — там осознанно
    только реально заработавшие XP."""
    guild = request.app["bot"].get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        page = max(1, int(request.query.get("page", "1")))
    except ValueError:
        page = 1
    search = request.query.get("search", "").strip().lower()

    xp_by_user = {row["user_id"]: row for row in stats_db.xp_all_members(request["guild_id"])}

    rows: list[dict] = []
    for member in guild.members:
        if member.bot:
            continue
        row = xp_by_user.pop(member.id, None)
        rows.append({
            "user_id": member.id,
            "xp": row["xp"] if row else 0,
            "messages": row["messages"] if row else 0,
            "voice_seconds": row["voice_seconds"] if row else 0,
        })
    # Оставшиеся записи — участники, покинувшие сервер, но ещё числящиеся в рейтинге.
    for user_id, row in xp_by_user.items():
        rows.append({
            "user_id": user_id,
            "xp": row["xp"],
            "messages": row["messages"],
            "voice_seconds": row["voice_seconds"],
        })

    if search:
        def matches(row: dict) -> bool:
            member = guild.get_member(row["user_id"])
            haystack = member.display_name.lower() if member else str(row["user_id"])
            return search in haystack

        rows = [r for r in rows if matches(r)]

    rows.sort(key=lambda r: r["xp"], reverse=True)

    total = len(rows)
    offset = (page - 1) * PAGE_SIZE
    page_rows = rows[offset:offset + PAGE_SIZE]

    return web.json_response({
        "total": total,
        "page": page,
        "page_size": PAGE_SIZE,
        "entries": [_serialize_row(row, guild, offset + i + 1) for i, row in enumerate(page_rows)],
    })


@routes.put("/api/xp/members/{user_id}")
@require_dashboard_access
async def xp_member_set(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    if guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        user_id = int(request.match_info["user_id"])
        body = await request.json()
        xp_value = body["xp"]
    except (ValueError, KeyError, TypeError):
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(xp_value, int) or not xp_core.XP_ADMIN_MIN <= xp_value <= xp_core.XP_ADMIN_MAX:
        return web.json_response({"error": "invalid_xp"}, status=400)

    member = guild.get_member(user_id)
    cog = bot.get_cog("XPCog")
    if member is not None and cog is not None:
        await cog.set_member_xp(member, xp_value)
    else:
        stats_db.xp_set_xp(request["guild_id"], user_id, xp_value, xp_core.level_from_xp(xp_value))
    return web.json_response({"ok": True, "level": xp_core.level_from_xp(xp_value)})


@routes.post("/api/xp/members/{user_id}/reset")
@require_dashboard_access
async def xp_member_reset(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    try:
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)

    member = guild.get_member(user_id) if guild else None
    cog = bot.get_cog("XPCog")
    if member is not None and cog is not None:
        await cog.reset_member(member)
    else:
        stats_db.xp_reset_member(request["guild_id"], user_id)
    return web.json_response({"ok": True})


@routes.post("/api/xp/reset-all")
@require_dashboard_access
async def xp_reset_all(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    guild = bot.get_guild(request["guild_id"])
    cog = bot.get_cog("XPCog")

    # Снимаем награды у всех, кто есть в рейтинге и на сервере
    if guild is not None and cog is not None:
        settings = xp_core.get_settings(request["guild_id"])
        for row in stats_db.xp_leaderboard(request["guild_id"], limit=100000):
            member = guild.get_member(row["user_id"])
            if member is not None:
                await cog.sync_reward_roles(member, {**settings, "level_rewards": [], "voice_rewards": []}, 0, 0)

    stats_db.xp_reset_all(request["guild_id"])
    return web.json_response({"ok": True})


# ────────────────── Фон карточки ──────────────────

@routes.post("/api/xp/card-bg")
@require_dashboard_access
async def xp_card_bg_upload(request: web.Request) -> web.Response:
    body = await request.read()
    if not body or len(body) > MAX_BG_SIZE:
        return web.json_response({"error": "invalid_size"}, status=400)
    # PNG или JPEG по сигнатуре
    if not (body.startswith(b"\x89PNG") or body.startswith(b"\xff\xd8\xff")):
        return web.json_response({"error": "invalid_format"}, status=400)
    with open(xp_core.get_card_bg_path(request["guild_id"]), "wb") as f:
        f.write(body)
    return web.json_response({"ok": True})


@routes.delete("/api/xp/card-bg")
@require_dashboard_access
async def xp_card_bg_delete(request: web.Request) -> web.Response:
    if os.path.exists(xp_core.get_card_bg_path(request["guild_id"])):
        os.remove(xp_core.get_card_bg_path(request["guild_id"]))
    return web.json_response({"ok": True})


# ────────────────── Публичный лидерборд ──────────────────

def _public_leaderboard_payload(bot, guild_id: int) -> web.Response | dict:
    settings = xp_core.get_settings(guild_id)
    if not settings["enabled"] or not settings["public_leaderboard"]:
        return web.json_response({"error": "not_found"}, status=404)

    guild = bot.get_guild(guild_id)
    lang = i18n.lang_for(guild_id)
    left_label = i18n.t("xp.leaderboard.left_server", lang)
    rows = stats_db.xp_leaderboard(guild_id, limit=100)
    entries = []
    for i, row in enumerate(rows):
        member = guild.get_member(row["user_id"]) if guild else None
        level, into, step = xp_core.level_progress(row["xp"])
        entries.append({
            "rank": i + 1,
            "display": member.display_name if member else left_label,
            "avatar": str(member.display_avatar.url) if member else None,
            "level": level,
            "xp": row["xp"],
            "voice_time_text": xp_core.format_voice_time(row["voice_seconds"]),
        })
    return {
        "guild_id": str(guild_id),
        "guild_name": guild.name if guild else "",
        "entries": entries,
    }


@routes.get("/api/public/leaderboard")
async def xp_public_leaderboard(request: web.Request) -> web.Response:
    """Legacy URL: require guild_id query param. Prefer /api/public/leaderboard/{guild_id}."""
    raw = request.rel_url.query.get("guild_id")
    if raw is None or raw == "":
        return web.json_response(
            {
                "error": "guild_id_required",
                "hint": "Use /api/public/leaderboard/{guild_id}",
            },
            status=400,
        )
    try:
        guild_id = int(raw)
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    payload = _public_leaderboard_payload(request.app["bot"], guild_id)
    if isinstance(payload, web.Response):
        return payload
    return web.json_response(payload)


@routes.get("/api/public/leaderboard/{guild_id}")
async def xp_public_leaderboard_for_guild(request: web.Request) -> web.Response:
    try:
        guild_id = int(request.match_info["guild_id"])
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_request"}, status=400)

    payload = _public_leaderboard_payload(request.app["bot"], guild_id)
    if isinstance(payload, web.Response):
        return payload
    return web.json_response(payload)
