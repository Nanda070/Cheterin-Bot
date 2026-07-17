"""Ядро игры «Бункер»: конфигурация, генерация персонажей, подсчёт голосов, условие конца игры.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и mafia_core.py).
Карточные пулы лежат в bunker_data.py; здесь только логика их выбора и раздачи.
"""

import json
import os
import random

import bunker_data

CONFIG_FILE = "bunker_config.json"

PLAYERS_FLOOR = 4
PLAYERS_CEIL = 20

DEFAULT_MIN_PLAYERS = 4
DEFAULT_MAX_PLAYERS = 12
DEFAULT_DISCUSSION_TIMER_SEC = 180
DEFAULT_VOTE_TIMER_SEC = 90
DEFAULT_UNIQUE_CARDS = True

# Порядок и подписи раскрываемых характеристик персонажа (спец. возможности сюда не входят —
# они не «раскрываются», а разыгрываются отдельно через заявку игрока).
FIELD_KEYS = (
    "profession", "age", "gender", "body_type", "health",
    "hobby", "phobia", "backpack_item", "large_item", "trait", "additional_info",
)

_cache: dict | None = None
_cache_mtime: float | None = None


def load_config() -> dict:
    global _cache, _cache_mtime
    if not os.path.exists(CONFIG_FILE):
        _cache, _cache_mtime = None, None
        return {}

    mtime = os.path.getmtime(CONFIG_FILE)
    if _cache is not None and _cache_mtime == mtime:
        return _cache

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    _cache, _cache_mtime = data, mtime
    return data


def save_config(data: dict) -> None:
    global _cache, _cache_mtime
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    _cache = data
    _cache_mtime = os.path.getmtime(CONFIG_FILE)


def get_settings() -> dict:
    """Настройки модуля с дефолтами (выключен по умолчанию)."""
    data = load_config()
    return {
        "enabled": bool(data.get("enabled", False)),
        "default_min_players": int(data.get("default_min_players", DEFAULT_MIN_PLAYERS)),
        "default_max_players": int(data.get("default_max_players", DEFAULT_MAX_PLAYERS)),
        "default_discussion_timer_sec": int(data.get("default_discussion_timer_sec", DEFAULT_DISCUSSION_TIMER_SEC)),
        "default_vote_timer_sec": int(data.get("default_vote_timer_sec", DEFAULT_VOTE_TIMER_SEC)),
        "default_unique_cards": bool(data.get("default_unique_cards", DEFAULT_UNIQUE_CARDS)),
        "log_channel_id": str(data.get("log_channel_id") or ""),
    }


def has_moderator_access(member) -> bool:
    permissions = getattr(member, "guild_permissions", None)
    if permissions is None:
        return False
    return bool(permissions.manage_guild or permissions.administrator)


