import time
from collections import defaultdict
from datetime import datetime, timedelta, timezone

from aiohttp import web

import stats_db
import xp_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

MSK = timezone(timedelta(hours=3))


@routes.get("/api/voice-stats")
@require_dashboard_access
async def voice_stats(request: web.Request) -> web.Response:
    try:
        days = min(180, max(1, int(request.query.get("days", "30"))))
    except ValueError:
        days = 30

    guild = request.app["bot"].get_guild(request["guild_id"])
    since_ts = int(time.time()) - days * 24 * 3600
    sessions = stats_db.voice_sessions_since(request["guild_id"], since_ts)

    by_hour = [0] * 24          # суммарные минуты по часам суток (МСК)
    by_weekday = [0] * 7        # суммарные минуты по дням недели (0=Пн)
    by_channel: dict[int, dict] = {}
    by_user: dict[int, int] = defaultdict(int)
    total_seconds = 0
    events: list[tuple[int, int]] = []  # (ts, +1/-1) для пикового онлайна

    for row in sessions:
        start, end = row["joined_ts"], row["left_ts"]
        if end <= start:
            continue
        duration = end - start
        total_seconds += duration
        by_user[row["user_id"]] += duration

        ch = by_channel.setdefault(row["channel_id"], {"name": row["channel_name"], "seconds": 0})
        ch["seconds"] += duration
        channel = guild.get_channel(row["channel_id"]) if guild else None
        if channel is not None:
            ch["name"] = channel.name

        events.append((start, 1))
        events.append((end, -1))

        # Распределение по часам/дням: идём по часовым срезам сессии
        cursor = start
        while cursor < end:
            dt = datetime.fromtimestamp(cursor, MSK)
            hour_end = int(dt.replace(minute=0, second=0, microsecond=0).timestamp()) + 3600
            chunk = min(end, hour_end) - cursor
            by_hour[dt.hour] += chunk
            by_weekday[dt.weekday()] += chunk
            cursor += chunk

    # Пиковый одновременный онлайн
    peak = 0
    current = 0
    for _, delta in sorted(events):
        current += delta
        peak = max(peak, current)

    top_channels = sorted(by_channel.values(), key=lambda c: c["seconds"], reverse=True)[:10]
    top_users_raw = sorted(by_user.items(), key=lambda kv: kv[1], reverse=True)[:10]
    top_users = []
    for user_id, seconds in top_users_raw:
        member = guild.get_member(user_id) if guild else None
        top_users.append({
            "user_id": str(user_id),
            "display": member.display_name if member else str(user_id),
            "avatar": str(member.display_avatar.url) if member else None,
            "seconds": seconds,
            "time_text": xp_core.format_voice_time(seconds),
        })

    return web.json_response({
        "days": days,
        "session_count": len(sessions),
        "total_seconds": total_seconds,
        "total_time_text": xp_core.format_voice_time(total_seconds),
        "peak_concurrent": peak,
        "by_hour_minutes": [s // 60 for s in by_hour],
        "by_weekday_minutes": [s // 60 for s in by_weekday],
        "top_channels": [
            {"name": c["name"], "seconds": c["seconds"], "time_text": xp_core.format_voice_time(c["seconds"])}
            for c in top_channels
        ],
        "top_users": top_users,
    })
