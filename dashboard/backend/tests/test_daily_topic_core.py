import pytest

import daily_topic_core


@pytest.fixture(autouse=True)
def isolated_config(tmp_path, monkeypatch):
    monkeypatch.setattr(daily_topic_core, "CONFIG_FILE", str(tmp_path / "daily_topic_config.json"))


def test_is_valid_time():
    assert daily_topic_core.is_valid_time("09:00")
    assert daily_topic_core.is_valid_time("23:59")
    assert daily_topic_core.is_valid_time("00:00")
    assert not daily_topic_core.is_valid_time("24:00")
    assert not daily_topic_core.is_valid_time("9:00")
    assert not daily_topic_core.is_valid_time("09:60")
    assert not daily_topic_core.is_valid_time("")
    assert not daily_topic_core.is_valid_time(None)


def test_get_settings_defaults():
    assert daily_topic_core.get_settings() == {
        "enabled": False,
        "channel_id": "",
        "post_times": [],
        "topics": [],
    }


def test_update_settings():
    settings = daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["09:00", "20:00"])
    assert settings["enabled"] is True
    assert settings["channel_id"] == "500"
    assert settings["post_times"] == ["09:00", "20:00"]


def test_add_update_delete_topic():
    topic = daily_topic_core.add_topic("Вопрос 1")
    assert topic == {"id": "1", "text": "Вопрос 1"}

    second = daily_topic_core.add_topic("Вопрос 2")
    assert second["id"] == "2"
    assert len(daily_topic_core.get_settings()["topics"]) == 2

    updated = daily_topic_core.update_topic(topic["id"], "Обновлённый вопрос")
    assert updated["text"] == "Обновлённый вопрос"
    assert daily_topic_core.update_topic("999", "x") is None

    assert daily_topic_core.delete_topic(topic["id"]) is True
    assert daily_topic_core.delete_topic(topic["id"]) is False
    assert len(daily_topic_core.get_settings()["topics"]) == 1


def test_pick_next_topic_no_topics_returns_none():
    assert daily_topic_core.pick_next_topic() is None


def test_pick_next_topic_cycles_without_repeats():
    ids = {daily_topic_core.add_topic(f"Тема {i}")["id"] for i in range(5)}

    seen = [daily_topic_core.pick_next_topic()["id"] for _ in range(5)]

    assert set(seen) == ids
    assert len(seen) == len(set(seen))


def test_pick_next_topic_avoids_immediate_repeat_when_cycle_restarts():
    for i in range(2):
        daily_topic_core.add_topic(f"Тема {i}")

    first_cycle = [daily_topic_core.pick_next_topic()["id"] for _ in range(2)]
    last_of_cycle = first_cycle[-1]

    next_topic = daily_topic_core.pick_next_topic()
    assert next_topic["id"] != last_of_cycle


def test_pick_next_topic_survives_deleted_topic_in_queue():
    a = daily_topic_core.add_topic("A")
    b = daily_topic_core.add_topic("B")
    first = daily_topic_core.pick_next_topic()
    remaining_id = b["id"] if first["id"] == a["id"] else a["id"]

    daily_topic_core.delete_topic(remaining_id)
    c = daily_topic_core.add_topic("C")

    second = daily_topic_core.pick_next_topic()
    assert second["id"] == c["id"]


def test_mark_and_check_posted_today():
    assert daily_topic_core.already_posted_today() is False
    daily_topic_core.mark_posted_today()
    assert daily_topic_core.already_posted_today() is True


def test_get_today_post_time_no_times_returns_none():
    assert daily_topic_core.get_today_post_time() is None


def test_get_today_post_time_stable_within_day():
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["09:00", "14:00", "20:00"])
    first = daily_topic_core.get_today_post_time()
    assert first in ("09:00", "14:00", "20:00")
    for _ in range(5):
        assert daily_topic_core.get_today_post_time() == first


def test_get_today_post_time_recovers_if_chosen_time_removed():
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["09:00"])
    assert daily_topic_core.get_today_post_time() == "09:00"

    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["14:00"])
    assert daily_topic_core.get_today_post_time() == "14:00"


def test_should_post_now_false_without_post_times():
    assert daily_topic_core.should_post_now() is False


def test_should_post_now_true_when_time_passed():
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["00:00"])
    assert daily_topic_core.should_post_now() is True


def test_should_post_now_false_after_marking_posted():
    daily_topic_core.update_settings(enabled=True, channel_id="500", post_times=["00:00"])
    daily_topic_core.mark_posted_today()
    assert daily_topic_core.should_post_now() is False
