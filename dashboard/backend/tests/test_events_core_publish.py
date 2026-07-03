import discord
import pytest

import events
import events_core
from dashboard.backend.tests.fakes import FakeBot, FakeChannel, FakeGuild


@pytest.fixture(autouse=True)
def isolated_events_file(tmp_path, monkeypatch):
    monkeypatch.setattr(events, "EVENTS_FILE", str(tmp_path / "events_data.json"))


def _tournament_spec(**overrides):
    spec = {
        "type": "tournament",
        "title": "Летний турнир",
        "description": "Описание турнира",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "options": [],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


def _poll_spec(**overrides):
    spec = {
        "type": "poll",
        "title": "Опрос дня",
        "description": "Описание опроса",
        "banner_url": "",
        "mode": "solo",
        "require_info": False,
        "max_limit": 0,
        "team_size": 5,
        "role_reward": None,
        "ping": "none",
        "options": ["Да", "Нет"],
        "multi_select": False,
    }
    spec.update(overrides)
    return spec


# --- validate_event_spec ---


def test_validate_event_spec_rejects_invalid_type():
    assert events_core.validate_event_spec(_tournament_spec(type="bogus")) == "invalid_type"


def test_validate_event_spec_rejects_empty_title():
    assert events_core.validate_event_spec(_tournament_spec(title="")) == "invalid_title"


def test_validate_event_spec_rejects_title_too_long():
    assert events_core.validate_event_spec(_tournament_spec(title="x" * 101)) == "invalid_title"


def test_validate_event_spec_rejects_empty_description():
    assert events_core.validate_event_spec(_tournament_spec(description="")) == "invalid_description"


def test_validate_event_spec_rejects_description_too_long():
    assert events_core.validate_event_spec(_tournament_spec(description="x" * 2001)) == "invalid_description"


def test_validate_event_spec_rejects_invalid_ping():
    assert events_core.validate_event_spec(_tournament_spec(ping="role:123")) == "invalid_ping"


def test_validate_event_spec_rejects_invalid_mode_for_tournament():
    assert events_core.validate_event_spec(_tournament_spec(mode="bogus")) == "invalid_mode"


def test_validate_event_spec_rejects_negative_max_limit():
    assert events_core.validate_event_spec(_tournament_spec(max_limit=-1)) == "invalid_max_limit"


def test_validate_event_spec_rejects_team_size_below_2_when_not_solo():
    spec = _tournament_spec(mode="team_captain", team_size=1)
    assert events_core.validate_event_spec(spec) == "invalid_team_size"


def test_validate_event_spec_allows_missing_team_size_check_for_solo_mode():
    spec = _tournament_spec(mode="solo", team_size=1)
    assert events_core.validate_event_spec(spec) is None


def test_validate_event_spec_rejects_poll_with_too_few_options():
    assert events_core.validate_event_spec(_poll_spec(options=["Только один"])) == "invalid_options"


def test_validate_event_spec_rejects_poll_with_non_list_options():
    assert events_core.validate_event_spec(_poll_spec(options="Да, Нет")) == "invalid_options"


def test_validate_event_spec_accepts_valid_tournament_spec():
    assert events_core.validate_event_spec(_tournament_spec()) is None


def test_validate_event_spec_accepts_valid_poll_spec():
    assert events_core.validate_event_spec(_poll_spec()) is None


# --- publish_event ---


@pytest.mark.asyncio
async def test_publish_event_tournament_creates_matching_event_obj_and_view():
    channel = FakeChannel(500, name="tourneys")
    bot = FakeBot(FakeGuild())
    spec = _tournament_spec(max_limit=10, role_reward="200")

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    ev = data["events"][str(message.id)]
    assert ev["type"] == "tournament"
    assert ev["channel_id"] == 500
    assert ev["author_id"] == 1
    assert ev["title"] == "Летний турнир"
    assert ev["mode"] == "solo"
    assert ev["max_limit"] == 10
    assert ev["role_reward"] == 200
    assert ev["status"] == "open"
    assert ev["participants"] == []
    assert ev["votes"] == {}
    assert len(channel.send_calls) == 1
    assert channel.send_calls[0]["embed"].title == "Летний турнир"
    sent_message = channel._messages[message.id]
    assert len(sent_message.edit_calls) == 1
    assert sent_message.edit_calls[0]["view"] is not None


@pytest.mark.asyncio
async def test_publish_event_poll_creates_matching_event_obj_and_view():
    channel = FakeChannel(500, name="polls")
    bot = FakeBot(FakeGuild())
    spec = _poll_spec(multi_select=True)

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    ev = data["events"][str(message.id)]
    assert ev["type"] == "poll"
    assert ev["options"] == ["Да", "Нет"]
    assert ev["multi_select"] is True
    assert ev["votes"] == {}
    assert len(channel.send_calls) == 1


@pytest.mark.asyncio
async def test_publish_event_role_reward_none_stays_none():
    channel = FakeChannel(500, name="tourneys")
    bot = FakeBot(FakeGuild())
    spec = _tournament_spec(role_reward=None)

    message = await events_core.publish_event(bot, channel, spec, author_id=1)

    data = await events.load_events()
    assert data["events"][str(message.id)]["role_reward"] is None
