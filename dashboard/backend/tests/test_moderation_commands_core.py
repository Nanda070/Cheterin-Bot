import pytest

import moderation_commands_core as core


@pytest.mark.parametrize(
    ("value", "expected_seconds"),
    [("30s", 30), ("10m", 600), ("2h", 7200), ("7d", 604800), ("1D", 86400)],
)
def test_parse_duration_valid(value, expected_seconds):
    assert core.parse_duration(value) == expected_seconds


@pytest.mark.parametrize("value", ["", "abc", "10", "m10", "10x", "-5m", "10 m"])
def test_parse_duration_invalid(value):
    with pytest.raises(ValueError):
        core.parse_duration(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("30s", "30 сек."), ("10m", "10 мин."), ("2h", "2 ч."), ("7d", "7 дн.")],
)
def test_format_duration(value, expected):
    assert core.format_duration(value) == expected


def test_normalize_reason_defaults_when_empty():
    assert core.normalize_reason(None) == core.DEFAULT_REASON
    assert core.normalize_reason("") == core.DEFAULT_REASON
    assert core.normalize_reason("   ") == core.DEFAULT_REASON


def test_normalize_reason_strips_and_keeps_text():
    assert core.normalize_reason("  спам  ") == "спам"


def test_command_reason_includes_moderator_id_and_name():
    text = core.command_reason("спам", "ModName", 12345)
    assert "спам" in text
    assert "ModName" in text
    assert "12345" in text


@pytest.mark.parametrize("number", [1, 500, 999])
def test_is_valid_clear_count_within_bounds(number):
    assert core.is_valid_clear_count(number) is True


@pytest.mark.parametrize("number", [0, -1, 1000, 10000])
def test_is_valid_clear_count_out_of_bounds(number):
    assert core.is_valid_clear_count(number) is False


@pytest.mark.parametrize(("value", "expected_seconds"), [("1m", 60), ("28d", 28 * 86400)])
def test_parse_mute_duration_within_limit(value, expected_seconds):
    assert core.parse_mute_duration(value) == expected_seconds


def test_parse_mute_duration_rejects_over_28_days():
    with pytest.raises(ValueError, match="28 дней"):
        core.parse_mute_duration("29d")


def test_parse_mute_duration_rejects_bad_format():
    with pytest.raises(ValueError, match="Неверный формат"):
        core.parse_mute_duration("бесконечно")
