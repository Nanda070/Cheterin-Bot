import pytest

import bunker_core
import bunker_data
import settings_db


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setenv("SETTINGS_DB_PATH", str(tmp_path / "settings.db"))
    monkeypatch.setattr(settings_db, "_cache", {})
    settings_db.init()


def test_get_settings_defaults():
    settings = bunker_core.get_settings(404)
    assert settings["enabled"] is False
    assert settings["default_min_players"] == bunker_core.DEFAULT_MIN_PLAYERS
    assert settings["default_max_players"] == bunker_core.DEFAULT_MAX_PLAYERS
    assert settings["default_discussion_timer_sec"] == bunker_core.DEFAULT_DISCUSSION_TIMER_SEC
    assert settings["default_vote_timer_sec"] == bunker_core.DEFAULT_VOTE_TIMER_SEC
    assert settings["default_unique_cards"] == bunker_core.DEFAULT_UNIQUE_CARDS
    assert settings["log_channel_id"] == ""


def test_save_config_roundtrip():
    bunker_core.save_config(404, {"enabled": True, "default_min_players": 6, "default_unique_cards": False, "log_channel_id": "123"})
    settings = bunker_core.get_settings(404)
    assert settings["enabled"] is True
    assert settings["default_min_players"] == 6
    assert settings["default_unique_cards"] is False
    assert settings["log_channel_id"] == "123"


class _FakePermissions:
    def __init__(self, manage_guild=False, administrator=False):
        self.manage_guild = manage_guild
        self.administrator = administrator


class _FakeMember:
    def __init__(self, manage_guild=False, administrator=False):
        self.guild_permissions = _FakePermissions(manage_guild, administrator)


def test_has_moderator_access():
    assert bunker_core.has_moderator_access(_FakeMember(manage_guild=True)) is True
    assert bunker_core.has_moderator_access(_FakeMember(administrator=True)) is True
    assert bunker_core.has_moderator_access(_FakeMember()) is False


@pytest.mark.parametrize(("count", "expected"), [(1, 1), (2, 1), (3, 1), (4, 2), (7, 3), (10, 5)])
def test_default_bunker_capacity(count, expected):
    assert bunker_core.default_bunker_capacity(count) == expected


# ────────────────────────── Генерация персонажей ──────────────────────────

def test_generate_characters_covers_all_players_with_full_field_set():
    player_ids = [1, 2, 3]
    display_names = {1: "Аня", 2: "Боря", 3: "Вика"}
    characters = bunker_core.generate_characters(player_ids, display_names)

    assert set(characters.keys()) == set(player_ids)
    for character in characters.values():
        for key in bunker_core.FIELD_KEYS:
            assert key in character
        assert character["gender"] in bunker_data.GENDERS
        assert len(character["special_abilities"]) == 2
        names = {c["name"] for c in character["special_abilities"]}
        assert len(names) == 2
        assert all(c["used"] is False for c in character["special_abilities"])


def test_generate_characters_health_severity_matches_disease_presence():
    characters = bunker_core.generate_characters([1], {1: "Аня"})
    health = characters[1]["health"]
    if health["severity"] == "Здоров":
        assert health["disease_name"] is None
    else:
        assert health["disease_name"] is not None


def test_generate_characters_relationship_card_links_to_another_player(monkeypatch):
    relationship_entry = {
        "id": 999,
        "name": "Вы и Игрок №X — кровные враги.",
        "category": "Активные (Отношения)",
    }
    monkeypatch.setattr(bunker_data, "ADDITIONAL_INFO", [relationship_entry])

    player_ids = [1, 2, 3]
    display_names = {1: "Аня", 2: "Боря", 3: "Вика"}
    # unique_cards=False -- пул из одной карты не может обеспечить 3 уникальных розыгрыша.
    characters = bunker_core.generate_characters(player_ids, display_names, unique_cards=False)

    for user_id, character in characters.items():
        info = character["additional_info"]
        assert info["category"] == "Активные (Отношения)"
        assert info["linked_user_id"] in {p for p in player_ids if p != user_id}
        assert "№X" not in info["name"]
        assert display_names[info["linked_user_id"]] in info["name"]


