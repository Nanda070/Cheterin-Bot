import pytest

import bot.modules.moderation.moderation_commands_core as core


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


def test_normalize_reason_empty_when_missing():
    assert core.normalize_reason(None) == ""
    assert core.normalize_reason("") == ""
    assert core.normalize_reason("   ") == ""


def test_normalize_reason_strips_and_keeps_text():
    assert core.normalize_reason("  спам  ") == "спам"


def test_command_reason_includes_moderator_id_and_name():
    text = core.command_reason("спам", "ModName", 12345)
    assert "спам" in text
    assert "ModName" in text
    assert "12345" in text


def test_command_reason_bare_when_empty():
    text = core.command_reason("", "ModName", 12345)
    assert "ModName" in text
    assert "12345" in text
    assert text.startswith("команда:") or " — " not in text


def test_format_user_ref_prefers_mention():
    assert core.format_user_ref("alice", 42, "<@42>") == "<@42> (`42`)"
    assert core.format_user_ref("alice", 42) == "alice (`42`)"


def test_action_log_fields_omits_empty_reason():
    fields = core.action_log_fields("ru", "who", "target", reason="", extra="Срок: 1 ч.")
    names = [name for name, _ in fields]
    assert names == ["Кто", "Кого", "Дополнительно"]
    assert fields[2][1] == "Срок: 1 ч."


def test_action_log_fields_includes_nonempty_reason():
    fields = core.action_log_fields("ru", "who", "target", reason="спам")
    names = [name for name, _ in fields]
    assert names == ["Кто", "Кого", "Причина"]
    assert fields[2][1] == "спам"


def test_success_message_appends_reason_only_when_present():
    with_reason = core.success_message(
        "moderation.success.kick", "ru", "флуд", mention="<@1>",
    )
    without = core.success_message("moderation.success.kick", "ru", "", mention="<@1>")
    assert "Причина: флуд" in with_reason
    assert "Причина" not in without


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
