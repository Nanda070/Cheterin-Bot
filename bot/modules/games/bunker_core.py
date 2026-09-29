"""Ядро игры «Бункер»: конфигурация, генерация персонажей, подсчёт голосов, условие конца игры.

Без импорта discord — юнит-тестируемо напрямую (тот же подход, что и mafia_core.py).
Карточные пулы лежат в bunker_data.py; здесь только логика их выбора и раздачи.
"""

import random

import bot.data.bunker_data as bunker_data
import bot.data.bunker_data_en as bunker_data_en
import bot.modules.games.bunker_localize as bunker_localize
import bot.core.settings_db as settings_db

MODULE_NAME = "bunker"

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

def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_settings(guild_id: int) -> dict:
    """Настройки модуля сервера с дефолтами (выключен по умолчанию)."""
    data = settings_db.get(guild_id, MODULE_NAME)
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
    level_idx = random.randrange(len(bunker_data.PROFESSION_EXPERIENCE_LEVELS))
    return bunker_localize.merge_profession(profession, level_idx)


def _pick_hobby(deck: _Deck) -> dict:
    hobby = deck.draw()
    level_idx = random.randrange(len(bunker_data.HOBBY_EXPERIENCE_LEVELS))
    return bunker_localize.merge_hobby(hobby, level_idx)


def _pick_health(disease_deck: _Deck) -> dict:
    severity_idx = random.randrange(len(bunker_data.HEALTH_SEVERITIES))
    if bunker_data.HEALTH_SEVERITIES[severity_idx] == bunker_localize.HEALTHY_RU:
        return bunker_localize.merge_health(severity_idx, None)
    disease = disease_deck.draw()
    return bunker_localize.merge_health(severity_idx, disease)


def _pick_phobia(deck: _Deck) -> dict:
    return bunker_localize.merge_phobia(deck.draw())


def _pick_age() -> dict:
    return bunker_localize.merge_age(random.choice(bunker_data.AGE_CATEGORIES))


def _pick_body_type() -> dict:
    return bunker_localize.merge_body_type(random.choice(bunker_data.BODY_TYPES))


def _pick_backpack_item(deck: _Deck) -> dict:
    return bunker_localize.merge_inventory_item("backpack_items", deck.draw())


def _pick_large_item(deck: _Deck) -> dict:
    return bunker_localize.merge_inventory_item("large_items", deck.draw())


def _pick_trait(deck: _Deck) -> dict:
    return bunker_localize.merge_trait(deck.draw())


def _pick_additional_info(deck: _Deck, other_player_ids: list[int], display_names: dict[int, str]) -> dict:
    info = deck.draw()
    en_info = bunker_localize.additional_info_en_template(info)
    name = info["name"]
    name_en = en_info
    linked_user_id = None
    if info["category"] == bunker_localize.RELATIONSHIP_CATEGORY and other_player_ids:
        linked_user_id = random.choice(other_player_ids)
        target_name = display_names.get(linked_user_id, str(linked_user_id))
        name = name.replace(bunker_localize.RELATIONSHIP_MARKER_RU, target_name).replace("игрока №X", target_name)
        name_en = name_en.replace(bunker_localize.RELATIONSHIP_MARKER_EN, target_name)
    return bunker_localize.merge_additional_info(info, name, name_en, linked_user_id)


def _pick_special_abilities(deck: _Deck) -> list[dict]:
    cards = deck.draw_many(2)
    return [bunker_localize.merge_special_ability({**c, "used": False}) for c in cards]


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
            "gender": (gender := random.choice(bunker_data.GENDERS)),
            "gender_en": bunker_data_en.GENDERS[bunker_data.GENDERS.index(gender)],
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
    return bunker_localize.merge_catastrophe(random.choice(bunker_data.CATASTROPHES))


def pick_bunker_conditions() -> dict:
    return bunker_localize.merge_bunker_conditions(random.choice(bunker_data.BUNKER_CONDITIONS))


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