def test_generate_characters_relationship_card_no_link_when_solo(monkeypatch):
    relationship_entry = {
        "id": 999,
        "name": "Вы и Игрок №X — кровные враги.",
        "category": "Активные (Отношения)",
    }
    monkeypatch.setattr(bunker_data, "ADDITIONAL_INFO", [relationship_entry])

    characters = bunker_core.generate_characters([1], {1: "Аня"})
    info = characters[1]["additional_info"]
    assert info["linked_user_id"] is None
    assert "№X" in info["name"]


def test_pick_catastrophe_and_bunker_conditions_return_known_entries():
    catastrophe = bunker_core.pick_catastrophe()
    assert catastrophe in bunker_data.CATASTROPHES
    conditions = bunker_core.pick_bunker_conditions()
    assert conditions in bunker_data.BUNKER_CONDITIONS


# ────────────────────────── Раздача карточек: без повторов / с повторами ──────────────────────────

def test_generate_characters_unique_cards_no_duplicates_across_players():
    player_ids = list(range(1, 11))
    display_names = {i: f"P{i}" for i in player_ids}
    characters = bunker_core.generate_characters(player_ids, display_names, unique_cards=True)

    professions = [c["profession"]["name"] for c in characters.values()]
    assert len(set(professions)) == len(professions)

    hobbies = [c["hobby"]["name"] for c in characters.values()]
    assert len(set(hobbies)) == len(hobbies)

    backpack_items = [c["backpack_item"]["name"] for c in characters.values()]
    assert len(set(backpack_items)) == len(backpack_items)

    all_ability_names = [a["name"] for c in characters.values() for a in c["special_abilities"]]
    assert len(set(all_ability_names)) == len(all_ability_names)  # уникальны и внутри игрока, и между игроками


def test_generate_characters_unique_cards_is_default():
    player_ids = list(range(1, 11))
    display_names = {i: f"P{i}" for i in player_ids}
    characters = bunker_core.generate_characters(player_ids, display_names)  # unique_cards не передан

    professions = [c["profession"]["name"] for c in characters.values()]
    assert len(set(professions)) == len(professions)


def test_generate_characters_with_repeats_allows_duplicates(monkeypatch):
    tiny_pool = [{"id": 1, "name": "Единственная профессия", "category": "Тест"}]
    monkeypatch.setattr(bunker_data, "PROFESSIONS", tiny_pool)

    player_ids = [1, 2, 3]
    display_names = {1: "A", 2: "B", 3: "C"}
    characters = bunker_core.generate_characters(player_ids, display_names, unique_cards=False)
    assert all(c["profession"]["name"] == "Единственная профессия" for c in characters.values())


def test_generate_characters_unique_cards_raises_when_pool_smaller_than_player_count(monkeypatch):
    tiny_pool = [{"id": 1, "name": "Единственная профессия", "category": "Тест"}]
    monkeypatch.setattr(bunker_data, "PROFESSIONS", tiny_pool)

    player_ids = [1, 2]
    display_names = {1: "A", 2: "B"}
    with pytest.raises(IndexError):
        bunker_core.generate_characters(player_ids, display_names, unique_cards=True)


# ────────────────────────── Голосование и конец игры ──────────────────────────

def test_resolve_expulsion_vote_majority():
    assert bunker_core.resolve_expulsion_vote({1: 100, 2: 100, 3: 200}) == 100


def test_resolve_expulsion_vote_tie_returns_none():
    assert bunker_core.resolve_expulsion_vote({1: 100, 2: 200}) is None


def test_resolve_expulsion_vote_all_skip_returns_none():
    assert bunker_core.resolve_expulsion_vote({1: None, 2: None}) is None


def test_resolve_expulsion_vote_empty_returns_none():
    assert bunker_core.resolve_expulsion_vote({}) is None


def test_is_game_over():
    assert bunker_core.is_game_over(alive_count=4, bunker_capacity=4) is True
    assert bunker_core.is_game_over(alive_count=3, bunker_capacity=4) is True
    assert bunker_core.is_game_over(alive_count=5, bunker_capacity=4) is False
