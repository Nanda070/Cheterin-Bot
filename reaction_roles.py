import json
import os

CONFIG_FILE = "reaction_roles.json"


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_pairs_for_message(message_id: str) -> list | None:
    config = load_config()
    entry = config.get(str(message_id))
    return entry["pairs"] if entry else None


def find_pair_by_emoji(pairs: list, emoji_str: str) -> dict | None:
    for pair in pairs:
        if pair["emoji"] == emoji_str:
            return pair
    return None


def has_duplicate_emoji(pairs: list) -> bool:
    emojis = [p["emoji"] for p in pairs]
    return len(emojis) != len(set(emojis))
