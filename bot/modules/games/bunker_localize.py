"""Localization for Bunker card data: RU source pools + bunker_data_en."""

from __future__ import annotations

import copy

import bot.data.bunker_data as bunker_data
import bot.data.bunker_data_en as bunker_data_en

RELATIONSHIP_CATEGORY = "Активные (Отношения)"
RELATIONSHIP_MARKER_RU = "Игрок №X"
RELATIONSHIP_MARKER_EN = "Player #X"

HEALTHY_RU = "Здоров"
HEALTHY_EN = "Healthy"

_BY_ID = {
    "professions": ({p["id"]: p for p in bunker_data_en.PROFESSIONS}, "id"),
    "hobbies": ({h["id"]: h for h in bunker_data_en.HOBBIES}, "id"),
    "health_diseases": ({d["id"]: d for d in bunker_data_en.HEALTH_DISEASES}, "id"),
    "phobias": ({p["id"]: p for p in bunker_data_en.PHOBIAS}, "id"),
    "backpack_items": ({i["id"]: i for i in bunker_data_en.BACKPACK_ITEMS}, "id"),
    "large_items": ({i["id"]: i for i in bunker_data_en.LARGE_INVENTORY_ITEMS}, "id"),
    "additional_info": ({i["id"]: i for i in bunker_data_en.ADDITIONAL_INFO}, "id"),
    "special_abilities": ({a["id"]: a for a in bunker_data_en.SPECIAL_ABILITIES}, "id"),
}

_AGE_BY_KEY = {a["key"]: a for a in bunker_data_en.AGE_CATEGORIES}
_BODY_BY_KEY = {b["key"]: b for b in bunker_data_en.BODY_TYPES}
_CATASTROPHE_BY_KEY = {c["key"]: c for c in bunker_data_en.CATASTROPHES}
_CONDITIONS_BY_KEY = {c["key"]: c for c in bunker_data_en.BUNKER_CONDITIONS}

_TRAIT_EN_BY_RU = {t["trait"]: en["trait"] for t, en in zip(bunker_data.TRAITS, bunker_data_en.TRAITS, strict=True)}
_TRAIT_CATEGORY_EN = {
    ru["trait"]: en["category"] for ru, en in zip(bunker_data.TRAITS, bunker_data_en.TRAITS, strict=True)
}
_TRAIT_BEHAVIOR_EN = {
    ru["trait"]: en["behavior_example"]
    for ru, en in zip(bunker_data.TRAITS, bunker_data_en.TRAITS, strict=True)
}
_TRAIT_BUNKER_BEHAVIOR_EN = {
    ru["trait"]: en["possible_bunker_behavior"]
    for ru, en in zip(bunker_data.TRAITS, bunker_data_en.TRAITS, strict=True)
}


def _en_item(pool_name: str, ru_item: dict) -> dict | None:
    lookup, key_field = _BY_ID[pool_name]
    item_id = ru_item.get(key_field)
    if item_id is None:
        return None
    return lookup.get(item_id)


def _attach_en_fields(ru: dict, en: dict | None, fields: tuple[str, ...]) -> dict:
    out = dict(ru)
    if en is None:
        return out
    for field in fields:
        if field in en:
            out[f"{field}_en"] = en[field]
    return out


def merge_profession(ru: dict, level_idx: int) -> dict:
    en = _en_item("professions", ru)
    level_ru = bunker_data.PROFESSION_EXPERIENCE_LEVELS[level_idx]
    level_en = bunker_data_en.PROFESSION_EXPERIENCE_LEVELS[level_idx]
    return {
        "id": ru["id"],
        "name": ru["name"],
        "name_en": en["name"] if en else ru["name"],
        "category": ru["category"],
        "category_en": en["category"] if en else ru["category"],
        "experience_level": level_ru["level"],
        "experience_level_en": level_en["level"],
        "has_ability": level_ru["has_ability"],
    }


def merge_hobby(ru: dict, level_idx: int) -> dict:
    en = _en_item("hobbies", ru)
    level_ru = bunker_data.HOBBY_EXPERIENCE_LEVELS[level_idx]
    level_en = bunker_data_en.HOBBY_EXPERIENCE_LEVELS[level_idx]
    return {
        "id": ru["id"],
        "name": ru["name"],
        "name_en": en["name"] if en else ru["name"],
        "category": ru["category"],
        "category_en": en["category"] if en else ru["category"],
        "experience_level": level_ru["level"],
        "experience_level_en": level_en["level"],
    }


