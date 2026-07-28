import time

from aiohttp import web

import bunker_core
import bunker_db
import bunker_localize
import language_core

from ..access_middleware import require_dashboard_access

routes = web.RouteTableDef()

TIMER_MIN = 10
TIMER_MAX = 3600


def _is_id(value) -> bool:
    return isinstance(value, str) and (value == "" or value.isdigit())


def _display_name(guild, user_id: int, stored: str | None = None) -> str:
    member = guild.get_member(user_id) if guild else None
    if member is not None:
        return member.display_name
    return stored or str(user_id)


def _avatar_url(guild, user_id: int, stored: str | None = None) -> str | None:
    member = guild.get_member(user_id) if guild else None
    if member is not None and getattr(member, "display_avatar", None) is not None:
        return str(member.display_avatar.url)
    return stored or None


def _player_ref(guild, player: dict) -> dict:
    return {
        "user_id": str(player["user_id"]),
        "display_name": _display_name(guild, player["user_id"], player.get("display_name")),
        "avatar_url": _avatar_url(guild, player["user_id"], player.get("avatar_url")),
    }


def _serialize_game_summary(game: dict, bot) -> dict:
    channel = bot.get_channel(game["channel_id"])
    channel_name = getattr(channel, "name", None) or str(game["channel_id"])
    player_count = bunker_db.count_players(game["id"])
    alive_count = len(bunker_db.list_alive_players(game["id"])) if game["status"] == "active" else player_count
    return {
        "id": game["id"],
        "channel_id": str(game["channel_id"]),
        "channel_name": channel_name,
        "status": game["status"],
        "phase": game["phase"],
        "round_number": game["round_number"],
        "bunker_capacity": game["bunker_capacity"],
        "unique_cards": bool(game["unique_cards"]),
        "player_count": player_count,
        "alive_count": alive_count,
        "created_at": game["created_at"],
    }


def _public_character_view(character: dict | None, revealed_fields: list[str]) -> dict:
    """Только раскрытые поля — используется для отображения ДРУГИХ игроков в ростере."""
    if not character:
        return {}
    return {key: character[key] for key in bunker_core.FIELD_KEYS if key in revealed_fields and key in character}


def _serialize_ability_announcement(announcement: dict, guild) -> dict:
    return {
        "id": announcement["id"],
        "round_number": announcement["round_number"],
        "player_user_id": str(announcement["player_user_id"]),
        "player_display_name": _display_name(
            guild, announcement["player_user_id"], announcement.get("player_display_name")
        ),
        "card_index": announcement["card_index"],
        "card_name": announcement["card_name"],
        "target_user_id": str(announcement["target_user_id"]) if announcement["target_user_id"] is not None else None,
        "target_display_name": (
            _display_name(
                guild, announcement["target_user_id"], announcement.get("target_display_name")
            )
            if announcement["target_user_id"] is not None
            else None
        ),
        "note": announcement["note"],
        "applied": bool(announcement["applied"]),
        "created_at": announcement["created_at"],
    }


# ────────────────────────── Настройки ──────────────────────────

@routes.get("/api/bunker")
@require_dashboard_access
async def bunker_get(request: web.Request) -> web.Response:
    return web.json_response(bunker_core.get_settings(request["guild_id"]))


