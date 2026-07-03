import pytest

import feedback_categories


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(feedback_categories, "CONFIG_FILE", str(tmp_path / "feedback_categories.json"))


def _valid_spec(key="players", case_prefix="PR"):
    return {
        "key": key,
        "title": "Жалоба на участника",
        "button_label": "Жалоба на участника",
        "channel_id": "500",
        "case_prefix": case_prefix,
        "case_title": "Жалоба на участника",
        "thread_name": "player-report",
        "review_role_ids": ["111"],
        "approved_text": "Участник наказан.",
        "denied_text": "Жалоба отклонена.",
        "modal_title": "Жалоба на участника",
        "fields": [
            {"key": "offender", "label": "Ник участника", "style": "short", "required": True, "max_length": 120},
        ],
        "mini_summary_key": "offender",
    }


def test_load_categories_returns_empty_dict_when_file_missing():
    assert feedback_categories.load_categories() == {}


def test_save_then_load_round_trip():
    data = {"players": {"title": "X"}}
    feedback_categories.save_categories(data)
    assert feedback_categories.load_categories() == data


def test_validate_category_spec_accepts_valid_spec():
    assert feedback_categories.validate_category_spec(_valid_spec(), {}) is None


def test_validate_category_spec_rejects_invalid_key_format():
    spec = _valid_spec(key="Players With Spaces")
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_key"


def test_validate_category_spec_rejects_duplicate_key_on_create():
    spec = _valid_spec(key="players")
    existing = {"players": {}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key=None) == "key_taken"


def test_validate_category_spec_allows_same_key_on_edit():
    spec = _valid_spec(key="players")
    existing = {"players": {"case_prefix": "OTHER"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key="players") is None


def test_validate_category_spec_rejects_duplicate_case_prefix():
    spec = _valid_spec(key="staff", case_prefix="PR")
    existing = {"players": {"case_prefix": "PR"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key=None) == "case_prefix_taken"


def test_validate_category_spec_allows_own_case_prefix_on_edit():
    spec = _valid_spec(key="players", case_prefix="PR")
    existing = {"players": {"case_prefix": "PR"}}
    assert feedback_categories.validate_category_spec(spec, existing, existing_key="players") is None


def test_validate_category_spec_rejects_too_many_fields():
    spec = _valid_spec()
    spec["fields"] = [
        {"key": f"f{i}", "label": f"Field {i}", "style": "short", "required": False, "max_length": 100}
        for i in range(6)
    ]
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_count"


def test_validate_category_spec_rejects_zero_fields():
    spec = _valid_spec()
    spec["fields"] = []
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_count"


def test_validate_category_spec_rejects_duplicate_field_keys():
    spec = _valid_spec()
    spec["fields"] = [
        {"key": "a", "label": "A", "style": "short", "required": False, "max_length": 100},
        {"key": "a", "label": "B", "style": "short", "required": False, "max_length": 100},
    ]
    spec["mini_summary_key"] = "a"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_key"


def test_validate_category_spec_rejects_mini_summary_key_not_in_fields():
    spec = _valid_spec()
    spec["mini_summary_key"] = "does_not_exist"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_mini_summary_key"


def test_validate_category_spec_rejects_invalid_field_style():
    spec = _valid_spec()
    spec["fields"][0]["style"] = "wrong"
    assert feedback_categories.validate_category_spec(spec, {}) == "invalid_field_style"


def test_migrate_from_env_if_needed_creates_config_from_env(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    feedback_categories.migrate_from_env_if_needed()
    categories = feedback_categories.load_categories()
    assert "players" in categories
    assert categories["players"]["channel_id"] == "500"
    assert categories["players"]["case_prefix"] == "PR"


def test_migrate_from_env_if_needed_skips_when_file_already_exists(monkeypatch):
    monkeypatch.setenv("CHANNEL_COMPLAINT_PLAY", "500")
    monkeypatch.setenv("ROLE_PLAYERS", "111")
    feedback_categories.save_categories({"existing": {"case_prefix": "EX"}})
    feedback_categories.migrate_from_env_if_needed()
    categories = feedback_categories.load_categories()
    assert categories == {"existing": {"case_prefix": "EX"}}


def test_migrate_from_env_if_needed_skips_when_env_vars_missing():
    feedback_categories.migrate_from_env_if_needed()
    assert feedback_categories.load_categories() == {}
