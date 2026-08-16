"""Кастомки (custom lobbies): settings, ranks, map pool, balancer, lobby persistence.

Stored per-guild in settings_db under module name ``customs``.

Join modes:
- solo — individuals; host balances by rank into Team A / Team B
- team_code — players share a short code; balancer keeps stacks together
"""

from __future__ import annotations

import itertools
import random
import string
import time
from typing import Any

import settings_db
import valorant_maps

MODULE_NAME = "customs"

RANKS: tuple[dict[str, Any], ...] = (
    {"id": "iron", "name": "Iron", "weight": 1},
    {"id": "bronze", "name": "Bronze", "weight": 2},
    {"id": "silver", "name": "Silver", "weight": 3},
    {"id": "gold", "name": "Gold", "weight": 4},
    {"id": "platinum", "name": "Platinum", "weight": 5},
    {"id": "diamond", "name": "Diamond", "weight": 6},
    {"id": "ascendant", "name": "Ascendant", "weight": 7},
    {"id": "immortal", "name": "Immortal", "weight": 8},
    {"id": "radiant", "name": "Radiant", "weight": 9},
)

RANK_BY_ID = {r["id"]: r for r in RANKS}
RANK_IDS = tuple(r["id"] for r in RANKS)
LOWEST_RANK_ID = RANKS[0]["id"]
MAX_PLAYERS = 10
MAX_SUBS = 4
DEFAULT_VOTE_SECONDS = 45
TEAM_CODE_LEN = 5
# Avoid ambiguous 0/O, 1/I/L
TEAM_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"

JOIN_MODE_SOLO = "solo"
JOIN_MODE_TEAM_CODE = "team_code"
JOIN_MODES = frozenset({JOIN_MODE_SOLO, JOIN_MODE_TEAM_CODE})

PING_NONE = "none"
PING_PARTICIPANTS = "participants"
PING_ROLE = "role"
PING_MODES = frozenset({PING_NONE, PING_PARTICIPANTS, PING_ROLE})
# Legacy publish values; treated as none going forward.
PING_LEGACY = frozenset({"everyone", "here"})

STATUS_OPEN = "open"
STATUS_CHECKIN = "checkin"
STATUS_READY = "ready"
STATUS_LIVE = "live"
STATUS_FINISHED = "finished"
STATUS_CANCELLED = "cancelled"

ACTIVE_STATUSES = frozenset({STATUS_OPEN, STATUS_CHECKIN, STATUS_READY, STATUS_LIVE})

MAX_LOBBY_MAP_BANS = 2
DEFAULT_SIGNUP_MINUTES = 0
WEEKDAYS = (0, 1, 2, 3, 4, 5, 6)  # Monday–Sunday (guild TZ)


def _default_map_pool() -> dict[str, bool]:
    return {m["id"]: True for m in valorant_maps.MAPS}


def _default_rank_roles() -> dict[str, str]:
    return {rid: "" for rid in RANK_IDS}


def _empty_blob() -> dict[str, Any]:
    return {
        "enabled": False,
        "channel_id": "",
        "host_role_id": "",
        "voice_category_id": "",
        "auto_lobby_vc": True,
        "auto_move_on_start": True,
        "rank_roles": _default_rank_roles(),
        "map_pool": _default_map_pool(),
        "require_rank_role": True,
        "checkin_enabled": False,
        "vote_seconds": DEFAULT_VOTE_SECONDS,
        "xp_on_win": 0,
        "default_mode": JOIN_MODE_SOLO,
        "default_name": "Кастомка",
        "default_notes": "",
        "default_ping": PING_NONE,
        "ping_role_id": "",
        "default_signup_minutes": DEFAULT_SIGNUP_MINUTES,
        "avoid_last_map": True,
        "results_channel_id": "",
        "default_banned_maps": [],
        "features": {
            "side_random": True,
            "voting": True,
        },
        "last_map_id": "",
        "seq": 0,
        "schedule_seq": 0,
        "lobbies": {},
        "schedules": {},
        "stats": {},
    }


def load_data(guild_id: int) -> dict[str, Any]:
    return _normalized(settings_db.get(guild_id, MODULE_NAME))


def save_data(guild_id: int, data: dict[str, Any]) -> None:
    settings_db.put(guild_id, MODULE_NAME, _normalized(data))


def _normalized(data: dict | None) -> dict[str, Any]:
    base = _empty_blob()
    if not isinstance(data, dict):
        return base
    base["enabled"] = bool(data.get("enabled", False))
    channel_id = str(data.get("channel_id") or "")
    if channel_id and not channel_id.isdigit():
        channel_id = ""
    base["channel_id"] = channel_id
    host_role_id = str(data.get("host_role_id") or "")
    if host_role_id and not host_role_id.isdigit():
        host_role_id = ""
    base["host_role_id"] = host_role_id

    voice_category_id = str(data.get("voice_category_id") or "")
    if voice_category_id and not voice_category_id.isdigit():
        voice_category_id = ""
    base["voice_category_id"] = voice_category_id
    base["auto_lobby_vc"] = bool(data.get("auto_lobby_vc", True))
    base["auto_move_on_start"] = bool(data.get("auto_move_on_start", True))

    rank_roles = dict(base["rank_roles"])
    raw_ranks = data.get("rank_roles") if isinstance(data.get("rank_roles"), dict) else {}
    for rid in RANK_IDS:
        val = str(raw_ranks.get(rid) or "")
        if val and not val.isdigit():
            val = ""
        rank_roles[rid] = val
    base["rank_roles"] = rank_roles

    map_pool = dict(base["map_pool"])
    raw_pool = data.get("map_pool") if isinstance(data.get("map_pool"), dict) else {}
    for mid in map_pool:
        if mid in raw_pool:
            map_pool[mid] = bool(raw_pool[mid])
    base["map_pool"] = map_pool

    base["require_rank_role"] = bool(data.get("require_rank_role", True))
    # Check-in UI removed; keep field for legacy blobs, default off.
    base["checkin_enabled"] = bool(data.get("checkin_enabled", False))
    try:
        vote_seconds = int(data.get("vote_seconds", DEFAULT_VOTE_SECONDS))
    except (TypeError, ValueError):
        vote_seconds = DEFAULT_VOTE_SECONDS
    base["vote_seconds"] = max(15, min(300, vote_seconds))
    try:
        xp_on_win = int(data.get("xp_on_win", 0) or 0)
    except (TypeError, ValueError):
        xp_on_win = 0
    base["xp_on_win"] = max(0, min(50_000, xp_on_win))

    default_mode = str(data.get("default_mode") or JOIN_MODE_SOLO)
    if default_mode not in JOIN_MODES:
        default_mode = JOIN_MODE_SOLO
    base["default_mode"] = default_mode

    base["default_name"] = str(data.get("default_name") or "Кастомка").strip()[:80] or "Кастомка"
    base["default_notes"] = str(data.get("default_notes") or "").strip()[:500]
    default_ping = str(data.get("default_ping") or PING_NONE)
    if default_ping in PING_LEGACY:
        default_ping = PING_NONE
    if default_ping not in PING_MODES:
        default_ping = PING_NONE
    base["default_ping"] = default_ping
    ping_role_id = str(data.get("ping_role_id") or "")
    if ping_role_id and not ping_role_id.isdigit():
        ping_role_id = ""
    base["ping_role_id"] = ping_role_id
    try:
        signup_min = int(data.get("default_signup_minutes") or DEFAULT_SIGNUP_MINUTES)
    except (TypeError, ValueError):
        signup_min = DEFAULT_SIGNUP_MINUTES
    base["default_signup_minutes"] = max(0, min(240, signup_min))
    base["avoid_last_map"] = bool(data.get("avoid_last_map", True))
    results_channel_id = str(data.get("results_channel_id") or "")
    if results_channel_id and not results_channel_id.isdigit():
        results_channel_id = ""
    base["results_channel_id"] = results_channel_id
    base["default_banned_maps"] = _normalize_map_id_list(data.get("default_banned_maps"), limit=None)

    feats = data.get("features") if isinstance(data.get("features"), dict) else {}
    for key in ("side_random", "voting"):
        if key in feats:
            base["features"][key] = bool(feats[key])
    # Legacy keys ignored (captains / veto removed).

    base["last_map_id"] = str(data.get("last_map_id") or "")
    try:
        base["seq"] = int(data.get("seq") or 0)
    except (TypeError, ValueError):
        base["seq"] = 0
    try:
        base["schedule_seq"] = int(data.get("schedule_seq") or 0)
    except (TypeError, ValueError):
        base["schedule_seq"] = 0
    lobbies = data.get("lobbies") if isinstance(data.get("lobbies"), dict) else {}
    base["lobbies"] = {str(k): _normalize_lobby(v) for k, v in lobbies.items() if isinstance(v, dict)}
    schedules = data.get("schedules") if isinstance(data.get("schedules"), dict) else {}
    normalized_schedules: dict[str, Any] = {}
    for k, v in schedules.items():
        if not isinstance(v, dict):
            continue
        sch = _normalize_schedule(v, str(k))
        if sch is not None:
            normalized_schedules[str(k)] = sch
    base["schedules"] = normalized_schedules
    stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}
    base["stats"] = {str(k): v for k, v in stats.items() if isinstance(v, dict)}
    return base


