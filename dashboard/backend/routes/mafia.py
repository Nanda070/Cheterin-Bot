import time

from aiohttp import web

import language_core
import mafia_core
import mafia_db

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

TIMER_MIN = 10
TIMER_MAX = 3600


def _is_id(value) -> bool:
    return isinstance(value, str) and (value == "" or value.isdigit())


def _display_name(guild, user_id: int) -> str:
    member = guild.get_member(user_id) if guild else None
    return member.display_name if member else str(user_id)


def _serialize_game_summary(game: dict, bot) -> dict:
    channel = bot.get_channel(game["channel_id"])
    channel_name = getattr(channel, "name", None) or str(game["channel_id"])
    player_count = mafia_db.count_players(game["id"])
    alive_count = len(mafia_db.list_alive_players(game["id"])) if game["status"] == "active" else player_count
    return {
        "id": game["id"],
        "channel_id": str(game["channel_id"]),
        "channel_name": channel_name,
        "status": game["status"],
        "phase": game["phase"],
        "round_number": game["round_number"],
        "player_count": player_count,
        "alive_count": alive_count,
        "created_at": game["created_at"],
    }


# ────────────────────────── Настройки ──────────────────────────

@routes.get("/api/mafia")
@require_dashboard_access
async def mafia_get(request: web.Request) -> web.Response:
    return web.json_response(mafia_core.get_settings(request["guild_id"]))


@routes.put("/api/mafia")
@require_dashboard_access
async def mafia_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    min_players = body.get("default_min_players", mafia_core.DEFAULT_MIN_PLAYERS)
    max_players = body.get("default_max_players", mafia_core.DEFAULT_MAX_PLAYERS)
    if not isinstance(min_players, int) or isinstance(min_players, bool) or not mafia_core.PLAYERS_FLOOR <= min_players <= mafia_core.PLAYERS_CEIL:
        return web.json_response({"error": "invalid_default_min_players"}, status=400)
    if not isinstance(max_players, int) or isinstance(max_players, bool) or not mafia_core.PLAYERS_FLOOR <= max_players <= mafia_core.PLAYERS_CEIL:
        return web.json_response({"error": "invalid_default_max_players"}, status=400)
    if min_players > max_players:
        return web.json_response({"error": "min_greater_than_max"}, status=400)

    night_timer = body.get("default_night_timer_sec", mafia_core.DEFAULT_NIGHT_TIMER_SEC)
    discussion_timer = body.get("default_day_discussion_timer_sec", mafia_core.DEFAULT_DAY_DISCUSSION_TIMER_SEC)
    vote_timer = body.get("default_day_vote_timer_sec", mafia_core.DEFAULT_DAY_VOTE_TIMER_SEC)
    for value, key in (
        (night_timer, "default_night_timer_sec"),
        (discussion_timer, "default_day_discussion_timer_sec"),
        (vote_timer, "default_day_vote_timer_sec"),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not TIMER_MIN <= value <= TIMER_MAX:
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    log_channel_id = body.get("log_channel_id", "")
    if not _is_id(log_channel_id):
        return web.json_response({"error": "invalid_log_channel_id"}, status=400)

    guild_id = request["guild_id"]
    mafia_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "default_min_players": min_players,
        "default_max_players": max_players,
        "default_night_timer_sec": night_timer,
        "default_day_discussion_timer_sec": discussion_timer,
        "default_day_vote_timer_sec": vote_timer,
        "log_channel_id": log_channel_id,
    })
    return web.json_response(mafia_core.get_settings(guild_id))


