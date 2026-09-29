import uuid

from aiohttp import web

import bot.modules.games.economy_core as economy_core
import bot.modules.games.economy_db as economy_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()


@routes.get("/api/economy")
@require_dashboard_access
async def economy_get(request: web.Request) -> web.Response:
    return web.json_response(economy_core.get_settings(request["guild_id"]))


@routes.put("/api/economy")
@require_dashboard_access
async def economy_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    for key in (
        "enabled",
        "transfer_enabled",
        "roulette_bets_enabled",
        "daily_bonus_enabled",
        "weekly_report_enabled",
    ):
        if not isinstance(body.get(key, False), bool):
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    currency_name = body.get("currency_name", economy_core.DEFAULT_CURRENCY_NAME)
    currency_emoji = body.get("currency_emoji", economy_core.DEFAULT_CURRENCY_EMOJI)
    if not isinstance(currency_name, str) or not 1 <= len(currency_name.strip()) <= 30:
        return web.json_response({"error": "invalid_currency_name"}, status=400)
    if not isinstance(currency_emoji, str) or not 1 <= len(currency_emoji.strip()) <= 8:
        return web.json_response({"error": "invalid_currency_emoji"}, status=400)

    int_checks = (
        ("text_rate_percent", economy_core.DEFAULT_TEXT_RATE_PERCENT, 0, economy_core.RATE_PERCENT_MAX),
        ("voice_rate_percent", economy_core.DEFAULT_VOICE_RATE_PERCENT, 0, economy_core.RATE_PERCENT_MAX),
        ("transfer_fee_percent", economy_core.DEFAULT_TRANSFER_FEE_PERCENT, 0, economy_core.TRANSFER_FEE_MAX),
        ("roulette_max_bet", economy_core.DEFAULT_ROULETTE_MAX_BET, 0, economy_core.ROULETTE_BET_MAX_LIMIT),
        ("daily_base_amount", economy_core.DEFAULT_DAILY_BASE_AMOUNT, 0, economy_core.DAILY_AMOUNT_MAX),
        ("daily_growth_per_day", economy_core.DEFAULT_DAILY_GROWTH_PER_DAY, 0, economy_core.DAILY_AMOUNT_MAX),
        ("daily_max_streak_days", economy_core.DEFAULT_DAILY_MAX_STREAK_DAYS, 1, economy_core.DAILY_STREAK_DAYS_MAX),
        ("weekly_report_days", 7, 1, 30),
    )
    int_values = {}
    for key, default, lo, hi in int_checks:
        value = body.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or not lo <= value <= hi:
            return web.json_response({"error": f"invalid_{key}"}, status=400)
        int_values[key] = value

    raw_items = body.get("shop_items", [])
    if not isinstance(raw_items, list) or len(raw_items) > economy_core.SHOP_ITEMS_MAX:
        return web.json_response({"error": "invalid_shop_items"}, status=400)
    shop_items = []
    for raw in raw_items:
        if not isinstance(raw, dict):
            return web.json_response({"error": "invalid_shop_items"}, status=400)

        item_type = raw.get("type", "role")
        if item_type not in economy_core.SHOP_ITEM_TYPES:
            return web.json_response({"error": "invalid_shop_item_type"}, status=400)

        price = raw.get("price")
        name = raw.get("name", "")
        if not isinstance(price, int) or isinstance(price, bool) or not 1 <= price <= economy_core.SHOP_PRICE_MAX:
            return web.json_response({"error": "invalid_shop_item_price"}, status=400)
        if not isinstance(name, str) or len(name) > 60:
            return web.json_response({"error": "invalid_shop_item_name"}, status=400)

        item = {
            "id": str(raw.get("id") or uuid.uuid4().hex[:8]),
            "type": item_type,
            "role_id": "",
            "color_hex": "",
            "title_text": "",
            "price": price,
            "name": name.strip(),
        }

        if item_type == "role":
            # Строка, не число: Discord ID (snowflake) превышает Number.MAX_SAFE_INTEGER
            # во фронтенде — числом его передавать нельзя, значение тихо портится.
            role_id = raw.get("role_id")
            if not isinstance(role_id, str) or not role_id.isdigit() or int(role_id) <= 0:
                return web.json_response({"error": "invalid_shop_item_role"}, status=400)
            item["role_id"] = role_id
        elif item_type == "frame_color":
            color_hex = raw.get("color_hex", "")
            if not isinstance(color_hex, str) or not economy_core.COLOR_HEX_RE.match(color_hex):
                return web.json_response({"error": "invalid_shop_item_color"}, status=400)
            item["color_hex"] = color_hex
        else:  # title
            title_text = raw.get("title_text", "")
            if not isinstance(title_text, str) or not 1 <= len(title_text.strip()) <= economy_core.TITLE_TEXT_MAX:
                return web.json_response({"error": "invalid_shop_item_title"}, status=400)
            item["title_text"] = title_text.strip()

        shop_items.append(item)

    guild_id = request["guild_id"]
    economy_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "currency_name": currency_name.strip(),
        "currency_emoji": currency_emoji.strip(),
        "transfer_enabled": body.get("transfer_enabled", True),
        "roulette_bets_enabled": body.get("roulette_bets_enabled", True),
        "daily_bonus_enabled": body.get("daily_bonus_enabled", True),
        **int_values,
        "shop_items": shop_items,
        "weekly_report_enabled": bool(body.get("weekly_report_enabled", False)),
        "weekly_report_channel_id": str(body.get("weekly_report_channel_id") or ""),
        "weekly_report_days": int_values["weekly_report_days"],
        "last_weekly_report_date": economy_core.get_settings(guild_id).get("last_weekly_report_date", ""),
    })
    return web.json_response(economy_core.get_settings(guild_id))


