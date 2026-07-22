import bunker_core
import bunker_data
import bunker_localize


def test_localize_character_en_swaps_text_fields():
    characters = bunker_core.generate_characters([1], {1: "Alice"})
    ru = characters[1]
    en = bunker_localize.localize_character(ru, "en")

    assert en["gender"] == ru["gender_en"]
    assert en["profession"]["name"] == ru["profession"]["name_en"]
    assert en["profession"]["category"] == ru["profession"]["category_en"]
    assert en["age"]["label"] == ru["age"]["label_en"]
    assert en["special_abilities"][0]["effect"] == ru["special_abilities"][0]["effect_en"]


def test_localize_character_ru_returns_unchanged():
    characters = bunker_core.generate_characters([1], {1: "Alice"})
    ru = characters[1]
    assert bunker_localize.localize_character(ru, "ru") is ru


def test_localize_game_scenario_uses_keys():
    catastrophe = bunker_core.pick_catastrophe()
    conditions = bunker_core.pick_bunker_conditions()
    game = {
        "catastrophe_key": catastrophe["key"],
        "catastrophe_name": catastrophe["name"],
        "catastrophe_description": catastrophe["description"],
        "bunker_conditions_key": conditions["key"],
        "bunker_conditions_name": conditions["name"],
        "bunker_conditions_description": conditions["description"],
    }
    cat_name, cat_desc, cond_name, cond_desc = bunker_localize.localize_game_scenario(game, "en")
    assert cat_name == catastrophe["name_en"]
    assert cat_desc == catastrophe["description_en"]
    assert cond_name == conditions["name_en"]
    assert cond_desc == conditions["description_en"]


def test_get_card_pools_en():
    pools = bunker_localize.get_card_pools("en")
    assert pools["genders"] == ["Male", "Female"]
    assert pools["health_severities"][0] == "Healthy"
    assert len(pools["professions"]) == len(bunker_data.PROFESSIONS)
