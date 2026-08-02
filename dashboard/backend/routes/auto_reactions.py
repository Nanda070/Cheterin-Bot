from aiohttp import web

import auto_reactions_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


def _validate_rules(rules) -> tuple[list[dict] | None, str | None]:
    if not isinstance(rules, list):
        return None, "invalid_rules"
    if len(rules) > auto_reactions_core.MAX_RULES:
        return None, "too_many_rules"

    cleaned: list[dict] = []
    for raw in rules:
        if not isinstance(raw, dict):
            return None, "invalid_rule"
        rule_id = raw.get("id")
        if rule_id is None or not isinstance(rule_id, str) or not rule_id.strip():
            rule_id = auto_reactions_core.new_rule_id()
        emojis = raw.get("emojis") or []
        if not isinstance(emojis, list) or not emojis:
            return None, "invalid_emojis"
        if len(emojis) > auto_reactions_core.MAX_EMOJIS_PER_RULE:
            return None, "too_many_emojis"
        for e in emojis:
            if not auto_reactions_core.is_valid_emoji_token(e):
                return None, "invalid_emoji"

        keywords = raw.get("keywords") or []
        if not isinstance(keywords, list):
            return None, "invalid_keywords"
        if len(keywords) > auto_reactions_core.MAX_KEYWORDS_PER_RULE:
            return None, "too_many_keywords"
        for k in keywords:
            if not isinstance(k, str) or not k.strip() or len(k.strip()) > auto_reactions_core.MAX_KEYWORD_LEN:
                return None, "invalid_keyword"

        mode = raw.get("channel_mode", "all")
        if mode not in auto_reactions_core.CHANNEL_MODES:
            return None, "invalid_channel_mode"

        def _ids(key: str) -> list[str] | None:
            vals = raw.get(key) or []
            if not isinstance(vals, list):
                return None
            out = []
            for v in vals:
                if not isinstance(v, str) or (v and not v.isdigit()):
                    return None
                if v:
                    out.append(v)
            return out

        channel_ids = _ids("channel_ids")
        exclude_ids = _ids("exclude_channel_ids")
        if channel_ids is None or exclude_ids is None:
            return None, "invalid_channel_ids"

        ignore_bots = raw.get("ignore_bots", True)
        if not isinstance(ignore_bots, bool):
            return None, "invalid_ignore_bots"

        if mode == "include" and not channel_ids:
            return None, "channels_required"

        cleaned.append({
            "id": rule_id.strip(),
            "emojis": [str(e).strip() for e in emojis],
            "keywords": [str(k).strip() for k in keywords],
            "channel_mode": mode,
            "channel_ids": channel_ids,
            "exclude_channel_ids": exclude_ids,
            "ignore_bots": ignore_bots,
        })
    return cleaned, None


@routes.get("/api/auto-reactions")
@require_dashboard_access
async def auto_reactions_get(request: web.Request) -> web.Response:
    return web.json_response(auto_reactions_core.get_settings(request["guild_id"]))


@routes.put("/api/auto-reactions")
@require_dashboard_access
async def auto_reactions_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    rules, err = _validate_rules(body.get("rules", []))
    if err:
        return web.json_response({"error": err}, status=400)

    settings = auto_reactions_core.save_config(
        request["guild_id"], enabled=enabled, rules=rules or [],
    )
    return web.json_response(settings)
