from aiohttp import web

import streams

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

EDITABLE_FIELDS = {
    "enabled", "channel_id", "ping_role_id", "template", "keywords",
    "keyword_mode", "min_interval_minutes", "mention_everyone", "use_embed", "embed_color",
    "video_template", "live_template", "video_embed_color", "live_embed_color",
    "video_mention_everyone", "live_mention_everyone", "video_use_embed", "live_use_embed",
    "live_title_style",
}


def _public_sub(sub: dict) -> dict:
    return {k: v for k, v in sub.items() if k not in ("last_notified_ts",)}


@routes.get("/api/streams")
@require_dashboard_access
async def streams_list(request: web.Request) -> web.Response:
    cog = request.app["bot"].get_cog("Streams")
    return web.json_response({
        "twitch_configured": bool(cog and cog.twitch_configured()),
        "subscriptions": [_public_sub(s) for s in streams.get_subscriptions(request["guild_id"])],
    })


@routes.post("/api/streams")
@require_dashboard_access
async def streams_create(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("Streams")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    platform = body.get("platform")
    query = body.get("query", "")
    channel_id = body.get("channel_id", "")
    if platform not in ("twitch", "youtube", "tiktok"):
        return web.json_response({"error": "invalid_platform"}, status=400)
    if not isinstance(query, str) or not query.strip():
        return web.json_response({"error": "invalid_query"}, status=400)
    if not isinstance(channel_id, str) or not channel_id.isdigit():
        return web.json_response({"error": "invalid_channel"}, status=400)

    if platform == "twitch":
        if not cog.twitch_configured():
            return web.json_response({"error": "twitch_not_configured"}, status=409)
        resolved = await cog.resolve_twitch(query)
    elif platform == "tiktok":
        if streams.parse_tiktok_username(query) is None:
            return web.json_response({"error": "invalid_tiktok_username"}, status=400)
        resolved = await cog.resolve_tiktok(query)
        if resolved is None:
            return web.json_response({"error": "tiktok_not_found"}, status=404)
    else:
        resolved = await cog.resolve_youtube(query)

    if resolved is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    guild_id = request["guild_id"]
    existing = [s for s in streams.get_subscriptions(guild_id) if s["platform"] == platform and s["identifier"] == resolved["identifier"]]
    if existing:
        return web.json_response({"error": "already_subscribed"}, status=409)

    sub = streams.add_subscription(guild_id, {
        "platform": platform,
        "identifier": resolved["identifier"],
        "display_name": resolved["display_name"],
        "avatar_url": resolved["avatar_url"],
        "enabled": True,
        "channel_id": channel_id,
        "ping_role_id": "",
        "template": "",
        "keywords": [],
        "keyword_mode": "any",
        "min_interval_minutes": 0,
        "mention_everyone": False,
        "use_embed": True,
        "embed_color": "",
        "video_template": "",
        "live_template": "",
        "video_embed_color": "",
        "live_embed_color": "",
        "video_mention_everyone": False,
        "live_mention_everyone": False,
        "video_use_embed": True,
        "live_use_embed": True,
        "live_title_style": "live_dot",
        "last_notified_ts": 0,
        "last_stream_id": "",
        "last_live_room_id": "",
    })
    if platform == "tiktok":
        await cog.seed_tiktok_subscription(guild_id, sub["id"], resolved["identifier"])
    elif platform == "youtube":
        feed = await cog._youtube_feed(resolved["identifier"])
        if feed and feed.get("entries"):
            streams.update_subscription(
                guild_id, sub["id"], last_stream_id=str(feed["entries"][0]["video_id"]),
            )
    refreshed = next((s for s in streams.get_subscriptions(guild_id) if s["id"] == sub["id"]), sub)
    return web.json_response(_public_sub({**refreshed}), status=201)


@routes.patch("/api/streams/{sub_id}")
@require_dashboard_access
async def streams_update(request: web.Request) -> web.Response:
    sub_id = request.match_info["sub_id"]
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    fields = {}
    for key, value in body.items():
        if key not in EDITABLE_FIELDS:
            continue
        if key == "enabled":
            if not isinstance(value, bool):
                return web.json_response({"error": "invalid_enabled"}, status=400)
        elif key in ("channel_id", "ping_role_id"):
            if not isinstance(value, str) or (value and not value.isdigit()):
                return web.json_response({"error": f"invalid_{key}"}, status=400)
        elif key == "template":
            if not isinstance(value, str) or len(value) > 1500:
                return web.json_response({"error": "invalid_template"}, status=400)
        elif key == "keywords":
            if not isinstance(value, list) or not all(isinstance(k, str) for k in value):
                return web.json_response({"error": "invalid_keywords"}, status=400)
            value = [k.strip() for k in value if k.strip()]
        elif key == "keyword_mode":
            if value not in ("any", "all"):
                return web.json_response({"error": "invalid_keyword_mode"}, status=400)
        elif key == "min_interval_minutes":
            if not isinstance(value, int) or not 0 <= value <= 10080:
                return web.json_response({"error": "invalid_interval"}, status=400)
        elif key in ("mention_everyone", "use_embed"):
            if not isinstance(value, bool):
                return web.json_response({"error": f"invalid_{key}"}, status=400)
        elif key == "embed_color":
            if not isinstance(value, str) or (value and not (value.startswith("#") and len(value) == 7)):
                return web.json_response({"error": "invalid_embed_color"}, status=400)
        elif key in ("video_embed_color", "live_embed_color"):
            if not isinstance(value, str) or (value and not (value.startswith("#") and len(value) == 7)):
                return web.json_response({"error": "invalid_embed_color"}, status=400)
        elif key in ("video_mention_everyone", "live_mention_everyone", "video_use_embed", "live_use_embed"):
            if not isinstance(value, bool):
                return web.json_response({"error": f"invalid_{key}"}, status=400)
        elif key in ("video_template", "live_template"):
            if not isinstance(value, str) or len(value) > 1500:
                return web.json_response({"error": "invalid_template"}, status=400)
        elif key == "live_title_style":
            if value not in streams._LIVE_TITLE_STYLES:
                return web.json_response({"error": "invalid_live_title_style"}, status=400)
        fields[key] = value

    updated = streams.update_subscription(request["guild_id"], sub_id, **fields)
    if updated is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(_public_sub({**updated}))


@routes.delete("/api/streams/{sub_id}")
@require_dashboard_access
async def streams_delete(request: web.Request) -> web.Response:
    if not streams.delete_subscription(request["guild_id"], request.match_info["sub_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/streams/{sub_id}/test")
@require_dashboard_access
async def streams_test(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("Streams")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    guild_id = request["guild_id"]
    sub = next(
        (s for s in streams.get_subscriptions(guild_id) if str(s["id"]) == request.match_info["sub_id"]),
        None,
    )
    if sub is None:
        return web.json_response({"error": "not_found"}, status=404)

    err = await cog.send_test_announce(guild_id, sub)
    if err:
        status = 400 if err in ("channel_required",) else 404 if err == "channel_not_found" else 502
        return web.json_response({"error": err}, status=status)
    return web.json_response({"ok": True})
