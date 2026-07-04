import pytest

import brackets


@pytest.fixture(autouse=True)
def isolated_brackets_file(tmp_path, monkeypatch):
    monkeypatch.setattr(brackets, "BRACKETS_FILE", str(tmp_path / "brackets_data.json"))


def test_load_brackets_returns_empty_dict_when_file_missing():
    assert brackets.load_brackets() == {}


def test_load_brackets_returns_empty_dict_on_corrupt_json():
    with open(brackets.BRACKETS_FILE, "w", encoding="utf-8") as f:
        f.write("{not valid json")
    assert brackets.load_brackets() == {}


def test_save_then_load_round_trip():
    data = {"abc": {"id": "abc", "title": "T"}}
    brackets.save_brackets(data)
    assert brackets.load_brackets() == data


class _FakeMember:
    def __init__(self, member_id, display_name):
        self.id = member_id
        self.display_name = display_name


class _FakeGuild:
    def __init__(self, members):
        self._members = members

    def get_member(self, user_id):
        return next((m for m in self._members if m.id == user_id), None)


def test_extract_entries_solo_mode_uses_ign():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 1, "ign": "Nickname"}]}
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Nickname"]


def test_extract_entries_solo_mode_falls_back_to_member_display_name():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 42, "ign": None}]}
    guild = _FakeGuild([_FakeMember(42, "DiscordName")])
    assert brackets.extract_entries_from_event(ev, guild) == ["DiscordName"]


def test_extract_entries_solo_mode_falls_back_to_user_id_when_no_member():
    ev = {"type": "tournament", "mode": "solo", "participants": [{"user_id": 99, "ign": None}]}
    assert brackets.extract_entries_from_event(ev, guild=None) == ["User 99"]


def test_extract_entries_team_captain_mode():
    ev = {
        "type": "tournament",
        "mode": "team_captain",
        "participants": [
            {"user_id": 1, "team_name": "Alpha", "members": "a, b, c"},
            {"user_id": 2, "team_name": "Beta", "members": "d, e, f"},
        ],
    }
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Alpha", "Beta"]


def test_extract_entries_team_code_mode_groups_by_code_and_uses_captain_name():
    ev = {
        "type": "tournament",
        "mode": "team_code",
        "participants": [
            {"user_id": 1, "team_code": "ABC123", "team_name": "Alpha", "is_captain": True},
            {"user_id": 2, "team_code": "ABC123", "team_name": "Alpha", "is_captain": False},
            {"user_id": 3, "team_code": "XYZ999", "team_name": "Beta", "is_captain": True},
        ],
    }
    assert brackets.extract_entries_from_event(ev, guild=None) == ["Alpha", "Beta"]


@pytest.mark.parametrize("n,expected", [(1, 1), (2, 2), (3, 4), (4, 4), (5, 8), (8, 8), (9, 16)])
def test_next_power_of_two(n, expected):
    assert brackets._next_power_of_two(n) == expected


@pytest.mark.parametrize(
    "size,expected",
    [
        (2, [1, 2]),
        (4, [1, 4, 2, 3]),
        (8, [1, 8, 4, 5, 2, 7, 3, 6]),
    ],
)
def test_seed_order(size, expected):
    assert brackets._seed_order(size) == expected


def test_generate_rounds_no_byes_perfect_power_of_two():
    rounds = brackets.generate_rounds(["A", "B", "C", "D"])
    assert len(rounds) == 2
    assert rounds[0] == [
        {"slot_a": "A", "slot_b": "D", "winner": None},
        {"slot_a": "B", "slot_b": "C", "winner": None},
    ]
    assert rounds[1] == [{"slot_a": None, "slot_b": None, "winner": None}]


def test_generate_rounds_with_byes_auto_resolves():
    rounds = brackets.generate_rounds(["A", "B", "C", "D", "E"])
    assert rounds[0] == [
        {"slot_a": "A", "slot_b": None, "winner": "a"},
        {"slot_a": "D", "slot_b": "E", "winner": None},
        {"slot_a": "B", "slot_b": None, "winner": "a"},
        {"slot_a": "C", "slot_b": None, "winner": "a"},
    ]
    assert rounds[1] == [
        {"slot_a": "A", "slot_b": None, "winner": None},
        {"slot_a": "B", "slot_b": "C", "winner": None},
    ]
    assert rounds[2] == [{"slot_a": None, "slot_b": None, "winner": None}]


@pytest.mark.parametrize("n", list(range(2, 25)))
def test_generate_rounds_never_produces_a_double_bye_match(n):
    entries = [f"E{i}" for i in range(n)]
    rounds = brackets.generate_rounds(entries)
    for match in rounds[0]:
        assert not (match["slot_a"] is None and match["slot_b"] is None)


def test_create_bracket_builds_expected_shape():
    bracket = brackets.create_bracket("Летний турнир", ["A", "B", "C", "D"], None, 10)
    assert bracket["title"] == "Летний турнир"
    assert bracket["source_event_id"] is None
    assert bracket["entries"] == ["A", "B", "C", "D"]
    assert bracket["created_by"] == "10"
    assert bracket["share_token"] is None
    assert len(bracket["rounds"]) == 2
    assert "id" in bracket
    assert "created_at" in bracket