@routes.get("/api/economy/top")
@require_dashboard_access
async def economy_top(request: web.Request) -> web.Response:
    economy_db.init()
    guild_id = request["guild_id"]
    guild = request.app["bot"].get_guild(guild_id)
    result = []
    for row in economy_db.top(guild_id, 25):
        member = guild.get_member(row["user_id"]) if guild else None
        result.append({
            "user_id": str(row["user_id"]),
            "display_name": member.display_name if member else str(row["user_id"]),
            "balance": row["balance"],
        })
    return web.json_response(result)


@routes.get("/api/economy/weekly-report")
@require_dashboard_access
async def economy_weekly_report(request: web.Request) -> web.Response:
    economy_db.init()
    guild_id = request["guild_id"]
    settings = economy_core.get_settings(guild_id)
    days = max(1, min(30, int(settings.get("weekly_report_days") or 7)))
    guild = request.app["bot"].get_guild(guild_id)
    rows = []
    for row in economy_db.weekly_report(guild_id, days=days):
        member = guild.get_member(row["user_id"]) if guild else None
        rows.append({
            "user_id": str(row["user_id"]),
            "display_name": member.display_name if member else str(row["user_id"]),
            "earned": row["earned"],
            "spent": row["spent"],
            "net": row["net"],
        })
    return web.json_response({
        "days": days,
        "weekly_report_enabled": settings["weekly_report_enabled"],
        "weekly_report_channel_id": settings["weekly_report_channel_id"],
        "rows": rows,
    })


@routes.put("/api/economy/balance")
@require_dashboard_access
async def economy_set_balance(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    user_id = body.get("user_id")
    if isinstance(user_id, str) and user_id.isdigit():
        user_id = int(user_id)
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        return web.json_response({"error": "invalid_user_id"}, status=400)

    balance = body.get("balance")
    if not isinstance(balance, int) or isinstance(balance, bool) or not 0 <= balance <= economy_core.BALANCE_ADMIN_MAX:
        return web.json_response({"error": "invalid_balance"}, status=400)

    economy_db.init()
    economy_db.set_balance(request["guild_id"], user_id, balance, "dashboard_adjust")
    return web.json_response({"user_id": str(user_id), "balance": balance})


@routes.post("/api/economy/reset-all")
@require_dashboard_access
async def economy_reset_all(request: web.Request) -> web.Response:
    economy_db.init()
    cleared = economy_db.reset_all_balances(request["guild_id"])
    return web.json_response({"ok": True, "cleared": cleared})
