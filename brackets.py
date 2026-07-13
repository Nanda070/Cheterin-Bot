import json
import os
import uuid
from datetime import datetime, timezone

BRACKETS_FILE = "brackets_data.json"


def load_brackets() -> dict:
    if os.path.exists(BRACKETS_FILE):
        with open(BRACKETS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_brackets(data: dict) -> None:
    with open(BRACKETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def extract_entries_from_event(ev: dict, guild) -> list[str]:
    mode = ev.get("mode", "solo")
    participants = ev.get("participants", [])

    if mode == "solo":
        entries = []
        for p in participants:
            ign = p.get("ign")
            if ign:
                entries.append(ign)
                continue
            member = guild.get_member(p["user_id"]) if guild else None
            entries.append(member.display_name if member else f"User {p['user_id']}")
        return entries

    if mode == "team_captain":
        return [p.get("team_name", "") for p in participants]

    teams: dict = {}
    for p in participants:
        teams.setdefault(p.get("team_code"), []).append(p)
    result = []
    for members in teams.values():
        captain = next((m for m in members if m.get("is_captain")), members[0] if members else None)
        result.append(captain.get("team_name", "") if captain else "")
    return result


def _next_power_of_two(n: int) -> int:
    power = 1
    while power < n:
        power *= 2
    return power


def _seed_order(size: int) -> list[int]:
    """Standard recursive bracket-seeding order: guarantees a bye (a seed
    number beyond the real entry count) is always paired against a real
    entry in round 1, never against another bye. This is the same
    algorithm used by every real single-elimination bracket tool."""
    order = [1]
    while len(order) < size:
        next_size = len(order) * 2
        new_order = []
        for seed in order:
            new_order.append(seed)
            new_order.append(next_size + 1 - seed)
        order = new_order
    return order


def _match_winner_entry(match: dict) -> str | None:
    if match["winner"] == "a":
        return match["slot_a"]
    if match["winner"] == "b":
        return match["slot_b"]
    return None


def generate_rounds(entries: list[str]) -> list[list[dict]]:
    n = len(entries)
    size = _next_power_of_two(n)
    order = _seed_order(size)
    slots = [entries[seed - 1] if seed <= n else None for seed in order]

    num_rounds = size.bit_length() - 1
    rounds = []

    round1 = []
    for i in range(0, size, 2):
        slot_a, slot_b = slots[i], slots[i + 1]
        match = {"slot_a": slot_a, "slot_b": slot_b, "winner": None}
        if slot_a is not None and slot_b is None:
            match["winner"] = "a"
        elif slot_a is None and slot_b is not None:
            match["winner"] = "b"
        round1.append(match)
    rounds.append(round1)

    prev_round = round1
    for _ in range(1, num_rounds):
        this_round = []
        for i in range(0, len(prev_round), 2):
            slot_a = _match_winner_entry(prev_round[i])
            slot_b = _match_winner_entry(prev_round[i + 1])
            this_round.append({"slot_a": slot_a, "slot_b": slot_b, "winner": None})
        rounds.append(this_round)
        prev_round = this_round

    return rounds


def create_bracket(title: str, entries: list[str], source_event_id: str | None, created_by: int) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "title": title,
        "source_event_id": source_event_id,
        "entries": entries,
        "rounds": generate_rounds(entries),
        "created_by": str(created_by),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "share_token": None,
    }


def set_winner(bracket: dict, round_index: int, match_index: int, winner: str) -> None:
    match = bracket["rounds"][round_index][match_index]
    match["winner"] = winner
    entry = match["slot_a"] if winner == "a" else match["slot_b"]
    _propagate(bracket, round_index, match_index, entry)


def _propagate(bracket: dict, round_index: int, match_index: int, entry) -> None:
    rounds = bracket["rounds"]
    next_round_index = round_index + 1
    if next_round_index >= len(rounds):
        return
    next_match_index = match_index // 2
    slot_key = "slot_a" if match_index % 2 == 0 else "slot_b"
    next_match = rounds[next_round_index][next_match_index]
    next_match[slot_key] = entry
    if next_match["winner"] is not None:
        next_match["winner"] = None
        _propagate(bracket, next_round_index, next_match_index, None)


# ────────────────────────── Форматы: DE и Round Robin ──────────────────────────
#
# Single Elimination хранится по-старому (rounds) для обратной совместимости.
# Double Elimination использует модель «источников»: каждый слот матча знает,
# откуда он берётся (посев, победитель или проигравший другого матча), а
# recompute_de() пересчитывает всю сетку после каждого изменения результата.

FORMAT_SINGLE = "single_elim"
FORMAT_DOUBLE = "double_elim"
FORMAT_ROUND_ROBIN = "round_robin"

FORMATS = (FORMAT_SINGLE, FORMAT_DOUBLE, FORMAT_ROUND_ROBIN)


def _de_match(src_a: str, src_b: str) -> dict:
    return {
        "src_a": src_a, "src_b": src_b,
        "slot_a": None, "slot_b": None,
        "winner": None, "auto": False, "void": False,
    }


def generate_de(entries: list[str]) -> dict:
    n = len(entries)
    size = _next_power_of_two(n)
    order = _seed_order(size)
    seeds = [entries[s - 1] if s <= n else None for s in order]
    k = size.bit_length() - 1  # число раундов верхней сетки

    winners: list[list[dict]] = []
    round1 = [_de_match(f"seed:{i}", f"seed:{i + 1}") for i in range(0, size, 2)]
    winners.append(round1)
    for r in range(1, k):
        count = size // (2 ** (r + 1))
        winners.append([
            _de_match(f"w:W:{r - 1}:{2 * i}", f"w:W:{r - 1}:{2 * i + 1}")
            for i in range(count)
        ])

    losers: list[list[dict]] = []
    if k >= 2:
        # Минорный раунд 0: проигравшие первого раунда верхней сетки
        count = size // 4
        losers.append([
            _de_match(f"l:W:0:{2 * i}", f"l:W:0:{2 * i + 1}")
            for i in range(count)
        ])
        for r in range(1, k):
            # Мажорный раунд: выжившие нижней сетки против проигравших WB r
            count = size // (2 ** (r + 1))
            major = []
            for i in range(count):
                major.append(_de_match(f"w:L:{len(losers) - 1}:{i}", f"l:W:{r}:{count - 1 - i}"))
            losers.append(major)
            # Минорный раунд между мажорными (кроме последнего)
            if r <= k - 2:
                count2 = size // (2 ** (r + 2))
                losers.append([
                    _de_match(f"w:L:{len(losers) - 1}:{2 * i}", f"w:L:{len(losers) - 1}:{2 * i + 1}")
                    for i in range(count2)
                ])

    final_src_b = f"w:L:{len(losers) - 1}:0" if losers else "l:W:0:0"
    final = _de_match(f"w:W:{k - 1}:0", final_src_b)

    de = {"seeds": seeds, "winners": winners, "losers": losers, "final": final}
    recompute_de(de)
    return de


def _de_get_match(de: dict, segment: str, round_index: int, match_index: int) -> dict | None:
    if segment == "F":
        return de["final"]
    rounds = de["winners"] if segment == "W" else de["losers"]
    if 0 <= round_index < len(rounds) and 0 <= match_index < len(rounds[round_index]):
        return rounds[round_index][match_index]
    return None


def _de_resolve(de: dict, src: str) -> tuple:
    """(значение, определено ли). Значение None при «определено» = bye."""
    kind, rest = src.split(":", 1)
    if kind == "seed":
        return de["seeds"][int(rest)], True

    seg, r, m = rest.split(":")
    match = _de_get_match(de, seg, int(r), int(m))
    if match is None:
        return None, True
    if match.get("void"):
        return None, True
    if match["winner"] not in ("a", "b"):
        return None, False
    win_val = match["slot_a"] if match["winner"] == "a" else match["slot_b"]
    lose_val = match["slot_b"] if match["winner"] == "a" else match["slot_a"]
    return (win_val, True) if kind == "w" else (lose_val, True)


def _de_recompute_match(de: dict, match: dict) -> None:
    va, ra = _de_resolve(de, match["src_a"])
    vb, rb = _de_resolve(de, match["src_b"])

    slots_changed = match["slot_a"] != va or match["slot_b"] != vb
    match["slot_a"], match["slot_b"] = va, vb

    if slots_changed and not match["auto"]:
        match["winner"] = None
    if slots_changed and match["auto"]:
        match["winner"], match["auto"] = None, False
    match["void"] = False

    if match["winner"] is None and ra and rb:
        if va is not None and vb is None:
            match["winner"], match["auto"] = "a", True
        elif vb is not None and va is None:
            match["winner"], match["auto"] = "b", True
        elif va is None and vb is None:
            match["void"] = True


def recompute_de(de: dict) -> None:
    for rnd in de["winners"]:
        for match in rnd:
            _de_recompute_match(de, match)
    for rnd in de["losers"]:
        for match in rnd:
            _de_recompute_match(de, match)
    _de_recompute_match(de, de["final"])


def set_winner_de(bracket: dict, segment: str, round_index: int, match_index: int, winner: str) -> bool:
    de = bracket["de"]
    match = _de_get_match(de, segment, round_index, match_index)
    if match is None or match["slot_a"] is None or match["slot_b"] is None:
        return False
    match["winner"] = winner
    match["auto"] = False
    recompute_de(de)
    return True


# ────────────────────────── Round Robin ──────────────────────────

def generate_rr_rounds(entries: list[str]) -> list[list[dict]]:
    """Круговая система (метод вращения). При нечётном числе участников
    каждый по разу пропускает тур."""
    indexes: list[int | None] = list(range(len(entries)))
    if len(indexes) % 2:
        indexes.append(None)
    n = len(indexes)

    rounds = []
    arr = indexes[:]
    for _ in range(n - 1):
        matches = []
        for i in range(n // 2):
            a, b = arr[i], arr[n - 1 - i]
            if a is not None and b is not None:
                matches.append({"slot_a": entries[a], "slot_b": entries[b], "winner": None})
        rounds.append(matches)
        arr = [arr[0], arr[-1]] + arr[1:-1]
    return rounds


def set_winner_rr(bracket: dict, round_index: int, match_index: int, winner: str | None) -> bool:
    rounds = bracket.get("rr_rounds", [])
    if not (0 <= round_index < len(rounds) and 0 <= match_index < len(rounds[round_index])):
        return False
    rounds[round_index][match_index]["winner"] = winner
    return True


def rr_standings(bracket: dict) -> list[dict]:
    """Таблица: победа 3 очка, ничья 1, поражение 0."""
    table = {
        entry: {"entry": entry, "played": 0, "wins": 0, "draws": 0, "losses": 0, "points": 0}
        for entry in bracket.get("entries", [])
    }
    for rnd in bracket.get("rr_rounds", []):
        for match in rnd:
            result = match.get("winner")
            if result not in ("a", "b", "draw"):
                continue
            a, b = table.get(match["slot_a"]), table.get(match["slot_b"])
            if a is None or b is None:
                continue
            a["played"] += 1
            b["played"] += 1
            if result == "draw":
                a["draws"] += 1; b["draws"] += 1
                a["points"] += 1; b["points"] += 1
            elif result == "a":
                a["wins"] += 1; b["losses"] += 1
                a["points"] += 3
            else:
                b["wins"] += 1; a["losses"] += 1
                b["points"] += 3
    return sorted(table.values(), key=lambda row: (-row["points"], -row["wins"], row["entry"].lower()))


# ────────────────────────── Создание с форматом ──────────────────────────

def create_bracket_v2(title: str, entries: list[str], source_event_id: str | None, created_by: int, bracket_format: str) -> dict:
    bracket = {
        "id": str(uuid.uuid4()),
        "title": title,
        "format": bracket_format,
        "source_event_id": source_event_id,
        "entries": entries,
        "created_by": str(created_by),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "share_token": None,
    }
    if bracket_format == FORMAT_DOUBLE:
        bracket["de"] = generate_de(entries)
        bracket["rounds"] = []
    elif bracket_format == FORMAT_ROUND_ROBIN:
        bracket["rr_rounds"] = generate_rr_rounds(entries)
        bracket["rounds"] = []
    else:
        bracket["rounds"] = generate_rounds(entries)
    return bracket