def _normalize_map_id_list(raw: Any, *, limit: int | None) -> list[str]:
    valid = {m["id"] for m in valorant_maps.MAPS}
    if not isinstance(raw, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        mid = str(item or "")
        if mid not in valid or mid in seen:
            continue
        seen.add(mid)
        out.append(mid)
        if limit is not None and len(out) >= limit:
            break
    return out


def _normalize_ping(raw: Any) -> str:
    ping = str(raw or PING_NONE)
    if ping in PING_LEGACY:
        return PING_NONE
    return ping if ping in PING_MODES else PING_NONE


def _normalize_schedule(row: dict[str, Any], sid: str) -> dict[str, Any] | None:
    try:
        weekday = int(row.get("weekday"))
        hour = int(row.get("hour"))
        minute = int(row.get("minute") or 0)
    except (TypeError, ValueError):
        return None
    if weekday not in WEEKDAYS or not (0 <= hour <= 23) or not (0 <= minute <= 59):
        return None
    join_mode = str(row.get("join_mode") or JOIN_MODE_SOLO)
    if join_mode not in JOIN_MODES:
        join_mode = JOIN_MODE_SOLO
    channel_id = str(row.get("channel_id") or "")
    if channel_id and not channel_id.isdigit():
        channel_id = ""
    try:
        signup_minutes = int(row.get("signup_minutes") or 0)
    except (TypeError, ValueError):
        signup_minutes = 0
    return {
        "id": str(row.get("id") or sid),
        "enabled": bool(row.get("enabled", True)),
        "weekday": weekday,
        "hour": hour,
        "minute": minute,
        "name": str(row.get("name") or "Кастомка").strip()[:80] or "Кастомка",
        "notes": str(row.get("notes") or "").strip()[:500],
        "join_mode": join_mode,
        "channel_id": channel_id,
        "ping": _normalize_ping(row.get("ping")),
        "signup_minutes": max(0, min(240, signup_minutes)),
        "last_run": str(row.get("last_run") or ""),
    }


def _normalize_lobby(lobby: dict[str, Any]) -> dict[str, Any]:
    out = dict(lobby)
    join_mode = str(out.get("join_mode") or out.get("mode") or JOIN_MODE_SOLO)
    if join_mode in ("balanced", "captains"):
        join_mode = JOIN_MODE_SOLO
    if join_mode not in JOIN_MODES:
        join_mode = JOIN_MODE_SOLO
    out["join_mode"] = join_mode
    out.pop("captains", None)
    out.pop("veto", None)
    out["vote_message_id"] = str(out.get("vote_message_id") or "")
    out["score_message_id"] = str(out.get("score_message_id") or "")
    out["ping"] = _normalize_ping(out.get("ping"))
    try:
        out["signup_minutes"] = max(0, min(240, int(out.get("signup_minutes") or 0)))
    except (TypeError, ValueError):
        out["signup_minutes"] = 0
    try:
        out["signup_ends_at"] = int(out.get("signup_ends_at") or 0)
    except (TypeError, ValueError):
        out["signup_ends_at"] = 0
    out["banned_maps"] = _normalize_map_id_list(out.get("banned_maps"), limit=MAX_LOBBY_MAP_BANS)
    for key in ("lobby_vc_id", "team_a_vc_id", "team_b_vc_id"):
        raw = str(out.get(key) or "")
        out[key] = raw if raw.isdigit() else ""
    for key in ("players", "subs", "team_a", "team_b"):
        rows = out.get(key)
        if isinstance(rows, list):
            out[key] = [_normalize_player(p) for p in rows if isinstance(p, dict)]
    return out


def _normalize_player(p: dict[str, Any]) -> dict[str, Any]:
    row = dict(p)
    code = str(row.get("team_code") or "").strip().upper()
    row["team_code"] = code
    for key in ("nick", "username", "global_name", "display_name"):
        row[key] = str(row.get(key) or "")
    if not row["display_name"]:
        row["display_name"] = row["nick"] or row["global_name"] or row["username"] or ""
    return row


def get_settings(guild_id: int) -> dict[str, Any]:
    data = load_data(guild_id)
    return {
        "enabled": data["enabled"],
        "channel_id": data["channel_id"],
        "host_role_id": data["host_role_id"],
        "voice_category_id": data["voice_category_id"],
        "auto_lobby_vc": data["auto_lobby_vc"],
        "auto_move_on_start": data["auto_move_on_start"],
        "rank_roles": dict(data["rank_roles"]),
        "map_pool": dict(data["map_pool"]),
        "require_rank_role": data["require_rank_role"],
        "checkin_enabled": data["checkin_enabled"],
        "vote_seconds": data["vote_seconds"],
        "xp_on_win": data["xp_on_win"],
        "default_mode": data["default_mode"],
        "default_name": data["default_name"],
        "default_notes": data["default_notes"],
        "default_ping": data["default_ping"],
        "ping_role_id": data["ping_role_id"],
        "default_signup_minutes": data["default_signup_minutes"],
        "avoid_last_map": data["avoid_last_map"],
        "results_channel_id": data["results_channel_id"],
        "default_banned_maps": list(data["default_banned_maps"]),
        "features": dict(data["features"]),
        "last_map_id": data["last_map_id"],
        "schedules": [
            dict(sch)
            for _, sch in sorted(data["schedules"].items(), key=lambda kv: int(kv[0]) if str(kv[0]).isdigit() else 0)
        ],
        "ranks": [{"id": r["id"], "name": r["name"], "weight": r["weight"]} for r in RANKS],
        "maps": [
            {"id": m["id"], "name": m["name"], "enabled": bool(data["map_pool"].get(m["id"], True))}
            for m in valorant_maps.MAPS
        ],
    }


def save_settings(guild_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    data = load_data(guild_id)
    if "enabled" in payload:
        data["enabled"] = bool(payload["enabled"])
    if "channel_id" in payload:
        channel_id = str(payload.get("channel_id") or "")
        if channel_id and not channel_id.isdigit():
            channel_id = ""
        data["channel_id"] = channel_id
    if "host_role_id" in payload:
        host_role_id = str(payload.get("host_role_id") or "")
        if host_role_id and not host_role_id.isdigit():
            host_role_id = ""
        data["host_role_id"] = host_role_id
    if "voice_category_id" in payload:
        voice_category_id = str(payload.get("voice_category_id") or "")
        if voice_category_id and not voice_category_id.isdigit():
            voice_category_id = ""
        data["voice_category_id"] = voice_category_id
    if "auto_lobby_vc" in payload:
        data["auto_lobby_vc"] = bool(payload["auto_lobby_vc"])
    if "auto_move_on_start" in payload:
        data["auto_move_on_start"] = bool(payload["auto_move_on_start"])
    if isinstance(payload.get("rank_roles"), dict):
        for rid in RANK_IDS:
            if rid in payload["rank_roles"]:
                val = str(payload["rank_roles"].get(rid) or "")
                if val and not val.isdigit():
                    val = ""
                data["rank_roles"][rid] = val
    if isinstance(payload.get("map_pool"), dict):
        for mid in list(data["map_pool"]):
            if mid in payload["map_pool"]:
                data["map_pool"][mid] = bool(payload["map_pool"][mid])
    if "require_rank_role" in payload:
        data["require_rank_role"] = bool(payload["require_rank_role"])
    if "checkin_enabled" in payload:
        data["checkin_enabled"] = bool(payload["checkin_enabled"])
    if "vote_seconds" in payload:
        try:
            data["vote_seconds"] = max(15, min(300, int(payload["vote_seconds"])))
        except (TypeError, ValueError):
            pass
    if "xp_on_win" in payload:
        try:
            data["xp_on_win"] = max(0, min(50_000, int(payload["xp_on_win"] or 0)))
        except (TypeError, ValueError):
            pass
    if "default_mode" in payload:
        mode = str(payload.get("default_mode") or JOIN_MODE_SOLO)
        data["default_mode"] = mode if mode in JOIN_MODES else JOIN_MODE_SOLO
    if "default_name" in payload:
        data["default_name"] = str(payload.get("default_name") or "Кастомка").strip()[:80] or "Кастомка"
    if "default_notes" in payload:
        data["default_notes"] = str(payload.get("default_notes") or "").strip()[:500]
    if "default_ping" in payload:
        data["default_ping"] = _normalize_ping(payload.get("default_ping"))
    if "ping_role_id" in payload:
        ping_role_id = str(payload.get("ping_role_id") or "")
        if ping_role_id and not ping_role_id.isdigit():
            ping_role_id = ""
        data["ping_role_id"] = ping_role_id
    if "default_signup_minutes" in payload:
        try:
            data["default_signup_minutes"] = max(0, min(240, int(payload.get("default_signup_minutes") or 0)))
        except (TypeError, ValueError):
            pass
    if "avoid_last_map" in payload:
        data["avoid_last_map"] = bool(payload["avoid_last_map"])
    if "results_channel_id" in payload:
        results_channel_id = str(payload.get("results_channel_id") or "")
        if results_channel_id and not results_channel_id.isdigit():
            results_channel_id = ""
        data["results_channel_id"] = results_channel_id
    if "default_banned_maps" in payload:
        data["default_banned_maps"] = _normalize_map_id_list(payload.get("default_banned_maps"), limit=None)
    if isinstance(payload.get("features"), dict):
        for key in ("side_random", "voting"):
            if key in payload["features"]:
                data["features"][key] = bool(payload["features"][key])
    if isinstance(payload.get("schedules"), list):
        rebuilt: dict[str, Any] = {}
        seq = 0
        for row in payload["schedules"]:
            if not isinstance(row, dict):
                continue
            seq += 1
            sid = str(row.get("id") or seq)
            sch = _normalize_schedule(row, sid)
            if sch is None:
                continue
            sch["id"] = sid
            rebuilt[sid] = sch
        data["schedules"] = rebuilt
        data["schedule_seq"] = max(seq, int(data.get("schedule_seq") or 0))
    save_data(guild_id, data)
    return get_settings(guild_id)


def enabled_maps(guild_id: int | None = None, data: dict | None = None) -> list[dict[str, str]]:
    blob = data if data is not None else (load_data(guild_id) if guild_id is not None else _empty_blob())
    pool = blob.get("map_pool") or _default_map_pool()
    out = []
    for m in valorant_maps.MAPS:
        if pool.get(m["id"], True):
            out.append(m)
    return out or list(valorant_maps.MAPS)


def maps_for_pick(
    guild_id: int | None = None,
    *,
    data: dict | None = None,
    lobby: dict | None = None,
) -> list[dict[str, str]]:
    """Enabled pool minus global default bans and per-lobby bans."""
    blob = data if data is not None else (load_data(guild_id) if guild_id is not None else _empty_blob())
    pool = enabled_maps(data=blob)
    banned: set[str] = set(blob.get("default_banned_maps") or [])
    if lobby is not None:
        banned.update(lobby.get("banned_maps") or [])
    remaining = [m for m in pool if m["id"] not in banned]
    return remaining or list(pool)


def pick_random_map(
    guild_id: int,
    *,
    avoid_last: bool | None = None,
    lobby: dict | None = None,
) -> dict[str, str]:
    data = load_data(guild_id)
    if avoid_last is None:
        avoid_last = bool(data.get("avoid_last_map", True))
    pool = maps_for_pick(data=data, lobby=lobby)
    last = data.get("last_map_id") or ""
    candidates = [m for m in pool if m["id"] != last] if avoid_last and len(pool) > 1 else list(pool)
    if not candidates:
        candidates = list(pool) or list(valorant_maps.MAPS)
    chosen = random.choice(candidates)
    data["last_map_id"] = chosen["id"]
    save_data(guild_id, data)
    return chosen


def rank_from_role_ids(member_role_ids: set[str] | list[str], rank_roles: dict[str, str]) -> dict[str, Any] | None:
    """Highest configured rank among the member's Discord roles."""
    role_set = {str(r) for r in member_role_ids}
    best: dict[str, Any] | None = None
    for rank in RANKS:
        role_id = str(rank_roles.get(rank["id"]) or "")
        if not role_id or role_id not in role_set:
            continue
        if best is None or rank["weight"] > best["weight"]:
            best = {"id": rank["id"], "name": rank["name"], "weight": rank["weight"]}
    return best


def rank_by_id(rank_id: str) -> dict[str, Any] | None:
    rank = RANK_BY_ID.get(str(rank_id))
    if rank is None:
        return None
    return {"id": rank["id"], "name": rank["name"], "weight": rank["weight"]}


def configured_rank_role_ids(rank_roles: dict[str, str]) -> list[int]:
    out: list[int] = []
    for rid in RANK_IDS:
        raw = str(rank_roles.get(rid) or "")
        if raw.isdigit():
            out.append(int(raw))
    return out


def rank_weight(rank_id: str | None) -> int:
    if not rank_id:
        return RANK_BY_ID[LOWEST_RANK_ID]["weight"]
    return int(RANK_BY_ID.get(rank_id, RANK_BY_ID[LOWEST_RANK_ID])["weight"])


def _team_mmr(players: list[dict[str, Any]]) -> int:
    return sum(int(p.get("weight") or rank_weight(p.get("rank"))) for p in players)


def _unit_weight(unit: list[dict[str, Any]]) -> int:
    return _team_mmr(unit)


def _group_units(players: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    stacks: dict[str, list[dict[str, Any]]] = {}
    units: list[list[dict[str, Any]]] = []
    for p in players:
        code = str(p.get("team_code") or "").strip().upper()
        if code:
            stacks.setdefault(code, []).append(p)
        else:
            units.append([p])
    units.extend(stacks.values())
    return units


def fair_split(players: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    """Minimize absolute MMR difference; keep same team_code players together."""
    n = len(players)
    if n == 0:
        return [], [], 0
    if n == 1:
        return [players[0]], [], int(players[0].get("weight") or 0)

    units = _group_units(players)
    if len(units) == 1:
        # Single stack — split individuals only if no codes (shouldn't happen for one coded stack).
        only = units[0]
        if len(only) == 1 or any(str(p.get("team_code") or "") for p in only):
            mid = (len(only) + 1) // 2
            # Keep coded stack intact on team A; empty B if whole lobby is one stack.
            if any(str(p.get("team_code") or "") for p in only):
                return list(only), [], _unit_weight(only)
            return list(only[:mid]), list(only[mid:]), abs(_team_mmr(only[:mid]) - _team_mmr(only[mid:]))

    indexed = list(enumerate(units))
    best_diff: int | None = None
    best_a: tuple[int, ...] | None = None
    best_size_gap: int | None = None
    total = n
    target = total / 2

    for r in range(1, len(indexed)):
        for combo in itertools.combinations(indexed, r):
            a_idx = tuple(i for i, _ in combo)
            team_a = [p for i, u in combo for p in u]
            team_b = [p for i, u in indexed if i not in a_idx for p in u]
            if not team_a or not team_b:
                continue
            diff = abs(_team_mmr(team_a) - _team_mmr(team_b))
            size_gap = abs(len(team_a) - target) + abs(len(team_b) - target)
            if (
                best_diff is None
                or diff < best_diff
                or (diff == best_diff and best_size_gap is not None and size_gap < best_size_gap)
            ):
                best_diff = diff
                best_a = a_idx
                best_size_gap = size_gap
                if diff == 0 and size_gap <= 1:
                    break
        if best_diff == 0 and best_size_gap is not None and best_size_gap <= 1:
            break

    if best_a is None or best_diff is None:
        # Fallback: classic individual split ignoring codes.
        return _fair_split_individuals(players)

    team_a = [p for i, u in indexed if i in best_a for p in u]
    team_b = [p for i, u in indexed if i not in best_a for p in u]
    return team_a, team_b, best_diff


def _fair_split_individuals(
    players: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    indexed = list(enumerate(players))
    target_a = (len(players) + 1) // 2
    best_diff = None
    best_a_idx: tuple[int, ...] | None = None
    for combo in itertools.combinations(indexed, target_a):
        a_idx = tuple(i for i, _ in combo)
        team_a = [p for _, p in combo]
        team_b = [p for i, p in indexed if i not in a_idx]
        diff = abs(_team_mmr(team_a) - _team_mmr(team_b))
        if best_diff is None or diff < best_diff:
            best_diff = diff
            best_a_idx = a_idx
            if diff == 0:
                break
    assert best_a_idx is not None and best_diff is not None
    team_a = [players[i] for i in best_a_idx]
    team_b = [p for i, p in enumerate(players) if i not in best_a_idx]
    return team_a, team_b, best_diff


def random_presets(players: list[dict[str, Any]], count: int = 3) -> list[dict[str, Any]]:
    """Return up to ``count`` distinct balance presets (fair + shuffled rebalances)."""
    count = max(1, min(5, count))
    presets: list[dict[str, Any]] = []
    seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()

    def _add(team_a: list[dict], team_b: list[dict], label: str) -> None:
        key = (
            tuple(sorted(str(p["user_id"]) for p in team_a)),
            tuple(sorted(str(p["user_id"]) for p in team_b)),
        )
        key_n = tuple(sorted(key))
        if key_n in seen:
            return
        seen.add(key_n)
        presets.append(
            {
                "label": label,
                "team_a": [dict(p) for p in team_a],
                "team_b": [dict(p) for p in team_b],
                "diff": abs(_team_mmr(team_a) - _team_mmr(team_b)),
                "mmr_a": _team_mmr(team_a),
                "mmr_b": _team_mmr(team_b),
            }
        )

    a, b, _ = fair_split(players)
    _add(a, b, "fair")

    units = _group_units(players)
    attempts = 0
    while len(presets) < count and attempts < 40:
        attempts += 1
        shuffled = list(units)
        random.shuffle(shuffled)
        team_a: list[dict] = []
        team_b: list[dict] = []
        for unit in shuffled:
            if _team_mmr(team_a) <= _team_mmr(team_b):
                team_a.extend(unit)
            else:
                team_b.extend(unit)
        if not team_a or not team_b:
            continue
        _add(team_a, team_b, f"preset_{len(presets) + 1}")

    return presets


def generate_team_code(existing: set[str] | None = None, length: int = TEAM_CODE_LEN) -> str:
    existing = existing or set()
    length = max(4, min(6, int(length)))
    for _ in range(80):
        code = "".join(random.choices(TEAM_CODE_ALPHABET, k=length))
        if code not in existing:
            return code
    # Extremely unlikely collision path.
    return "".join(random.choices(string.ascii_uppercase, k=length))


def normalize_team_code(raw: str) -> str:
    return "".join(ch for ch in str(raw or "").strip().upper() if ch.isalnum())[:6]


def create_lobby(
    guild_id: int,
    *,
    host_id: int,
    name: str,
    notes: str = "",
    join_mode: str | None = None,
    max_players: int = MAX_PLAYERS,
    max_subs: int = MAX_SUBS,
    ping: str | None = None,
    signup_minutes: int | None = None,
    banned_maps: list[str] | None = None,
) -> dict[str, Any]:
    data = load_data(guild_id)
    data["seq"] += 1
    lobby_id = str(data["seq"])
    mode = str(join_mode or data.get("default_mode") or JOIN_MODE_SOLO)
    if mode not in JOIN_MODES:
        mode = JOIN_MODE_SOLO
    ping_mode = _normalize_ping(ping if ping is not None else data.get("default_ping"))
    try:
        minutes = int(signup_minutes if signup_minutes is not None else data.get("default_signup_minutes") or 0)
    except (TypeError, ValueError):
        minutes = 0
    minutes = max(0, min(240, minutes))
    now = int(time.time())
    name_val = (name or data.get("default_name") or "Кастомка").strip()[:80] or "Кастомка"
    notes_val = (notes if notes is not None else str(data.get("default_notes") or "")).strip()[:500]
    lobby = {
        "id": lobby_id,
        "guild_id": str(guild_id),
        "name": name_val,
        "notes": notes_val,
        "host_id": str(host_id),
        "status": STATUS_OPEN,
        "join_mode": mode,
        "players": [],
        "subs": [],
        "max_players": max(2, min(MAX_PLAYERS, int(max_players))),
        "max_subs": max(0, min(MAX_SUBS, int(max_subs))),
        "team_a": [],
        "team_b": [],
        "balance_presets": [],
        "selected_preset": 0,
        "map_id": "",
        "map_name": "",
        "riot_code": "",
        "side": "",
        "vote": None,
        "checkins": {},
        "score": {"a": 0, "b": 0},
        "channel_id": "",
        "message_id": "",
        "vote_message_id": "",
        "score_message_id": "",
        "lobby_vc_id": "",
        "team_a_vc_id": "",
        "team_b_vc_id": "",
        "ping": ping_mode,
        "signup_minutes": minutes,
        "signup_ends_at": (now + minutes * 60) if minutes > 0 else 0,
        "banned_maps": _normalize_map_id_list(banned_maps or [], limit=MAX_LOBBY_MAP_BANS),
        "created_at": now,
        "closed_at": None,
    }
    data["lobbies"][lobby_id] = lobby
    save_data(guild_id, data)
    return lobby


def get_lobby(guild_id: int, lobby_id: str) -> dict[str, Any] | None:
    return load_data(guild_id)["lobbies"].get(str(lobby_id))


def get_lobby_by_message(guild_id: int, message_id: int) -> dict[str, Any] | None:
    mid = str(message_id)
    for lobby in load_data(guild_id)["lobbies"].values():
        if lobby.get("message_id") == mid:
            return lobby
    return None


def get_lobby_by_vote_message(guild_id: int, message_id: int) -> dict[str, Any] | None:
    mid = str(message_id)
    for lobby in load_data(guild_id)["lobbies"].values():
        if lobby.get("vote_message_id") == mid:
            return lobby
    return None


def get_lobby_by_score_message(guild_id: int, message_id: int) -> dict[str, Any] | None:
    mid = str(message_id)
    for lobby in load_data(guild_id)["lobbies"].values():
        if lobby.get("score_message_id") == mid:
            return lobby
    return None


def update_lobby(guild_id: int, lobby_id: str, **fields: Any) -> dict[str, Any] | None:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return None
    lobby.update(fields)
    save_data(guild_id, data)
    return lobby


def list_active_lobbies(guild_id: int) -> list[dict[str, Any]]:
    return [
        lob
        for lob in load_data(guild_id)["lobbies"].values()
        if lob.get("status") in ACTIVE_STATUSES
    ]


def list_lobbies(guild_id: int, *, status: str | None = None) -> list[dict[str, Any]]:
    lobbies = list(load_data(guild_id)["lobbies"].values())
    if status == "active":
        lobbies = [lob for lob in lobbies if lob.get("status") in ACTIVE_STATUSES]
    elif status:
        lobbies = [lob for lob in lobbies if lob.get("status") == status]
    lobbies.sort(key=lambda lob: int(lob.get("created_at") or 0), reverse=True)
    return lobbies


def identity_from_member(member: Any) -> dict[str, str]:
    """Extract Discord name fields from a Member/User for roster storage."""
    if member is None:
        return {"nick": "", "username": "", "global_name": "", "display_name": ""}
    nick = str(getattr(member, "nick", None) or "")
    username = str(getattr(member, "name", None) or "")
    global_name = str(getattr(member, "global_name", None) or "")
    display_name = str(getattr(member, "display_name", None) or "") or (
        nick or global_name or username
    )
    return {
        "nick": nick,
        "username": username,
        "global_name": global_name,
        "display_name": display_name,
    }


def _resolve_player_names(p: dict[str, Any], guild: Any | None) -> dict[str, str]:
    """Prefer live guild cache, then stored join-time names."""
    uid = str(p.get("user_id") or "")
    stored = {
        "nick": str(p.get("nick") or ""),
        "username": str(p.get("username") or ""),
        "global_name": str(p.get("global_name") or ""),
        "display_name": str(p.get("display_name") or ""),
    }
    if guild is not None and uid.isdigit():
        member = guild.get_member(int(uid))
        if member is not None:
            return identity_from_member(member)
    if not stored["display_name"]:
        stored["display_name"] = (
            stored["nick"] or stored["global_name"] or stored["username"] or ""
        )
    return stored


def serialize_player(p: dict[str, Any], *, guild: Any | None = None) -> dict[str, Any]:
    names = _resolve_player_names(p, guild)
    return {
        "user_id": str(p.get("user_id") or ""),
        "rank": p.get("rank") or "",
        "rank_name": p.get("rank_name") or "",
        "team_code": p.get("team_code") or "",
        "team": p.get("team"),
        "nick": names["nick"],
        "username": names["username"],
        "global_name": names["global_name"],
        "display_name": names["display_name"],
    }


def serialize_lobby_summary(lobby: dict[str, Any], *, guild: Any | None = None) -> dict[str, Any]:
    score = lobby.get("score") if isinstance(lobby.get("score"), dict) else {}
    return {
        "id": str(lobby.get("id")),
        "name": lobby.get("name") or "",
        "notes": lobby.get("notes") or "",
        "status": lobby.get("status") or STATUS_OPEN,
        "join_mode": lobby.get("join_mode") or JOIN_MODE_SOLO,
        "channel_id": str(lobby.get("channel_id") or ""),
        "message_id": str(lobby.get("message_id") or ""),
        "host_id": str(lobby.get("host_id") or ""),
        "players": len(lobby.get("players") or []),
        "max_players": int(lobby.get("max_players") or MAX_PLAYERS),
        "map_id": lobby.get("map_id") or "",
        "map_name": lobby.get("map_name") or "",
        "side": lobby.get("side") or "",
        "ping": _normalize_ping(lobby.get("ping")),
        "banned_maps": list(lobby.get("banned_maps") or []),
        "signup_minutes": int(lobby.get("signup_minutes") or 0),
        "signup_ends_at": int(lobby.get("signup_ends_at") or 0),
        "score": {"a": int(score.get("a") or 0), "b": int(score.get("b") or 0)},
        "players_list": [
            serialize_player(p, guild=guild) for p in lobby.get("players") or [] if isinstance(p, dict)
        ],
        "subs_list": [
            serialize_player(p, guild=guild) for p in lobby.get("subs") or [] if isinstance(p, dict)
        ],
        "created_at": int(lobby.get("created_at") or 0),
    }


def _player_entry(
    user_id: int,
    rank: dict[str, Any] | None,
    *,
    team_code: str = "",
    nick: str = "",
    username: str = "",
    global_name: str = "",
    display_name: str = "",
) -> dict[str, Any]:
    rank = rank or {"id": LOWEST_RANK_ID, "name": RANK_BY_ID[LOWEST_RANK_ID]["name"], "weight": 1}
    nick_s = str(nick or "")
    username_s = str(username or "")
    global_name_s = str(global_name or "")
    display_s = str(display_name or "") or (nick_s or global_name_s or username_s)
    return {
        "user_id": str(user_id),
        "rank": rank["id"],
        "rank_name": rank["name"],
        "weight": int(rank["weight"]),
        "team_code": normalize_team_code(team_code),
        "team": None,
        "checked_in": False,
        "nick": nick_s,
        "username": username_s,
        "global_name": global_name_s,
        "display_name": display_s,
    }


def _existing_codes(lobby: dict[str, Any]) -> set[str]:
    codes: set[str] = set()
    for p in (lobby.get("players") or []) + (lobby.get("subs") or []):
        code = str(p.get("team_code") or "")
        if code:
            codes.add(code)
    return codes


def join_lobby(
    guild_id: int,
    lobby_id: str,
    user_id: int,
    rank: dict[str, Any] | None,
    *,
    as_sub: bool = False,
    team_code: str = "",
    create_code: bool = False,
    identity: dict[str, str] | None = None,
) -> tuple[str, dict[str, Any] | None]:
    """Returns (status, lobby_or_none). Status: joined | joined_sub | already | full | closed | not_found | no_rank | bad_code."""
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return "not_found", None
    if lobby.get("status") not in (STATUS_OPEN, STATUS_CHECKIN):
        return "closed", lobby

    uid = str(user_id)
    if any(p["user_id"] == uid for p in lobby["players"]) or any(p["user_id"] == uid for p in lobby["subs"]):
        return "already", lobby

    if data.get("require_rank_role") and rank is None:
        return "no_rank", lobby

    join_mode = lobby.get("join_mode") or JOIN_MODE_SOLO
    code = ""
    if join_mode == JOIN_MODE_TEAM_CODE:
        if create_code:
            code = generate_team_code(_existing_codes(lobby))
        else:
            code = normalize_team_code(team_code)
            if len(code) < 4:
                return "bad_code", lobby
            # Joining an existing code is preferred; creating alone with typed code is allowed.

    ident = identity or {}
    entry = _player_entry(
        user_id,
        rank,
        team_code=code,
        nick=str(ident.get("nick") or ""),
        username=str(ident.get("username") or ""),
        global_name=str(ident.get("global_name") or ""),
        display_name=str(ident.get("display_name") or ""),
    )
    if as_sub:
        if len(lobby["subs"]) >= int(lobby.get("max_subs") or MAX_SUBS):
            return "full", lobby
        lobby["subs"].append(entry)
        save_data(guild_id, data)
        return "joined_sub", lobby

    if len(lobby["players"]) >= int(lobby.get("max_players") or MAX_PLAYERS):
        if len(lobby["subs"]) < int(lobby.get("max_subs") or MAX_SUBS):
            lobby["subs"].append(entry)
            save_data(guild_id, data)
            return "joined_sub", lobby
        return "full", lobby

    lobby["players"].append(entry)
    save_data(guild_id, data)
    return "joined", lobby


def set_player_rank(
    guild_id: int,
    lobby_id: str,
    user_id: int,
    rank: dict[str, Any],
) -> str:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return "not_found"
    if lobby.get("status") not in ACTIVE_STATUSES:
        return "closed"
    uid = str(user_id)
    found = False
    for bucket in ("players", "subs", "team_a", "team_b"):
        for p in lobby.get(bucket) or []:
            if p.get("user_id") == uid:
                p["rank"] = rank["id"]
                p["rank_name"] = rank["name"]
                p["weight"] = int(rank["weight"])
                found = True
    if not found:
        return "not_in"
    save_data(guild_id, data)
    return "ok"


def leave_lobby(guild_id: int, lobby_id: str, user_id: int) -> str:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return "not_found"
    if lobby.get("status") not in ACTIVE_STATUSES:
        return "closed"
    uid = str(user_id)
    before_p = len(lobby["players"])
    before_s = len(lobby["subs"])
    lobby["players"] = [p for p in lobby["players"] if p["user_id"] != uid]
    lobby["subs"] = [p for p in lobby["subs"] if p["user_id"] != uid]
    if len(lobby["players"]) == before_p and len(lobby["subs"]) == before_s:
        return "not_in"
    lobby["team_a"] = [p for p in lobby.get("team_a") or [] if p.get("user_id") != uid]
    lobby["team_b"] = [p for p in lobby.get("team_b") or [] if p.get("user_id") != uid]
    save_data(guild_id, data)
    return "left"


def kick_player(guild_id: int, lobby_id: str, user_id: int) -> str:
    """Host/admin kick — same as leave, frees the slot."""
    result = leave_lobby(guild_id, lobby_id, user_id)
    return "kicked" if result == "left" else result


def promote_sub(guild_id: int, lobby_id: str, user_id: int) -> str:
    """Move a sub into the main roster if a seat is free."""
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return "not_found"
    if lobby.get("status") not in (STATUS_OPEN, STATUS_CHECKIN, STATUS_READY):
        return "closed"
    uid = str(user_id)
    sub = next((p for p in lobby["subs"] if p["user_id"] == uid), None)
    if sub is None:
        return "not_sub"
    if len(lobby["players"]) >= int(lobby.get("max_players") or MAX_PLAYERS):
        return "full"
    lobby["subs"] = [p for p in lobby["subs"] if p["user_id"] != uid]
    lobby["players"].append(sub)
    save_data(guild_id, data)
    return "promoted"


def apply_balance(guild_id: int, lobby_id: str, preset_index: int = 0) -> dict[str, Any] | None:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return None
    players = list(lobby.get("players") or [])
    presets = random_presets(players, count=3)
    lobby["balance_presets"] = presets
    idx = max(0, min(len(presets) - 1, int(preset_index))) if presets else 0
    lobby["selected_preset"] = idx
    if presets:
        chosen = presets[idx]
        lobby["team_a"] = chosen["team_a"]
        lobby["team_b"] = chosen["team_b"]
        for p in lobby["team_a"]:
            p["team"] = "A"
        for p in lobby["team_b"]:
            p["team"] = "B"
    save_data(guild_id, data)
    return lobby


def start_vote(
    guild_id: int,
    lobby_id: str,
    *,
    kind: str,
    options: list[dict[str, str]],
    seconds: int | None = None,
) -> dict[str, Any] | None:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return None
    secs = int(seconds if seconds is not None else data.get("vote_seconds") or DEFAULT_VOTE_SECONDS)
    lobby["vote"] = {
        "kind": kind,
        "options": options,
        "votes": {},
        "ends_at": int(time.time()) + max(15, min(300, secs)),
        "applied": False,
    }
    save_data(guild_id, data)
    return lobby


def cast_vote(guild_id: int, lobby_id: str, user_id: int, option_id: str) -> str:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None or not lobby.get("vote"):
        return "not_found"
    vote = lobby["vote"]
    if vote.get("applied"):
        return "closed"
    if int(time.time()) >= int(vote.get("ends_at") or 0):
        return "closed"
    uid = str(user_id)
    roster = {p["user_id"] for p in lobby.get("players") or []} | {p["user_id"] for p in lobby.get("subs") or []}
    roster.add(str(lobby.get("host_id")))
    if uid not in roster:
        return "not_member"
    if not any(o["id"] == option_id for o in vote.get("options") or []):
        return "bad_option"
    vote["votes"][uid] = option_id
    save_data(guild_id, data)
    return "ok"


def resolve_vote(guild_id: int, lobby_id: str) -> tuple[dict[str, Any] | None, str | None]:
    """Apply majority vote; ties broken randomly. Returns (lobby, winning_option_id)."""
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None or not lobby.get("vote"):
        return lobby, None
    vote = lobby["vote"]
    if vote.get("applied"):
        return lobby, None
    tallies: dict[str, int] = {}
    for opt_id in vote.get("votes", {}).values():
        tallies[opt_id] = tallies.get(opt_id, 0) + 1
    if not tallies:
        winner = (vote.get("options") or [{"id": None}])[0]["id"]
    else:
        best = max(tallies.values())
        contenders = [oid for oid, n in tallies.items() if n == best]
        winner = random.choice(contenders)
    vote["applied"] = True
    vote["winner"] = winner
    kind = vote.get("kind")
    if kind == "map" and winner:
        info = next((m for m in valorant_maps.MAPS if m["id"] == winner), None)
        lobby["map_id"] = winner
        lobby["map_name"] = info["name"] if info else winner
        data["last_map_id"] = winner
    elif kind == "balance" and winner is not None:
        try:
            idx = int(str(winner).replace("preset_", "") or "0")
        except ValueError:
            idx = 0
        presets = lobby.get("balance_presets") or []
        if 0 <= idx < len(presets):
            chosen = presets[idx]
            lobby["team_a"] = chosen["team_a"]
            lobby["team_b"] = chosen["team_b"]
            lobby["selected_preset"] = idx
    save_data(guild_id, data)
    return lobby, winner


def random_side(guild_id: int, lobby_id: str) -> dict[str, Any] | None:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return None
    lobby["side"] = random.choice(["attack_a", "defense_a"])
    save_data(guild_id, data)
    return lobby


def check_in(guild_id: int, lobby_id: str, user_id: int) -> str:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return "not_found"
    if lobby.get("status") not in (STATUS_CHECKIN, STATUS_READY, STATUS_OPEN):
        return "closed"
    uid = str(user_id)
    found = False
    for p in lobby.get("players") or []:
        if p["user_id"] == uid:
            p["checked_in"] = True
            found = True
            break
    if not found:
        return "not_in"
    checkins = lobby.setdefault("checkins", {})
    checkins[uid] = True
    save_data(guild_id, data)
    return "ok"


def set_result(guild_id: int, lobby_id: str, score_a: int, score_b: int) -> dict[str, Any] | None:
    data = load_data(guild_id)
    lobby = data["lobbies"].get(str(lobby_id))
    if lobby is None:
        return None
    lobby["score"] = {"a": int(score_a), "b": int(score_b)}
    lobby["status"] = STATUS_FINISHED
    lobby["closed_at"] = int(time.time())
    winner = "a" if score_a > score_b else ("b" if score_b > score_a else None)
    for p in lobby.get("team_a") or []:
        _bump_stat(data, p["user_id"], won=(winner == "a"))
    for p in lobby.get("team_b") or []:
        _bump_stat(data, p["user_id"], won=(winner == "b"))
    save_data(guild_id, data)
    return lobby


def cancel_lobby(guild_id: int, lobby_id: str) -> dict[str, Any] | None:
    return update_lobby(
        guild_id,
        lobby_id,
        status=STATUS_CANCELLED,
        closed_at=int(time.time()),
    )


def finish_lobby(guild_id: int, lobby_id: str) -> dict[str, Any] | None:
    """Mark a live lobby finished (no score UI)."""
    lobby = get_lobby(guild_id, lobby_id)
    if lobby is None:
        return None
    if lobby.get("status") not in (STATUS_LIVE, STATUS_READY):
        return lobby
    return update_lobby(
        guild_id,
        lobby_id,
        status=STATUS_FINISHED,
        closed_at=int(time.time()),
    )


def set_lobby_bans(guild_id: int, lobby_id: str, map_ids: list[str]) -> dict[str, Any] | None:
    bans = _normalize_map_id_list(map_ids, limit=MAX_LOBBY_MAP_BANS)
    return update_lobby(guild_id, lobby_id, banned_maps=bans)


def rematch_spec(lobby: dict[str, Any]) -> dict[str, Any]:
    """Settings to publish a new custom from a previous lobby."""
    return {
        "name": str(lobby.get("name") or "Кастомка").strip()[:80] or "Кастомка",
        "notes": str(lobby.get("notes") or "").strip()[:500],
        "join_mode": lobby.get("join_mode") or JOIN_MODE_SOLO,
        "channel_id": str(lobby.get("channel_id") or ""),
        "ping": _normalize_ping(lobby.get("ping")),
        "signup_minutes": int(lobby.get("signup_minutes") or 0),
        "banned_maps": list(lobby.get("banned_maps") or []),
    }


def lobby_voice_ids(lobby: dict[str, Any]) -> set[int]:
    ids: set[int] = set()
    for key in ("lobby_vc_id", "team_a_vc_id", "team_b_vc_id"):
        raw = str(lobby.get(key) or "")
        if raw.isdigit():
            ids.add(int(raw))
    return ids


def score_winner(lobby: dict[str, Any]) -> str | None:
    score = lobby.get("score") if isinstance(lobby.get("score"), dict) else {}
    try:
        a = int(score.get("a") or 0)
        b = int(score.get("b") or 0)
    except (TypeError, ValueError):
        return None
    if a > b:
        return "a"
    if b > a:
        return "b"
    return None


def serialize_schedule(sch: dict[str, Any]) -> dict[str, Any]:
    return dict(sch)


def list_schedules(guild_id: int) -> list[dict[str, Any]]:
    data = load_data(guild_id)
    rows = list(data.get("schedules") or {}).values()
    return sorted(rows, key=lambda s: (int(s.get("weekday") or 0), int(s.get("hour") or 0), int(s.get("minute") or 0)))


def upsert_schedule(guild_id: int, payload: dict[str, Any]) -> dict[str, Any] | None:
    data = load_data(guild_id)
    sid = str(payload.get("id") or "").strip()
    if not sid or sid not in data["schedules"]:
        data["schedule_seq"] = int(data.get("schedule_seq") or 0) + 1
        sid = str(data["schedule_seq"])
    sch = _normalize_schedule({**payload, "id": sid}, sid)
    if sch is None:
        return None
    # Preserve last_run unless caller sets it.
    prev = data["schedules"].get(sid) or {}
    if not payload.get("last_run"):
        sch["last_run"] = str(prev.get("last_run") or "")
    data["schedules"][sid] = sch
    save_data(guild_id, data)
    return sch


def delete_schedule(guild_id: int, schedule_id: str) -> bool:
    data = load_data(guild_id)
    if str(schedule_id) not in data["schedules"]:
        return False
    data["schedules"].pop(str(schedule_id), None)
    save_data(guild_id, data)
    return True


def mark_schedule_run(guild_id: int, schedule_id: str, day_key: str) -> None:
    data = load_data(guild_id)
    sch = data["schedules"].get(str(schedule_id))
    if sch is None:
        return
    sch["last_run"] = str(day_key)
    save_data(guild_id, data)


def due_schedules(guild_id: int, *, now_local=None, window_minutes: int = 10) -> list[dict[str, Any]]:
    """Weekly customs due in guild TZ (within window_minutes after scheduled time, once per day)."""
    import timezone_core

    now = now_local or timezone_core.now_local(guild_id)
    day_key = now.strftime("%Y-%m-%d")
    now_mins = now.hour * 60 + now.minute
    out: list[dict[str, Any]] = []
    for sch in (load_data(guild_id).get("schedules") or {}).values():
        if not sch.get("enabled"):
            continue
        if int(sch.get("weekday") or -1) != now.weekday():
            continue
        scheduled = int(sch.get("hour") or 0) * 60 + int(sch.get("minute") or 0)
        delta = now_mins - scheduled
        if delta < 0 or delta >= max(1, window_minutes):
            continue
        if str(sch.get("last_run") or "") == day_key:
            continue
        out.append(dict(sch))
    return out


def lobby_participant_ids(lobby: dict[str, Any]) -> list[str]:
    """Unique user ids across roster buckets (players, subs, teams)."""
    seen: set[str] = set()
    out: list[str] = []
    for bucket in ("players", "subs", "team_a", "team_b"):
        for p in lobby.get(bucket) or []:
            if not isinstance(p, dict):
                continue
            uid = str(p.get("user_id") or "")
            if uid and uid not in seen:
                seen.add(uid)
                out.append(uid)
    return out


def _bump_stat(data: dict, user_id: str, *, won: bool) -> None:
    row = data["stats"].setdefault(str(user_id), {"wins": 0, "losses": 0, "played": 0})
    row["played"] = int(row.get("played") or 0) + 1
    if won:
        row["wins"] = int(row.get("wins") or 0) + 1
    else:
        row["losses"] = int(row.get("losses") or 0) + 1


def leaderboard(guild_id: int, limit: int = 15) -> list[dict[str, Any]]:
    data = load_data(guild_id)
    rows = []
    for uid, row in data.get("stats", {}).items():
        rows.append(
            {
                "user_id": uid,
                "wins": int(row.get("wins") or 0),
                "losses": int(row.get("losses") or 0),
                "played": int(row.get("played") or 0),
            }
        )
    rows.sort(key=lambda r: (-r["wins"], -r["played"], r["user_id"]))
    return rows[:limit]


def award_xp_winners(guild_id: int, lobby: dict[str, Any]) -> list[str]:
    """Optional XP hook for winning team. Returns awarded user ids."""
    amount = int(get_settings(guild_id).get("xp_on_win") or 0)
    if amount <= 0:
        return []
    score = lobby.get("score") or {}
    if score.get("a", 0) == score.get("b", 0):
        return []
    winners = lobby.get("team_a") if score.get("a", 0) > score.get("b", 0) else lobby.get("team_b")
    awarded: list[str] = []
    try:
        import stats_db
        import xp_core

        now = int(time.time())
        for p in winners or []:
            uid = int(p["user_id"])
            stats_db.xp_add_text(guild_id, uid, amount, now)
            row = stats_db.xp_get_member(guild_id, uid)
            if row:
                level = xp_core.level_from_xp(int(row["xp"]))
                stats_db.xp_set_level(guild_id, uid, level)
            awarded.append(str(uid))
    except Exception:
        return awarded
    return awarded


def validate_create_spec(spec: dict[str, Any]) -> str | None:
    name = str(spec.get("name") or "").strip()
    if not name or len(name) > 80:
        return "invalid_name"
    notes = str(spec.get("notes") or "")
    if len(notes) > 500:
        return "invalid_notes"
    mode = str(spec.get("join_mode") or JOIN_MODE_SOLO)
    if mode not in JOIN_MODES:
        return "invalid_mode"
    channel_id = str(spec.get("channel_id") or "")
    if not channel_id.isdigit():
        return "invalid_channel"
    ping = str(spec.get("ping") or PING_NONE)
    if ping not in PING_MODES:
        return "invalid_ping"
    if "signup_minutes" in spec and spec.get("signup_minutes") is not None:
        try:
            minutes = int(spec.get("signup_minutes") or 0)
        except (TypeError, ValueError):
            return "invalid_signup"
        if minutes < 0 or minutes > 240:
            return "invalid_signup"
    if "banned_maps" in spec and spec.get("banned_maps") is not None:
        if not isinstance(spec.get("banned_maps"), list):
            return "invalid_bans"
        if len(_normalize_map_id_list(spec.get("banned_maps"), limit=MAX_LOBBY_MAP_BANS + 1)) > MAX_LOBBY_MAP_BANS:
            return "invalid_bans"
    return None


def validate_schedule_spec(spec: dict[str, Any]) -> str | None:
    sch = _normalize_schedule(spec if isinstance(spec, dict) else {}, str(spec.get("id") or "0"))
    if sch is None:
        return "invalid_schedule"
    return None