@routes.get("/api/mafia/games")
@require_dashboard_access
async def mafia_games_list(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    games = mafia_db.list_active_games()
    return web.json_response({"games": [_serialize_game_summary(g, bot) for g in games]})


# ────────────────────────── Публичная ссылка игрока ──────────────────────────

@routes.get("/api/public/mafia/{token}")
async def mafia_public_state(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = mafia_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = mafia_db.get_game(player["game_id"])
    if game is None:
        return web.json_response({"error": "unknown_token"}, status=404)

    guild = request.app["bot"].get_guild(game["guild_id"])
    round_number = game["round_number"]

    action = None
    if game["phase"] == "night":
        action = mafia_db.get_night_action(game["id"], round_number, player["user_id"])
    elif game["phase"] == "day_vote":
        action = mafia_db.get_day_vote(game["id"], round_number, player["user_id"])

    alive_players = mafia_db.list_alive_players(game["id"])
    action_required = bool(player["alive"]) and game["status"] == "active" and (
        (game["phase"] == "night" and player["role"] in mafia_core.NIGHT_ACTION_ROLES)
        or game["phase"] == "day_vote"
    )

    all_players = mafia_db.list_players(game["id"])
    roster = []
    for p in all_players:
        entry = {
            "user_id": str(p["user_id"]),
            "display_name": _display_name(guild, p["user_id"]),
            "alive": bool(p["alive"]),
        }
        if not p["alive"] or p["user_id"] == player["user_id"]:
            entry["role"] = p["role"]
        roster.append(entry)

    body = {
        "language": language_core.get_language(game["guild_id"]),
        "game_status": game["status"],
        "phase": game["phase"],
        "round_number": round_number,
        "phase_deadline_ts": game["phase_deadline_ts"],
        "your_role": player["role"],
        "your_alive": bool(player["alive"]),
        "action_required": action_required,
        "your_action_submitted": action is not None,
        "your_submitted_target": str(action["target_user_id"]) if action and action["target_user_id"] is not None else None,
        "alive_players": [
            {"user_id": str(p["user_id"]), "display_name": _display_name(guild, p["user_id"])}
            for p in alive_players
        ],
        "roster": roster,
    }

    if player["role"] == "mafia" and game["phase"] == "night":
        mafia_actions = mafia_db.get_night_actions(game["id"], round_number, role="mafia")
        body["mafia_votes"] = [
            {"actor": str(a["actor_user_id"]), "target": str(a["target_user_id"]) if a["target_user_id"] else None}
            for a in mafia_actions
        ]
        teammates = [
            p for p in mafia_db.list_players(game["id"])
            if p["role"] == "mafia" and p["user_id"] != player["user_id"]
        ]
        body["teammates"] = [
            {"user_id": str(p["user_id"]), "display_name": _display_name(guild, p["user_id"])}
            for p in teammates
        ]

    if game["phase"] == "day_vote":
        votes = mafia_db.get_day_votes(game["id"], round_number)
        tally: dict[str | None, int] = {}
        for v in votes:
            key = str(v["target_user_id"]) if v["target_user_id"] is not None else None
            tally[key] = tally.get(key, 0) + 1
        body["vote_tally"] = [
            {
                "target": key,
                "target_display": _display_name(guild, int(key)) if key else None,
                "count": count,
            }
            for key, count in sorted(tally.items(), key=lambda kv: -kv[1])
        ]

    return web.json_response(body)


@routes.post("/api/public/mafia/{token}/action")
async def mafia_public_action(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = mafia_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = mafia_db.get_game(player["game_id"])
    if game is None or game["status"] != "active":
        return web.json_response({"error": "game_ended"}, status=410)
    if not player["alive"]:
        return web.json_response({"error": "player_dead"}, status=403)
    if game["phase"] != "night" or player["role"] not in mafia_core.NIGHT_ACTION_ROLES:
        return web.json_response({"error": "wrong_phase"}, status=400)
    if game["phase_deadline_ts"] and int(time.time()) > game["phase_deadline_ts"]:
        return web.json_response({"error": "deadline_passed"}, status=409)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    raw_target = body.get("target_user_id")
    target_user_id = None
    if raw_target is not None:
        if not isinstance(raw_target, str) or not raw_target.isdigit():
            return web.json_response({"error": "invalid_target"}, status=400)
        target_user_id = int(raw_target)
        alive_ids = {p["user_id"] for p in mafia_db.list_alive_players(game["id"])}
        if target_user_id not in alive_ids:
            return web.json_response({"error": "invalid_target"}, status=400)
        if target_user_id == player["user_id"] and player["role"] in ("mafia", "sheriff"):
            return web.json_response({"error": "invalid_target"}, status=400)

    mafia_db.upsert_night_action(game["id"], game["round_number"], player["user_id"], player["role"], target_user_id)

    cog = request.app["bot"].get_cog("MafiaCog")
    if cog is not None:
        await cog.maybe_finish_night_early(game["id"])

    return web.json_response({"ok": True})


@routes.post("/api/public/mafia/{token}/vote")
async def mafia_public_vote(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = mafia_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = mafia_db.get_game(player["game_id"])
    if game is None or game["status"] != "active":
        return web.json_response({"error": "game_ended"}, status=410)
    if not player["alive"]:
        return web.json_response({"error": "player_dead"}, status=403)
    if game["phase"] != "day_vote":
        return web.json_response({"error": "wrong_phase"}, status=400)
    if game["phase_deadline_ts"] and int(time.time()) > game["phase_deadline_ts"]:
        return web.json_response({"error": "deadline_passed"}, status=409)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    raw_target = body.get("target_user_id")
    target_user_id = None
    if raw_target is not None:
        if not isinstance(raw_target, str) or not raw_target.isdigit():
            return web.json_response({"error": "invalid_target"}, status=400)
        target_user_id = int(raw_target)
        alive_ids = {p["user_id"] for p in mafia_db.list_alive_players(game["id"])}
        if target_user_id not in alive_ids:
            return web.json_response({"error": "invalid_target"}, status=400)

    mafia_db.upsert_day_vote(game["id"], game["round_number"], player["user_id"], target_user_id)

    cog = request.app["bot"].get_cog("MafiaCog")
    if cog is not None:
        await cog.refresh_vote_tally(game["id"])
        await cog.maybe_finish_day_vote_early(game["id"])

    return web.json_response({"ok": True})