def merge_health(severity_idx: int, disease: dict | None) -> dict:
    severity_ru = bunker_data.HEALTH_SEVERITIES[severity_idx]
    severity_en = bunker_data_en.HEALTH_SEVERITIES[severity_idx]
    if severity_ru == HEALTHY_RU:
        return {
            "severity": severity_ru,
            "severity_en": severity_en,
            "disease_name": None,
            "disease_name_en": None,
            "category": None,
            "category_en": None,
        }
    en = _en_item("health_diseases", disease) if disease else None
    return {
        "severity": severity_ru,
        "severity_en": severity_en,
        "disease_name": disease["name"],
        "disease_name_en": en["name"] if en else disease["name"],
        "category": disease["category"],
        "category_en": en["category"] if en else disease["category"],
    }


def merge_phobia(ru: dict) -> dict:
    en = _en_item("phobias", ru)
    return {
        "id": ru["id"],
        "name": ru["name"],
        "name_en": en["name"] if en else ru["name"],
        "type": ru["type"],
        "type_en": en["type"] if en else ru["type"],
    }


def merge_age(ru: dict) -> dict:
    en = _AGE_BY_KEY.get(ru["key"], ru)
    return {
        "key": ru["key"],
        "label": ru["label"],
        "label_en": en.get("label", ru["label"]),
        "note": ru.get("note"),
        "note_en": en.get("note"),
    }


def merge_body_type(ru: dict) -> dict:
    en = _BODY_BY_KEY.get(ru["key"], ru)
    out = dict(ru)
    for field in (
        "name", "agility", "stamina", "strength", "disease_note",
        "food_requirement", "heat_tolerance", "cold_tolerance", "reproduction",
    ):
        out[f"{field}_en"] = en.get(field, ru.get(field))
    return out


def merge_inventory_item(pool_name: str, ru: dict) -> dict:
    en = _en_item(pool_name, ru)
    return {
        "id": ru["id"],
        "name": ru["name"],
        "name_en": en["name"] if en else ru["name"],
        "category": ru["category"],
        "category_en": en["category"] if en else ru["category"],
    }


def merge_trait(ru: dict) -> dict:
    trait_key = ru["trait"]
    return {
        "trait": trait_key,
        "trait_en": _TRAIT_EN_BY_RU.get(trait_key, trait_key),
        "category": ru["category"],
        "category_en": _TRAIT_CATEGORY_EN.get(trait_key, ru["category"]),
        "behavior_example": ru["behavior_example"],
        "behavior_example_en": _TRAIT_BEHAVIOR_EN.get(trait_key, ru["behavior_example"]),
        "possible_bunker_behavior": ru["possible_bunker_behavior"],
        "possible_bunker_behavior_en": _TRAIT_BUNKER_BEHAVIOR_EN.get(
            trait_key, ru["possible_bunker_behavior"]
        ),
    }


def additional_info_en_template(ru: dict) -> str:
    en = _en_item("additional_info", ru)
    return en["name"] if en else ru["name"]


def merge_additional_info(ru: dict, name: str, name_en: str, linked_user_id: int | None) -> dict:
    en = _en_item("additional_info", ru)
    return {
        "id": ru["id"],
        "name": name,
        "name_en": name_en,
        "category": ru["category"],
        "category_en": en["category"] if en else ru["category"],
        "linked_user_id": linked_user_id,
    }


def merge_special_ability(ru: dict) -> dict:
    en = _en_item("special_abilities", ru)
    return {
        "id": ru["id"],
        "name": ru["name"],
        "name_en": en["name"] if en else ru["name"],
        "category": ru["category"],
        "category_en": en["category"] if en else ru["category"],
        "effect": ru["effect"],
        "effect_en": en["effect"] if en else ru["effect"],
        "used": ru.get("used", False),
    }


def merge_catastrophe(ru: dict) -> dict:
    en = _CATASTROPHE_BY_KEY.get(ru["key"], ru)
    return {
        "key": ru["key"],
        "name": ru["name"],
        "name_en": en.get("name", ru["name"]),
        "description": ru["description"],
        "description_en": en.get("description", ru["description"]),
    }


def merge_bunker_conditions(ru: dict) -> dict:
    en = _CONDITIONS_BY_KEY.get(ru["key"], ru)
    return {
        "key": ru["key"],
        "name": ru["name"],
        "name_en": en.get("name", ru["name"]),
        "description": ru["description"],
        "description_en": en.get("description", ru["description"]),
    }


def _swap_field(obj: dict, field: str) -> None:
    en_key = f"{field}_en"
    if en_key in obj and obj[en_key]:
        obj[field] = obj[en_key]


