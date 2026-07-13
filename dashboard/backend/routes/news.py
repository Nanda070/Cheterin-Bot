from aiohttp import web

import news

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/news")
@require_dashboard_access
async def news_get(request: web.Request) -> web.Response:
    return web.json_response(news.get_settings())


def _is_id_like(value) -> bool:
    if not isinstance(value, str):
        return False
    if value == "":
        return True
    return value.isdigit()


@routes.put("/api/news")
@require_dashboard_access
async def news_put(request: web.Request) -> web.Response:
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
        if source in seen_sources:
            return web.json_response({"error": "duplicate_source_channel"}, status=400)
        seen_sources.add(source)
        clean_mappings.append({
            "source_channel_id": source,
            "target_channel_id": target,
            "label": label.strip(),
        })

    news.save_config({
        "enabled": enabled,
        "source_guild_id": source_guild_id,
        "source_bot_ids": list(source_bot_ids),
        "log_channel_id": log_channel_id,
        "mappings": clean_mappings,
    })
    return web.json_response(news.get_settings())