def default_bunker_capacity(player_count: int) -> int:
    """Половина игроков (округление вниз, минимум 1) — если ведущий не задал своё число."""
    return max(1, player_count // 2)


# ────────────────────────── Генерация персонажей ──────────────────────────

class _Deck:
    """Тянет карточки из пула: без повторов (колода тасуется один раз на игру и тянется без
    возврата) либо с повторами (обычный случайный выбор каждый раз). Используется только для
    характеристик, которые в настольной версии — отдельная физическая колода карт (профессия,
    хобби, конкретная болезнь/фобия, инвентарь, характер, доп. сведения, спец. возможности).
    Возраст/пол/телосложение — это бросок кубика по немногочисленным категориям, а не карта,
    поэтому для них всегда используется выбор с повторами независимо от режима."""

    def __init__(self, pool: list[dict], unique: bool):
        self._pool = pool
        self._unique = unique
        self._shuffled = None
        if unique:
            self._shuffled = list(pool)
            random.shuffle(self._shuffled)

    def draw(self) -> dict:
        if self._unique:
            return self._shuffled.pop()
        return random.choice(self._pool)

    def draw_many(self, count: int) -> list[dict]:
        if self._unique:
            drawn = self._shuffled[-count:]
            del self._shuffled[-count:]
            return drawn
        return random.sample(self._pool, count)


def _pick_profession(deck: _Deck) -> dict:
    profession = deck.draw()
    level = random.choice(bunker_data.PROFESSION_EXPERIENCE_LEVELS)
    return {
        "name": profession["name"],
        "category": profession["category"],
        "experience_level": level["level"],
        "has_ability": level["has_ability"],
    }


def _pick_hobby(deck: _Deck) -> dict:
    hobby = deck.draw()
    level = random.choice(bunker_data.HOBBY_EXPERIENCE_LEVELS)
    return {
        "name": hobby["name"],
        "category": hobby["category"],
        "experience_level": level["level"],
    }


def _pick_health(disease_deck: _Deck) -> dict:
    severity = random.choice(bunker_data.HEALTH_SEVERITIES)
    if severity == "Здоров":
        return {"severity": severity, "disease_name": None, "category": None}
    disease = disease_deck.draw()
    return {"severity": severity, "disease_name": disease["name"], "category": disease["category"]}


def _pick_phobia(deck: _Deck) -> dict:
    phobia = deck.draw()
    return {"name": phobia["name"], "type": phobia["type"]}


def _pick_age() -> dict:
    age = random.choice(bunker_data.AGE_CATEGORIES)
    return {"key": age["key"], "label": age["label"]}


def _pick_body_type() -> dict:
    return dict(random.choice(bunker_data.BODY_TYPES))


def _pick_backpack_item(deck: _Deck) -> dict:
    item = deck.draw()
    return {"name": item["name"], "category": item["category"]}


def _pick_large_item(deck: _Deck) -> dict:
    item = deck.draw()
    return {"name": item["name"], "category": item["category"]}


def _pick_trait(deck: _Deck) -> dict:
    return dict(deck.draw())


def _pick_additional_info(deck: _Deck, other_player_ids: list[int], display_names: dict[int, str]) -> dict:
    info = deck.draw()
    name = info["name"]
    linked_user_id = None
    if info["category"] == "Активные (Отношения)" and other_player_ids:
        linked_user_id = random.choice(other_player_ids)
        target_name = display_names.get(linked_user_id, str(linked_user_id))
        name = name.replace("Игрок №X", target_name).replace("игрока №X", target_name)
    return {"name": name, "category": info["category"], "linked_user_id": linked_user_id}


def _pick_special_abilities(deck: _Deck) -> list[dict]:
    cards = deck.draw_many(2)
    return [{"name": c["name"], "category": c["category"], "effect": c["effect"], "used": False} for c in cards]


def generate_characters(
    player_ids: list[int], display_names: dict[int, str], unique_cards: bool = True,
) -> dict[int, dict]:
    """Раздаёт полную карточку персонажа каждому игроку.

    unique_cards=True (по умолчанию) — карточные характеристики раздаются без повторов в рамках
    одной игры, как колодой в настольной версии. unique_cards=False — с повторами (два игрока
    могут получить одинаковую профессию/хобби/спец.возможность и т.д.).

    Карты «Активные (Отношения)» в доп. сведениях привязываются к случайному другому игроку из
    этой же игры независимо от режима раздачи.
    """
    profession_deck = _Deck(bunker_data.PROFESSIONS, unique_cards)
    hobby_deck = _Deck(bunker_data.HOBBIES, unique_cards)
    disease_deck = _Deck(bunker_data.HEALTH_DISEASES, unique_cards)
    phobia_deck = _Deck(bunker_data.PHOBIAS, unique_cards)
    backpack_deck = _Deck(bunker_data.BACKPACK_ITEMS, unique_cards)
    large_item_deck = _Deck(bunker_data.LARGE_INVENTORY_ITEMS, unique_cards)
    trait_deck = _Deck(bunker_data.TRAITS, unique_cards)
    additional_info_deck = _Deck(bunker_data.ADDITIONAL_INFO, unique_cards)
    ability_deck = _Deck(bunker_data.SPECIAL_ABILITIES, unique_cards)

    characters: dict[int, dict] = {}
    for user_id in player_ids:
        others = [p for p in player_ids if p != user_id]
        characters[user_id] = {
            "profession": _pick_profession(profession_deck),
            "age": _pick_age(),
            "gender": random.choice(bunker_data.GENDERS),
            "body_type": _pick_body_type(),
            "health": _pick_health(disease_deck),
            "hobby": _pick_hobby(hobby_deck),
            "phobia": _pick_phobia(phobia_deck),
            "backpack_item": _pick_backpack_item(backpack_deck),
            "large_item": _pick_large_item(large_item_deck),
            "trait": _pick_trait(trait_deck),
            "additional_info": _pick_additional_info(additional_info_deck, others, display_names),
            "special_abilities": _pick_special_abilities(ability_deck),
        }
    return characters


def pick_catastrophe() -> dict:
    return random.choice(bunker_data.CATASTROPHES)


def pick_bunker_conditions() -> dict:
    return random.choice(bunker_data.BUNKER_CONDITIONS)


# ────────────────────────── Голосование и конец игры ──────────────────────────

def resolve_expulsion_vote(votes: dict[int, int | None]) -> int | None:
    """Большинство голосов за исключение; ничья среди лидеров — никто не исключён."""
    tally: dict[int, int] = {}
    for target in votes.values():
        if target is None:
            continue
        tally[target] = tally.get(target, 0) + 1
    if not tally:
        return None
    top = max(tally.values())
    leaders = [target for target, count in tally.items() if count == top]
    return leaders[0] if len(leaders) == 1 else None


def is_game_over(alive_count: int, bunker_capacity: int) -> bool:
    return alive_count <= bunker_capacity