@routes.put("/api/bunker")
@require_dashboard_access
async def bunker_put(request: web.Request) -> web.Response:
    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    if not isinstance(body.get("enabled", False), bool):
        return web.json_response({"error": "invalid_enabled"}, status=400)

    min_players = body.get("default_min_players", bunker_core.DEFAULT_MIN_PLAYERS)
    max_players = body.get("default_max_players", bunker_core.DEFAULT_MAX_PLAYERS)
    if not isinstance(min_players, int) or isinstance(min_players, bool) or not bunker_core.PLAYERS_FLOOR <= min_players <= bunker_core.PLAYERS_CEIL:
        return web.json_response({"error": "invalid_default_min_players"}, status=400)
    if not isinstance(max_players, int) or isinstance(max_players, bool) or not bunker_core.PLAYERS_FLOOR <= max_players <= bunker_core.PLAYERS_CEIL:
        return web.json_response({"error": "invalid_default_max_players"}, status=400)
    if min_players > max_players:
        return web.json_response({"error": "min_greater_than_max"}, status=400)

    discussion_timer = body.get("default_discussion_timer_sec", bunker_core.DEFAULT_DISCUSSION_TIMER_SEC)
    vote_timer = body.get("default_vote_timer_sec", bunker_core.DEFAULT_VOTE_TIMER_SEC)
    for value, key in (
        (discussion_timer, "default_discussion_timer_sec"),
        (vote_timer, "default_vote_timer_sec"),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or not TIMER_MIN <= value <= TIMER_MAX:
            return web.json_response({"error": f"invalid_{key}"}, status=400)

    log_channel_id = body.get("log_channel_id", "")
    if not _is_id(log_channel_id):
        return web.json_response({"error": "invalid_log_channel_id"}, status=400)

    unique_cards = body.get("default_unique_cards", bunker_core.DEFAULT_UNIQUE_CARDS)
    if not isinstance(unique_cards, bool):
        return web.json_response({"error": "invalid_default_unique_cards"}, status=400)

    guild_id = request["guild_id"]
    bunker_core.save_config(guild_id, {
        "enabled": body["enabled"],
        "default_min_players": min_players,
        "default_max_players": max_players,
        "default_discussion_timer_sec": discussion_timer,
        "default_vote_timer_sec": vote_timer,
        "default_unique_cards": unique_cards,
        "log_channel_id": log_channel_id,
    })
    return web.json_response(bunker_core.get_settings(guild_id))


@routes.get("/api/bunker/card-pools")
@require_dashboard_access
async def bunker_card_pools(request: web.Request) -> web.Response:
    """Справочные данные для типизированного редактора карточки игрока в админке."""
    lang = language_core.get_language(request["guild_id"])
    return web.json_response(bunker_localize.get_card_pools(lang))


def _game_for_guild(game_id: int, guild_id: int) -> dict | None:
    game = bunker_db.get_game(game_id)
    if game is None or int(game["guild_id"]) != int(guild_id):
        return None
    return game


@routes.get("/api/bunker/games")
@require_dashboard_access
async def bunker_games_list(request: web.Request) -> web.Response:
    bot = request.app["bot"]
    games = bunker_db.list_active_games(request["guild_id"])
    return web.json_response({"games": [_serialize_game_summary(g, bot) for g in games]})


@routes.get("/api/bunker/games/{id}")
@require_dashboard_access
async def bunker_game_detail(request: web.Request) -> web.Response:
    try:
        game_id = int(request.match_info["id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)
    game = _game_for_guild(game_id, request["guild_id"])
    if game is None:
        return web.json_response({"error": "not_found"}, status=404)

    bot = request.app["bot"]
    guild = bot.get_guild(game["guild_id"])
    players = bunker_db.list_players(game_id)

    return web.json_response({
        "game": _serialize_game_summary(game, bot),
        "players": [
            {
                "user_id": str(p["user_id"]),
                "display_name": _display_name(guild, p["user_id"]),
                "alive": bool(p["alive"]),
                "character": p["character"],
                "revealed_fields": p["revealed_fields"],
            }
            for p in players
        ],
        "ability_announcements": [
            _serialize_ability_announcement(a, guild) for a in bunker_db.list_ability_announcements(game_id)
        ],
    })


@routes.patch("/api/bunker/games/{id}/players/{user_id}")
@require_dashboard_access
async def bunker_patch_player(request: web.Request) -> web.Response:
    """Ручное применение эффекта спец. возможности ведущим — частичная замена полей карточки."""
    try:
        game_id = int(request.match_info["id"])
        user_id = int(request.match_info["user_id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)
    game = _game_for_guild(game_id, request["guild_id"])
    if game is None:
        return web.json_response({"error": "not_found"}, status=404)
    player = bunker_db.get_player(game_id, user_id)
    if player is None:
        return web.json_response({"error": "not_found"}, status=404)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    patch = body.get("character") if isinstance(body, dict) else None
    if not isinstance(patch, dict) or not patch:
        return web.json_response({"error": "invalid_character"}, status=400)
    if not set(patch.keys()) <= set(bunker_core.FIELD_KEYS) | {"special_abilities"}:
        return web.json_response({"error": "invalid_character_keys"}, status=400)

    character = dict(player["character"] or {})
    character.update(patch)
    bunker_db.set_player_character(game_id, user_id, character)

    return web.json_response({"character": character})


@routes.post("/api/bunker/games/{id}/ability/{announcement_id}/apply")
@require_dashboard_access
async def bunker_apply_ability(request: web.Request) -> web.Response:
    try:
        game_id = int(request.match_info["id"])
        announcement_id = int(request.match_info["announcement_id"])
    except ValueError:
        return web.json_response({"error": "invalid_id"}, status=400)
    if _game_for_guild(game_id, request["guild_id"]) is None:
        return web.json_response({"error": "not_found"}, status=404)
    announcement = bunker_db.get_ability_announcement(announcement_id)
    if announcement is None or announcement["game_id"] != game_id:
        return web.json_response({"error": "not_found"}, status=404)
    bunker_db.mark_ability_announcement_applied(announcement_id)
    return web.json_response({"ok": True})


# ────────────────────────── Публичная ссылка игрока ──────────────────────────

@routes.get("/api/public/bunker/{token}")
async def bunker_public_state(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = bunker_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = bunker_db.get_game(player["game_id"])
    if game is None:
        return web.json_response({"error": "unknown_token"}, status=404)

    guild = request.app["bot"].get_guild(game["guild_id"])
    round_number = game["round_number"]
    lang = language_core.get_language(game["guild_id"])
    cat_name, cat_desc, cond_name, cond_desc = bunker_localize.localize_game_scenario(game, lang)

    all_players = bunker_db.list_players(game["id"])
    roster = []
    for p in all_players:
        full = not bool(p["alive"]) or p["user_id"] == player["user_id"]
        raw_character = p["character"] if full else _public_character_view(p["character"], p["revealed_fields"])
        roster.append({
            **_player_ref(guild, p),
            "alive": bool(p["alive"]),
            "character": bunker_localize.localize_character(raw_character, lang),
            "revealed_fields": p["revealed_fields"],
        })

    action_required = bool(player["alive"]) and game["status"] == "active" and game["phase"] == "vote"
    vote = bunker_db.get_vote(game["id"], round_number, player["user_id"]) if game["phase"] == "vote" else None

    alive_players = bunker_db.list_alive_players(game["id"])

    body = {
        "language": lang,
        "game_status": game["status"],
        "phase": game["phase"],
        "round_number": round_number,
        "phase_deadline_ts": game["phase_deadline_ts"],
        "bunker_capacity": game["bunker_capacity"],
        "catastrophe_name": cat_name,
        "catastrophe_description": cat_desc,
        "bunker_conditions_name": cond_name,
        "bunker_conditions_description": cond_desc,
        "your_alive": bool(player["alive"]),
        "your_character": bunker_localize.localize_character(player["character"], lang),
        "your_revealed_fields": player["revealed_fields"],
        "action_required": action_required,
        "your_vote_submitted": vote is not None,
        "your_submitted_target": str(vote["target_user_id"]) if vote and vote["target_user_id"] is not None else None,
        "alive_players": [_player_ref(guild, p) for p in alive_players],
        "roster": roster,
    }

    if game["phase"] == "vote":
        votes = bunker_db.get_votes(game["id"], round_number)
        by_id = {p["user_id"]: p for p in all_players}
        tally: dict[str | None, int] = {}
        for v in votes:
            key = str(v["target_user_id"]) if v["target_user_id"] is not None else None
            tally[key] = tally.get(key, 0) + 1
        body["vote_tally"] = [
            {
                "target": key,
                "target_display": (
                    _display_name(
                        guild,
                        int(key),
                        by_id.get(int(key), {}).get("display_name"),
                    )
                    if key
                    else None
                ),
                "count": count,
            }
            for key, count in sorted(tally.items(), key=lambda kv: -kv[1])
        ]

    return web.json_response(body)


@routes.post("/api/public/bunker/{token}/reveal")
async def bunker_public_reveal(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = bunker_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = bunker_db.get_game(player["game_id"])
    if game is None or game["status"] != "active":
        return web.json_response({"error": "game_ended"}, status=410)
    if not player["alive"]:
        return web.json_response({"error": "player_dead"}, status=403)
    if game["phase"] != "discussion":
        return web.json_response({"error": "wrong_phase"}, status=400)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    field_keys = body.get("field_keys")
    if not isinstance(field_keys, list) or not field_keys or not all(isinstance(k, str) for k in field_keys):
        return web.json_response({"error": "invalid_field_keys"}, status=400)
    if not set(field_keys) <= set(bunker_core.FIELD_KEYS):
        return web.json_response({"error": "invalid_field_keys"}, status=400)

    bunker_db.reveal_fields(game["id"], player["user_id"], field_keys)
    return web.json_response({"ok": True})


@routes.post("/api/public/bunker/{token}/vote")
async def bunker_public_vote(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = bunker_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = bunker_db.get_game(player["game_id"])
    if game is None or game["status"] != "active":
        return web.json_response({"error": "game_ended"}, status=410)
    if not player["alive"]:
        return web.json_response({"error": "player_dead"}, status=403)
    if game["phase"] != "vote":
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
        alive_ids = {p["user_id"] for p in bunker_db.list_alive_players(game["id"])}
        if target_user_id not in alive_ids:
            return web.json_response({"error": "invalid_target"}, status=400)

    bunker_db.upsert_vote(game["id"], game["round_number"], player["user_id"], target_user_id)

    cog = request.app["bot"].get_cog("BunkerCog")
    if cog is not None:
        await cog.refresh_vote_tally(game["id"])
        await cog.maybe_finish_vote_early(game["id"])

    return web.json_response({"ok": True})


@routes.post("/api/public/bunker/{token}/ability")
async def bunker_public_ability(request: web.Request) -> web.Response:
    token = request.match_info["token"]
    player = bunker_db.get_player_by_token(token)
    if player is None:
        return web.json_response({"error": "unknown_token"}, status=404)
    game = bunker_db.get_game(player["game_id"])
    if game is None or game["status"] != "active":
        return web.json_response({"error": "game_ended"}, status=410)
    if not player["alive"]:
        return web.json_response({"error": "player_dead"}, status=403)
    if game["phase"] == "vote":
        return web.json_response({"error": "wrong_phase"}, status=400)

    try:
        body = await request.json()
    except ValueError:
        return web.json_response({"error": "invalid_request"}, status=400)
    if not isinstance(body, dict):
        return web.json_response({"error": "invalid_request"}, status=400)

    card_index = body.get("card_index")
    if card_index not in (1, 2):
        return web.json_response({"error": "invalid_card_index"}, status=400)

    character = player["character"] or {}
    abilities = character.get("special_abilities") or []
    if card_index > len(abilities):
        return web.json_response({"error": "invalid_card_index"}, status=400)
    card = abilities[card_index - 1]
    if card.get("used"):
        return web.json_response({"error": "card_already_used"}, status=409)

    raw_target = body.get("target_user_id")
    target_user_id = None
    if raw_target is not None:
        if not isinstance(raw_target, str) or not raw_target.isdigit():
            return web.json_response({"error": "invalid_target"}, status=400)
        target_user_id = int(raw_target)
        known_ids = {p["user_id"] for p in bunker_db.list_players(game["id"])}
        if target_user_id not in known_ids:
            return web.json_response({"error": "invalid_target"}, status=400)

    note = body.get("note", "")
    if not isinstance(note, str) or len(note) > 300:
        return web.json_response({"error": "invalid_note"}, status=400)

    card["used"] = True
    bunker_db.set_player_character(game["id"], player["user_id"], character)
    announcement = bunker_db.create_ability_announcement(
        game["id"], game["round_number"], player["user_id"], card_index, card["name"], target_user_id, note,
    )

    cog = request.app["bot"].get_cog("BunkerCog")
    if cog is not None:
        await cog.announce_ability(game["id"], announcement)

    return web.json_response({"ok": True})
