from aiohttp import web

import bot.modules.community.daily_topic_core as daily_topic_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/daily-topic")
@require_dashboard_access
async def daily_topic_get(request: web.Request) -> web.Response:
    return web.json_response(daily_topic_core.get_settings(request["guild_id"]))


@routes.put("/api/daily-topic/settings")
@require_dashboard_access
async def daily_topic_update_settings(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    channel_id = body.get("channel_id", "")
    post_times = body.get("post_times", [])

    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if not isinstance(channel_id, str) or (channel_id and not channel_id.isdigit()):
        return web.json_response({"error": "invalid_channel"}, status=400)
    if not isinstance(post_times, list) or len(post_times) > daily_topic_core.MAX_POST_TIMES:
        return web.json_response({"error": "invalid_post_times"}, status=400)
    if not all(isinstance(t, str) and daily_topic_core.is_valid_time(t) for t in post_times):
        return web.json_response({"error": "invalid_post_times"}, status=400)
    if enabled and not channel_id:
        return web.json_response({"error": "channel_required"}, status=400)
    if enabled and not post_times:
        return web.json_response({"error": "post_times_required"}, status=400)

    settings = daily_topic_core.update_settings(
        request["guild_id"], enabled=enabled, channel_id=channel_id, post_times=post_times,
    )
    return web.json_response(settings)


@routes.post("/api/daily-topic/topics")
@require_dashboard_access
async def daily_topic_create_topic(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    text = body.get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip() or len(text) > daily_topic_core.MAX_TOPIC_LENGTH:
        return web.json_response({"error": "invalid_text"}, status=400)

    topic = daily_topic_core.add_topic(request["guild_id"], text.strip())
    return web.json_response(topic, status=201)


@routes.patch("/api/daily-topic/topics/{topic_id}")
@require_dashboard_access
async def daily_topic_update_topic(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    text = body.get("text") if isinstance(body, dict) else None
    if not isinstance(text, str) or not text.strip() or len(text) > daily_topic_core.MAX_TOPIC_LENGTH:
        return web.json_response({"error": "invalid_text"}, status=400)

    topic = daily_topic_core.update_topic(request["guild_id"], request.match_info["topic_id"], text.strip())
    if topic is None:
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response(topic)


@routes.delete("/api/daily-topic/topics/{topic_id}")
@require_dashboard_access
async def daily_topic_delete_topic(request: web.Request) -> web.Response:
    if not daily_topic_core.delete_topic(request["guild_id"], request.match_info["topic_id"]):
        return web.json_response({"error": "not_found"}, status=404)
    return web.json_response({"ok": True})


@routes.post("/api/daily-topic/post-now")
@require_dashboard_access
async def daily_topic_post_now(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    cog = bot.get_cog("DailyTopicCog")
    if cog is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    guild_id = request["guild_id"]
    settings = daily_topic_core.get_settings(guild_id)
    if not settings["channel_id"]:
        return web.json_response({"error": "channel_not_configured"}, status=409)
    if not settings["topics"]:
        return web.json_response({"error": "no_topics"}, status=409)

    topic = await cog.post_topic_now(guild_id)
    if topic is None:
        return web.json_response({"error": "post_failed"}, status=502)
    return web.json_response({"ok": True, "topic": topic})
