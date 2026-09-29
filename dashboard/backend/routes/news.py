from aiohttp import web

import bot.modules.community.news as news

from ..access_middleware import require_super_admin

routes = web.RouteTableDef()


@routes.get("/api/news")
@require_super_admin
async def news_get(request: web.Request) -> web.Response:
    return web.json_response(news.get_settings(request["guild_id"]))


def _is_id_like(value) -> bool:
    if not isinstance(value, str):
        return False
    if value == "":
        return True
    return value.isdigit()


@routes.put("/api/news")
@require_super_admin
async def news_put(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    main_guild = bot.get_guild(request["guild_id"])
    if main_guild is None:
        return web.json_response({"error": "service_unavailable"}, status=503)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", True)
    source_guild_id = body.get("source_guild_id", "")
    source_bot_ids = body.get("source_bot_ids", [])
    log_channel_id = body.get("log_channel_id", "")
    mappings = body.get("mappings", [])

    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)
    if not _is_id_like(source_guild_id):
        return web.json_response({"error": "invalid_source_guild_id"}, status=400)
    if not isinstance(source_bot_ids, list) or not all(_is_id_like(v) and v for v in source_bot_ids):
        return web.json_response({"error": "invalid_source_bot_ids"}, status=400)
    if not _is_id_like(log_channel_id):
        return web.json_response({"error": "invalid_log_channel_id"}, status=400)
    # Лог-канал (как и целевые) обязан быть каналом мейн-сервера.
    if log_channel_id and main_guild.get_channel(int(log_channel_id)) is None:
        return web.json_response({"error": "log_channel_id_not_found"}, status=404)

    if not isinstance(mappings, list):
        return web.json_response({"error": "invalid_mappings"}, status=400)
    clean_mappings = []
    seen_sources = set()
    for item in mappings:
        if not isinstance(item, dict):
            return web.json_response({"error": "invalid_mappings"}, status=400)
        source = item.get("source_channel_id", "")
        target = item.get("target_channel_id", "")
        label = item.get("label", "")
        if not (_is_id_like(source) and source and _is_id_like(target) and target):
            return web.json_response({"error": "invalid_mappings"}, status=400)
        if not isinstance(label, str):
            return web.json_response({"error": "invalid_mappings"}, status=400)
        # Источник — на любом сервере (не валидируем), а цель обязана быть каналом мейна.
        if main_guild.get_channel(int(target)) is None:
            return web.json_response({"error": "target_channel_not_found"}, status=404)
        if source in seen_sources:
            return web.json_response({"error": "duplicate_source_channel"}, status=400)
        seen_sources.add(source)
        clean_mappings.append({
            "source_channel_id": source,
            "target_channel_id": target,
            "label": label.strip(),
        })

    guild_id = request["guild_id"]
    news.save_config(guild_id, {
        "enabled": enabled,
        "source_guild_id": source_guild_id,
        "source_bot_ids": list(source_bot_ids),
        "log_channel_id": log_channel_id,
        "mappings": clean_mappings,
    })
    return web.json_response(news.get_settings(guild_id))