def localize_character(character: dict | None, lang: str) -> dict | None:
    """Return a copy with RU text fields replaced by EN when lang == 'en'."""
    if not character or lang != "en":
        return character
    c = copy.deepcopy(character)

    if profession := c.get("profession"):
        for field in ("name", "category", "experience_level"):
            _swap_field(profession, field)

    if age := c.get("age"):
        _swap_field(age, "label")

    _swap_field(c, "gender")

    if body := c.get("body_type"):
        for field in (
            "name", "agility", "stamina", "strength", "disease_note",
            "food_requirement", "heat_tolerance", "cold_tolerance", "reproduction",
        ):
            _swap_field(body, field)

    if health := c.get("health"):
        for field in ("severity", "disease_name", "category"):
            _swap_field(health, field)

    if hobby := c.get("hobby"):
        for field in ("name", "category", "experience_level"):
            _swap_field(hobby, field)

    if phobia := c.get("phobia"):
        for field in ("name", "type"):
            _swap_field(phobia, field)

    for item_key in ("backpack_item", "large_item"):
        if item := c.get(item_key):
            for field in ("name", "category"):
                _swap_field(item, field)

    if trait := c.get("trait"):
        _swap_field(trait, "trait")
        _swap_field(trait, "category")
        _swap_field(trait, "behavior_example")
        _swap_field(trait, "possible_bunker_behavior")

    if info := c.get("additional_info"):
        for field in ("name", "category"):
            _swap_field(info, field)

    for ability in c.get("special_abilities") or []:
        for field in ("name", "category", "effect"):
            _swap_field(ability, field)

    return c


def localize_game_scenario(game: dict, lang: str) -> tuple[str, str, str, str]:
    """Catastrophe + bunker conditions names/descriptions for embeds and public API."""
    if lang != "en":
        return (
            game.get("catastrophe_name") or "",
            game.get("catastrophe_description") or "",
            game.get("bunker_conditions_name") or "",
            game.get("bunker_conditions_description") or "",
        )

    cat_key = game.get("catastrophe_key")
    cond_key = game.get("bunker_conditions_key")
    cat = _CATASTROPHE_BY_KEY.get(cat_key) if cat_key else None
    cond = _CONDITIONS_BY_KEY.get(cond_key) if cond_key else None

    return (
        cat["name"] if cat else game.get("catastrophe_name_en") or game.get("catastrophe_name") or "",
        cat["description"] if cat else game.get("catastrophe_description_en") or game.get("catastrophe_description") or "",
        cond["name"] if cond else game.get("bunker_conditions_name_en") or game.get("bunker_conditions_name") or "",
        cond["description"] if cond else game.get("bunker_conditions_description_en") or game.get("bunker_conditions_description") or "",
    )


def get_card_pools(lang: str) -> dict:
    """Card pools for dashboard editor — full pool in requested language."""
    if lang != "en":
        return {
            "genders": bunker_data.GENDERS,
            "ages": bunker_data.AGE_CATEGORIES,
            "body_types": bunker_data.BODY_TYPES,
            "professions": bunker_data.PROFESSIONS,
            "profession_experience_levels": bunker_data.PROFESSION_EXPERIENCE_LEVELS,
            "hobbies": bunker_data.HOBBIES,
            "hobby_experience_levels": bunker_data.HOBBY_EXPERIENCE_LEVELS,
            "health_severities": bunker_data.HEALTH_SEVERITIES,
            "health_diseases": bunker_data.HEALTH_DISEASES,
            "phobias": bunker_data.PHOBIAS,
            "backpack_items": bunker_data.BACKPACK_ITEMS,
            "large_items": bunker_data.LARGE_INVENTORY_ITEMS,
            "traits": bunker_data.TRAITS,
            "additional_info": bunker_data.ADDITIONAL_INFO,
            "special_abilities": bunker_data.SPECIAL_ABILITIES,
        }
    return {
        "genders": bunker_data_en.GENDERS,
        "ages": bunker_data_en.AGE_CATEGORIES,
        "body_types": bunker_data_en.BODY_TYPES,
        "professions": bunker_data_en.PROFESSIONS,
        "profession_experience_levels": bunker_data_en.PROFESSION_EXPERIENCE_LEVELS,
        "hobbies": bunker_data_en.HOBBIES,
        "hobby_experience_levels": bunker_data_en.HOBBY_EXPERIENCE_LEVELS,
        "health_severities": bunker_data_en.HEALTH_SEVERITIES,
        "health_diseases": bunker_data_en.HEALTH_DISEASES,
        "phobias": bunker_data_en.PHOBIAS,
        "backpack_items": bunker_data_en.BACKPACK_ITEMS,
        "large_items": bunker_data_en.LARGE_INVENTORY_ITEMS,
        "traits": bunker_data_en.TRAITS,
        "additional_info": bunker_data_en.ADDITIONAL_INFO,
        "special_abilities": bunker_data_en.SPECIAL_ABILITIES,
    }
