"""ValChecker pure formulas — port of matches.js / ranks.js / format.js / formStrip.js / statusFormat.js."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

import i18n
import valchecker_valorant_api as vap

REGIONS = ["eu", "na", "ap", "kr", "latam", "br"]
PLATFORM = "pc"

RANK_ORDER = [
    "Unrated",
    "Iron 1", "Iron 2", "Iron 3",
    "Bronze 1", "Bronze 2", "Bronze 3",
    "Silver 1", "Silver 2", "Silver 3",
    "Gold 1", "Gold 2", "Gold 3",
    "Platinum 1", "Platinum 2", "Platinum 3",
    "Diamond 1", "Diamond 2", "Diamond 3",
    "Ascendant 1", "Ascendant 2", "Ascendant 3",
    "Immortal 1", "Immortal 2", "Immortal 3",
    "Radiant",
]

RANK_GROUPS = [
    "Unrated", "Iron", "Bronze", "Silver", "Gold", "Platinum",
    "Diamond", "Ascendant", "Immortal", "Radiant",
]


# ── format ──────────────────────────────────────────────────────────────────

def riot_id(name: str, tag: str) -> str:
    return f"{name}#{tag}"


def parse_riot_id(input_str: str | None) -> dict[str, str] | None:
    if not input_str:
        return None
    cleaned = str(input_str).strip()
    idx = cleaned.rfind("#")
    if idx <= 0 or idx == len(cleaned) - 1:
        return None
    return {"name": cleaned[:idx].strip(), "tag": cleaned[idx + 1 :].strip()}


def kd(k: float, d: float) -> str:
    if not d:
        return f"{k:.2f}" if k else "0.00"
    return f"{k / d:.2f}"


def pct(n, digits: int = 1) -> str:
    if n is None:
        return "—"
    try:
        if n != n:  # NaN
            return "—"
        return f"{float(n):.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def signed(n) -> str:
    if n is None:
        return "—"
    v = float(n)
    if v == int(v):
        v_int = int(v)
        return f"+{v_int}" if v_int > 0 else str(v_int)
    return f"+{v}" if v > 0 else str(v)


def truncate(s: str | None, max_len: int = 1024) -> str:
    if not s:
        return ""
    return f"{s[: max_len - 1]}…" if len(s) > max_len else s


def ago(iso_or_sec, lang: str = "en") -> str:
    if not iso_or_sec:
        return "—"
    if isinstance(iso_or_sec, (int, float)):
        ms = iso_or_sec * 1000 if iso_or_sec < 1e12 else iso_or_sec
    else:
        try:
            ms = datetime.fromisoformat(str(iso_or_sec).replace("Z", "+00:00")).timestamp() * 1000
        except ValueError:
            try:
                ms = time.mktime(time.strptime(str(iso_or_sec)[:19], "%Y-%m-%dT%H:%M:%S")) * 1000
            except ValueError:
                return str(iso_or_sec)
    diff = max(0, time.time() * 1000 - ms)
    m = int(diff // 60000)
    if m < 60:
        return i18n.t("valchecker.time.m_ago", lang, n=m)
    h = m // 60
    if h < 48:
        return i18n.t("valchecker.time.h_ago", lang, n=h)
    d = h // 24
    return i18n.t("valchecker.time.d_ago", lang, n=d)


def mode_label(mode, lang: str = "en") -> str:
    if not mode:
        return i18n.t("valchecker.common.unknown", lang)
    m = str(mode).lower()
    if "competitive" in m or m == "competitive":
        return i18n.t("valchecker.mode.competitive", lang)
    if "unrated" in m:
        return i18n.t("valchecker.mode.unrated", lang)
    if "deathmatch" in m and "team" not in m:
        return i18n.t("valchecker.mode.deathmatch", lang)
    if "spikerush" in m or "spike_rush" in m:
        return i18n.t("valchecker.mode.spike_rush", lang)
    if "swiftplay" in m:
        return i18n.t("valchecker.mode.swiftplay", lang)
    if "premier" in m:
        return i18n.t("valchecker.mode.premier", lang)
    if "replication" in m:
        return i18n.t("valchecker.mode.replication", lang)
    if "teamdeathmatch" in m or "team deathmatch" in m:
        return i18n.t("valchecker.mode.tdm", lang)
    return str(mode)


# ── formStrip ───────────────────────────────────────────────────────────────

def form_strip(summaries, n: int = 5) -> str:
    if not isinstance(summaries, list) or not summaries:
        return "—"
    return "".join(
        "W" if s.get("won") is True else "L" if s.get("won") is False else "?"
        for s in summaries[:n]
    )


def form_strip_spaced(summaries, n: int = 5) -> str:
    if not isinstance(summaries, list) or not summaries:
        return "—"
    return " ".join(
        "W" if s.get("won") is True else "L" if s.get("won") is False else "?"
        for s in summaries[:n]
    )


def form_strip_dots(summaries, n: int = 5) -> str:
    if not isinstance(summaries, list) or not summaries:
        return "—"
    return " ".join(
        "●" if s.get("won") is True else "○" if s.get("won") is False else "◌"
        for s in summaries[:n]
    )


def form_strip_inline(summaries, n: int = 5) -> str | None:
    strip = form_strip_spaced(summaries, n)
    return None if strip == "—" else f"`{strip}`"


# ── ranks ───────────────────────────────────────────────────────────────────

def rank_group(rank_name: str | None) -> str:
    if not rank_name:
        return "Unrated"
    base = str(rank_name).split(" ")[0]
    return base if base in RANK_GROUPS else "Unrated"


def rank_sort_key(rank_name: str | None, rr: float = 0) -> float:
    idx = next(
        (i for i, r in enumerate(RANK_ORDER) if r.lower() == str(rank_name or "").lower()),
        -1,
    )
    return (idx if idx >= 0 else -1) * 1000 + float(rr or 0)


def rank_index(rank_name: str | None) -> int:
    return next(
        (i for i, r in enumerate(RANK_ORDER) if r.lower() == str(rank_name or "").lower()),
        -1,
    )


def rank_change_info(prev_rank, prev_rr, mmr: dict | None) -> dict | None:
    if not mmr:
        return None
    rank = mmr.get("rank") or "Unrated"
    rr = float(mmr.get("rr") or 0)
    if mmr.get("lastChange") is not None:
        delta = float(mmr["lastChange"])
    elif prev_rr is not None:
        delta = rr - float(prev_rr)
    else:
        delta = None

    movement = None
    if prev_rank:
        a = rank_index(prev_rank)
        b = rank_index(rank)
        if a >= 0 and b >= 0 and b > a:
            movement = "promoted"
        elif a >= 0 and b >= 0 and b < a:
            movement = "demoted"

    return {
        "rank": rank,
        "rr": rr,
        "delta": delta,
        "prevRank": prev_rank or None,
        "prevRr": float(prev_rr) if prev_rr is not None else None,
        "movement": movement,
    }


def normalize_mmr(mmr_body) -> dict:
    data = mmr_body.get("data") if isinstance(mmr_body, dict) and "data" in mmr_body else mmr_body
    if not data or not isinstance(data, dict):
        return {
            "account": None,
            "peak": None,
            "rank": "Unrated",
            "tier": 0,
            "rr": 0,
            "elo": None,
            "lastChange": None,
            "gamesNeeded": None,
            "seasonal": [],
            "raw": data,
        }

    current = data.get("current") or {}
    tier = current.get("tier") or {}
    peak = data.get("peak")

    peak_info = None
    if peak:
        peak_tier = peak.get("tier") or {}
        peak_season = peak.get("season") or {}
        peak_info = {
            "name": peak_tier.get("name") or "Unknown",
            "tier": peak_tier.get("id") if peak_tier.get("id") is not None else 0,
            "rr": peak.get("rr") if peak.get("rr") is not None else 0,
            "season": peak_season.get("short") or peak_season.get("id"),
        }

    return {
        "account": data.get("account"),
        "peak": peak_info,
        "rank": tier.get("name") or "Unrated",
        "tier": int(tier.get("id") or 0),
        "rr": float(current.get("rr") or 0),
        "elo": current.get("elo"),
        "lastChange": current.get("last_change"),
        "gamesNeeded": current.get("games_needed_for_rating"),
        "leaderboard": current.get("leaderboard_placement"),
        "seasonal": data.get("seasonal") if isinstance(data.get("seasonal"), list) else [],
        "raw": data,
    }


# ── matches ─────────────────────────────────────────────────────────────────

def _parse_started(meta: dict) -> float:
    raw = meta.get("started_at") or 0
    if isinstance(raw, (int, float)):
        return float(raw) if raw > 1e12 else float(raw) * 1000
    try:
        return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp() * 1000
    except ValueError:
        return 0.0


def pick_latest_match(matches, *, allow_incomplete: bool = False):
    lst = list(matches) if isinstance(matches, list) else []
    if not lst:
        return None

    scored = []
    for index, m in enumerate(lst):
        meta = (m or {}).get("metadata") or {}
        started = _parse_started(meta)
        completed = meta.get("is_completed") is not False
        scored.append({"m": m, "index": index, "started": started, "completed": completed})

    scored.sort(key=lambda a: (0 if a["completed"] else 1, -a["started"], a["index"]))

    if not allow_incomplete:
        for x in scored:
            if x["completed"]:
                return x["m"]
    return scored[0]["m"] if scored else None


def find_player(match, puuid, name=None, tag=None):
    players = (match or {}).get("players") or []
    if puuid:
        for p in players:
            if p.get("puuid") == puuid:
                return p
    if name and tag:
        nl, tl = name.lower(), tag.lower()
        for p in players:
            if (p.get("name") or "").lower() == nl and (p.get("tag") or "").lower() == tl:
                return p
    return None


def team_for_player(match, player):
    if not player:
        return None
    for t in (match or {}).get("teams") or []:
        if t.get("team_id") == player.get("team_id"):
            return t
    return None


def scoreline(match) -> str:
    teams = (match or {}).get("teams") or []
    if len(teams) < 2:
        return "—"
    a, b = teams[0], teams[1]
    ar = (a.get("rounds") or {}).get("won") if isinstance(a.get("rounds"), dict) else a.get("rounds")
    br = (b.get("rounds") or {}).get("won") if isinstance(b.get("rounds"), dict) else b.get("rounds")
    if ar is None:
        ar = "?"
    if br is None:
        br = "?"
    if isinstance(ar, dict):
        ar = ar.get("won", "?")
    if isinstance(br, dict):
        br = br.get("won", "?")
    return f"{ar}-{br}"


def summarize_match(match, puuid, name=None, tag=None) -> dict:
    meta = (match or {}).get("metadata") or {}
    player = find_player(match, puuid, name, tag)
    team = team_for_player(match, player)
    stats = (player or {}).get("stats") or {}
    map_obj = meta.get("map")
    map_name = (map_obj.get("name") if isinstance(map_obj, dict) else map_obj) or "Unknown"
    map_id = map_obj.get("id") if isinstance(map_obj, dict) else None
    map_asset = vap.map_by_path_or_name(map_name) or vap.map_by_path_or_name(map_id)

    agent_obj = (player or {}).get("agent") or {}
    agent_name = agent_obj.get("name") or "Unknown"
    agent_asset = vap.agent_by_uuid(agent_obj.get("id")) or vap.agent_by_name(agent_name)

    kills = stats.get("kills") or 0
    deaths = stats.get("deaths") or 0
    assists = stats.get("assists") or 0
    score = stats.get("score") or 0
    headshots = stats.get("headshots") or 0
    bodyshots = stats.get("bodyshots") or 0
    legshots = stats.get("legshots") or 0
    shots = headshots + bodyshots + legshots
    hs_pct = (headshots / shots) * 100 if shots else 0.0

    rounds_played = len((match or {}).get("rounds") or []) or 1
    acs = score / rounds_played

    queue = meta.get("queue") or {}
    season = meta.get("season") or {}

    damage = stats.get("damage")
    if isinstance(damage, dict):
        damage_val = damage.get("dealt")
    else:
        damage_val = damage

    player_out = None
    if player:
        tier = player.get("tier") or {}
        player_out = {
            "puuid": player.get("puuid"),
            "name": player.get("name"),
            "tag": player.get("tag"),
            "agent": agent_name,
            "agentIcon": (agent_asset or {}).get("displayIcon"),
            "tier": tier.get("name") if isinstance(tier, dict) else None,
            "kills": kills,
            "deaths": deaths,
            "assists": assists,
            "score": score,
            "acs": acs,
            "hsPct": hs_pct,
            "damage": damage_val,
        }

    return {
        "matchId": meta.get("match_id"),
        "map": map_name,
        "mapImage": (map_asset or {}).get("splash") or (map_asset or {}).get("listViewIcon"),
        "mode": mode_label(queue.get("name") or queue.get("id") or queue.get("mode_type")),
        "queueId": queue.get("id"),
        "startedAt": meta.get("started_at"),
        "season": season.get("short"),
        "region": meta.get("region"),
        "scoreline": scoreline(match),
        "won": team.get("won") if team else None,
        "player": player_out,
        "raw": match,
    }


def bucket_wr(bucket: dict | None) -> float:
    wins = (bucket or {}).get("wins") or 0
    losses = (bucket or {}).get("losses") or 0
    decided = wins + losses
    return (wins / decided) * 100 if decided else 0.0


def sort_summaries_newest_first(summaries):
    def key(a):
        raw = (a or {}).get("startedAt") or 0
        if isinstance(raw, (int, float)):
            return float(raw) if raw > 1e12 else float(raw) * 1000
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp() * 1000
        except ValueError:
            return 0.0

    return sorted(summaries or [], key=key, reverse=True)


def summaries_from_matches(matches, puuid, name=None, tag=None):
    return sort_summaries_newest_first(
        [summarize_match(m, puuid, name, tag) for m in (matches or [])]
    )


def aggregate_stats(summaries) -> dict:
    n = len(summaries or [])
    if not n:
        return {
            "games": 0, "wins": 0, "losses": 0, "wr": 0, "kd": 0, "avgAcs": 0, "avgHs": 0,
            "kills": 0, "deaths": 0, "assists": 0, "agents": {}, "maps": {},
        }

    wins = losses = kills = deaths = assists = 0
    acs = hs = 0.0
    agents: dict[str, dict] = {}
    maps: dict[str, dict] = {}

    for s in summaries:
        if s.get("won") is True:
            wins += 1
        elif s.get("won") is False:
            losses += 1

        p = s.get("player")
        if not p:
            continue
        kills += p["kills"]
        deaths += p["deaths"]
        assists += p["assists"]
        acs += p["acs"]
        hs += p["hsPct"]

        agents.setdefault(p["agent"], {"games": 0, "wins": 0, "losses": 0, "kills": 0, "deaths": 0, "acs": 0})
        agents[p["agent"]]["games"] += 1
        if s.get("won") is True:
            agents[p["agent"]]["wins"] += 1
        elif s.get("won") is False:
            agents[p["agent"]]["losses"] += 1
        agents[p["agent"]]["kills"] += p["kills"]
        agents[p["agent"]]["deaths"] += p["deaths"]
        agents[p["agent"]]["acs"] += p["acs"]

        maps.setdefault(s["map"], {"games": 0, "wins": 0, "losses": 0, "kills": 0, "deaths": 0, "acs": 0})
        maps[s["map"]]["games"] += 1
        if s.get("won") is True:
            maps[s["map"]]["wins"] += 1
        elif s.get("won") is False:
            maps[s["map"]]["losses"] += 1
        maps[s["map"]]["kills"] += p["kills"]
        maps[s["map"]]["deaths"] += p["deaths"]
        maps[s["map"]]["acs"] += p["acs"]

    decided = wins + losses
    return {
        "games": n,
        "wins": wins,
        "losses": losses,
        "wr": (wins / decided) * 100 if decided else 0,
        "kd": (kills / deaths) if deaths else kills,
        "avgAcs": acs / n,
        "avgHs": hs / n,
        "kills": kills,
        "deaths": deaths,
        "assists": assists,
        "agents": agents,
        "maps": maps,
    }


def to_cache_row(summary: dict, region=None) -> dict | None:
    p = summary.get("player")
    if not p:
        return None
    return {
        "match_id": summary.get("matchId"),
        "puuid": p["puuid"],
        "region": region or summary.get("region"),
        "map": summary.get("map"),
        "mode": summary.get("mode"),
        "agent": p["agent"],
        "kills": p["kills"],
        "deaths": p["deaths"],
        "assists": p["assists"],
        "acs": p["acs"],
        "hs_pct": p["hsPct"],
        "won": (None if summary.get("won") is None else (1 if summary.get("won") else 0)),
        "rr_change": None,
        "played_at": summary.get("startedAt"),
        "raw_json": None,
    }


# ── statusFormat ────────────────────────────────────────────────────────────

def _riot_locales(bot_locale: str) -> list[str]:
    return (
        ["ru_RU", "en_US", "en_GB", "en_SG"]
        if bot_locale == "ru"
        else ["en_US", "en_GB", "en_SG", "ru_RU"]
    )


def pick_locale(entries, bot_locale: str = "en") -> str | None:
    if not isinstance(entries, list) or not entries:
        return None
    for loc in _riot_locales(bot_locale):
        for e in entries:
            if e and e.get("locale") == loc and e.get("content"):
                return str(e["content"]).strip()
    for e in entries:
        if e and e.get("content"):
            return str(e["content"]).strip()
    return None


def issue_title(issue, bot_locale: str = "en") -> str:
    return (
        pick_locale((issue or {}).get("titles"), bot_locale)
        or (issue or {}).get("name")
        or (issue or {}).get("description")
        or i18n.t("valchecker.status.untitled", bot_locale)
    )


def latest_update(issue):
    updates = list((issue or {}).get("updates") or [])
    if not updates:
        return None

    def _ts(u):
        raw = u.get("updated_at") or u.get("created_at") or 0
        try:
            return datetime.fromisoformat(str(raw).replace("Z", "+00:00")).timestamp()
        except ValueError:
            return 0.0

    updates.sort(key=_ts)
    return updates[-1]


def issue_update(issue, bot_locale: str = "en") -> str | None:
    latest = latest_update(issue)
    if not latest:
        return None
    return (
        pick_locale(latest.get("translations"), bot_locale)
        or latest.get("content")
        or latest.get("description")
    )


def issue_severity(issue) -> str:
    return str(
        (issue or {}).get("incident_severity")
        or (issue or {}).get("maintenance_status")
        or "info"
    ).lower()


def issue_fingerprint(issue) -> str:
    latest = latest_update(issue)
    return "|".join([
        str((issue or {}).get("id") or ""),
        issue_severity(issue),
        str((latest or {}).get("id") or ""),
        issue_update(issue, "en") or "",
    ])


def issue_key(issue, kind: str = "incident") -> str:
    return f"{kind}:{(issue or {}).get('id') or issue_fingerprint(issue)}"


def build_fingerprint_map(items) -> dict:
    out = {}
    for entry in items or []:
        out[issue_key(entry["issue"], entry["kind"])] = issue_fingerprint(entry["issue"])
    return out


def diff_status_items(items, prev_fingerprints=None):
    prev = prev_fingerprints or {}
    next_fp = build_fingerprint_map(items)
    added = []
    updated = []
    for entry in items or []:
        key = issue_key(entry["issue"], entry["kind"])
        if key not in prev:
            added.append(entry)
        elif prev[key] != next_fp[key]:
            updated.append(entry)
    resolved_all = len(prev) > 0 and len(items or []) == 0
    return {
        "added": added,
        "updated": updated,
        "resolvedAll": resolved_all,
        "nextFingerprints": next_fp,
    }


def format_issue_line(issue, *, detail: bool = True, lang: str = "en") -> str:
    title = issue_title(issue, lang)
    sev = issue_severity(issue)
    update = issue_update(issue, lang) if detail else None
    head = f"**{title}** · {sev}"
    if not update or update == title:
        return head
    short = f"{update[:157]}…" if len(update) > 160 else update
    return f"{head}\n{short}"


def summarize_status(data, *, limit: int = 5, lang: str = "en") -> dict:
    maintenances = (data or {}).get("maintenances") or []
    incidents = (data or {}).get("incidents") or []
    items = (
        [{"kind": "maintenance", "issue": m} for m in maintenances]
        + [{"kind": "incident", "issue": i} for i in incidents]
    )
    shown = items[:limit]
    lines = []
    for entry in shown:
        label = i18n.t(
            "valchecker.status.maintenance" if entry["kind"] == "maintenance" else "valchecker.status.incident",
            lang,
        )
        lines.append(f"**{label}** · {format_issue_line(entry['issue'], lang=lang)}")
    remaining = len(items) - len(shown)
    if remaining > 0:
        lines.append(f"_{i18n.t('valchecker.common.more', lang, n=remaining)}_")
    return {
        "down": len(items) > 0,
        "summary": "\n\n".join(lines) or i18n.t("valchecker.status.no_issues", lang),
        "maintenanceCount": len(maintenances),
        "incidentCount": len(incidents),
        "items": items,
    }


def format_issue_list(issues, lang: str = "en", limit: int = 5) -> str:
    if not issues:
        return i18n.t("valchecker.status.none_reported", lang)
    lines = [format_issue_line(issue, lang=lang) for issue in issues[:limit]]
    more = len(issues) - min(len(issues), limit)
    if more > 0:
        lines.append(f"_{i18n.t('valchecker.common.more', lang, n=more)}_")
    return "\n\n".join(lines)


def format_delta(entries, lang: str = "en", limit: int = 5) -> str:
    lines = []
    for entry in entries[:limit]:
        label = i18n.t(
            "valchecker.status.maintenance" if entry["kind"] == "maintenance" else "valchecker.status.incident",
            lang,
        )
        lines.append(f"**{label}** · {format_issue_line(entry['issue'], lang=lang)}")
    more = len(entries) - min(len(entries), limit)
    if more > 0:
        lines.append(f"_{i18n.t('valchecker.common.more', lang, n=more)}_")
    return "\n\n".join(lines)


# ── session store (30m TTL) ─────────────────────────────────────────────────

_SESSION_STORE: dict[str, dict] = {}
_SESSION_TTL_MS = 1000 * 60 * 30


def _session_sweep() -> None:
    now = time.time() * 1000
    expired = [sid for sid, e in _SESSION_STORE.items() if now - e["at"] > _SESSION_TTL_MS]
    for sid in expired:
        _SESSION_STORE.pop(sid, None)


def create_session(data: dict) -> str:
    import secrets
    _session_sweep()
    sid = secrets.token_hex(4)
    _SESSION_STORE[sid] = {**data, "at": time.time() * 1000}
    return sid


def get_session(sid: str) -> dict | None:
    entry = _SESSION_STORE.get(sid)
    if not entry:
        return None
    if time.time() * 1000 - entry["at"] > _SESSION_TTL_MS:
        _SESSION_STORE.pop(sid, None)
        return None
    entry["at"] = time.time() * 1000
    return entry


def update_session(sid: str, patch: dict) -> dict | None:
    entry = get_session(sid)
    if not entry:
        return None
    entry.update(patch)
    entry["at"] = time.time() * 1000
    _SESSION_STORE[sid] = entry
    return entry
