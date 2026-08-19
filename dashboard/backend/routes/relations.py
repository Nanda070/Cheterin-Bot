from aiohttp import web

import relations_core
import relations_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/relations")
@require_dashboard_access
async def relations_get(request: web.Request) -> web.Response:
    return web.json_response(relations_core.get_settings(request["guild_id"]))


@routes.put("/api/relations")
@require_dashboard_access
async def relations_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    enabled = body.get("enabled", False)
    if not isinstance(enabled, bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    channel_id = str(body.get("announce_channel_id") or "")
    ch_err = relations_core.validate_channel_id(channel_id)
    if ch_err:
        return web.json_response({"error": ch_err}, status=400)

    married_role_id = str(body.get("married_role_id") or "")
    role_err = relations_core.validate_role_id(married_role_id)
    if role_err:
        return web.json_response({"error": role_err}, status=400)

    try:
        max_day = int(body.get("max_actions_per_day", relations_core.MAX_ACTIONS_PER_DAY))
    except (TypeError, ValueError):
        return web.json_response({"error": "invalid_max_actions_per_day"}, status=400)
    if not 1 <= max_day <= 500:
        return web.json_response({"error": "invalid_max_actions_per_day"}, status=400)

    actions = relations_core._normalize_actions(body.get("actions"))
    raw_thresholds = body.get("level_thresholds")
    if raw_thresholds is not None:
        if not isinstance(raw_thresholds, list) or len(raw_thresholds) != relations_core.LEVEL_COUNT:
            return web.json_response({"error": "invalid_level_thresholds"}, status=400)
        thresholds = relations_core._normalize_thresholds(raw_thresholds)
        try:
            coerced = [int(v) for v in raw_thresholds]
        except (TypeError, ValueError):
            return web.json_response({"error": "invalid_level_thresholds"}, status=400)
        if thresholds != coerced:
            # _normalize_thresholds fell back to defaults — the values were invalid
            return web.json_response({"error": "invalid_level_thresholds"}, status=400)
    else:
        thresholds = relations_core._normalize_thresholds(None)

    reward_roles = relations_core._normalize_reward_roles(body.get("reward_roles"))

    marriage_enabled = body.get("marriage_enabled", True)
    if not isinstance(marriage_enabled, bool):
        return web.json_response({"error": "invalid_marriage_enabled"}, status=400)
    allow_polygamy = body.get("allow_polygamy", False)
    if not isinstance(allow_polygamy, bool):
        return web.json_response({"error": "invalid_allow_polygamy"}, status=400)
    divorce_requires_accept = body.get("divorce_requires_accept", True)
    if not isinstance(divorce_requires_accept, bool):
        return web.json_response({"error": "invalid_divorce_requires_accept"}, status=400)

    saved = relations_core.save_config(
        request["guild_id"],
        {
            "enabled": enabled,
            "announce_channel_id": channel_id,
            "max_actions_per_day": max_day,
            "actions": actions,
            "level_thresholds": thresholds,
            "reward_roles": reward_roles,
            "marriage_enabled": marriage_enabled,
            "min_level_to_marry": body.get(
                "min_level_to_marry", relations_core.DEFAULT_MIN_LEVEL_TO_MARRY
            ),
            "married_role_id": married_role_id,
            "allow_polygamy": allow_polygamy,
            "proposal_timeout_sec": body.get(
                "proposal_timeout_sec", relations_core.DEFAULT_PROPOSAL_TIMEOUT_SEC
            ),
            "married_hp_bonus_percent": body.get(
                "married_hp_bonus_percent", relations_core.DEFAULT_MARRIED_HP_BONUS_PERCENT
            ),
            "divorce_requires_accept": divorce_requires_accept,
            "date_hp_gain": body.get("date_hp_gain", relations_core.DEFAULT_DATE_HP_GAIN),
            "date_cooldown_sec": body.get(
                "date_cooldown_sec", relations_core.DEFAULT_DATE_COOLDOWN_SEC
            ),
        },
    )
    return web.json_response(saved)


@routes.get("/api/relations/top")
@require_dashboard_access
async def relations_top(request: web.Request) -> web.Response:
    try:
        limit = int(request.rel_url.query.get("limit", "15"))
    except ValueError:
        limit = 15
    rows = relations_db.top_pairs(request["guild_id"], limit)
    return web.json_response({"pairs": rows})


@routes.get("/api/relations/marriages")
@require_dashboard_access
async def relations_marriages(request: web.Request) -> web.Response:
    try:
        limit = int(request.rel_url.query.get("limit", "15"))
    except ValueError:
        limit = 15
    rows = relations_db.top_marriages(request["guild_id"], limit)
    return web.json_response({"marriages": rows})
