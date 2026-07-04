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
