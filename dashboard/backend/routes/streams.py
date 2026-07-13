from aiohttp import web

import streams

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

EDITABLE_FIELDS = {"enabled", "channel_id", "ping_role_id", "template", "keywords", "keyword_mode", "min_interval_minutes"}


def _public_sub(sub: dict) -> dict:
    return {k: v for k, v in sub.items() if k not in ("last_notified_ts",)}


@routes.get("/api/streams")
@require_dashboard_access
async def streams_list(request: web.Request) -> web.Response:
    cog = request.app["bot"].get_cog("Streams")
    return web.json_response({
        "twitch_configured": bool(cog and cog.twitch_configured()),
        "subscriptions": [_public_sub(s) for s in streams.get_subscriptions()],
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
    if platform not in ("twitch", "youtube"):
        return web.json_response({"error": "invalid_platform"}, status=400)
    if not isinstance(query, str) or not query.strip():
        return web.json_response({"error": "invalid_query"}, status=400)
    if not isinstance(channel_id, str) or not channel_id.isdigit():
        return web.json_response({"error": "invalid_channel"}, status=400)

    if platform == "twitch":
        if not cog.twitch_configured():
            return web.json_response({"error": "twitch_not_configured"}, status=409)
        resolved = await cog.resolve_twitch(query)
    else:
        resolved = await cog.resolve_youtube(query)

    if resolved is None:
        return web.json_response({"error": "channel_not_found"}, status=404)

    existing = [s for s in streams.get_subscriptions() if s["platform"] == platform and s["identifier"] == resolved["identifier"]]
    if existing:
        return web.json_response({"error": "already_subscribed"}, status=409)

    sub = streams.add_subscription({
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
        "last_notified_ts": 0,
        "last_stream_id": "",
    })
    return web.json_response(_public_sub({**sub}), status=201)


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
        fields[key] = value

    updated = streams.update_subscription(sub_id, **fields)
    if updated is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(_public_sub({**updated}))


@routes.delete("/api/streams/{sub_id}")
@require_dashboard_access
async def streams_delete(request: web.Request) -> web.Response:
    if not streams.delete_subscription(request.match_info["sub_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})
