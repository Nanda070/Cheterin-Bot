import case_timeline_core


def test_build_case_timeline_filters_sorts_and_limits():
    warns = [
        {
            "id": 1,
            "reason": "flood",
            "moderator_id": "10",
            "source": "manual",
            "created_at": "2026-01-01T12:00:00+00:00",
            "expires_at": None,
            "removed": False,
            "removed_by": None,
            "removed_at": None,
        }
    ]
    events = [
        {
            "type": "manual_ban",
            "timestamp": "2026-01-03T12:00:00+00:00",
            "user_id": "100",
            "user_display": "fighter",
            "moderator_id": "10",
            "moderator_display": "mod",
            "reason": "repeat offense",
            "extra": "delete 0d",
        },
        {
            "type": "manual_kick",
            "timestamp": "2026-01-02T12:00:00+00:00",
            "user_id": "999",
            "user_display": "other",
            "moderator_id": "10",
            "moderator_display": "mod",
            "reason": "not this user",
            "extra": "",
        },
        {
            "type": "command_mute",
            "timestamp": "2026-01-02T08:00:00+00:00",
            "user_id": "100",
            "user_display": "fighter",
            "moderator_id": "10",
            "moderator_display": "mod",
            "reason": "timeout",
            "extra": "1h",
        },
    ]

    items = case_timeline_core.build_case_timeline(warns, events, 100, limit=10)
    assert [i["kind"] for i in items] == ["manual_ban", "command_mute", "warn"]
    assert items[0]["reason"] == "repeat offense"
    assert items[0]["moderator_display"] == "mod"
    assert items[2]["meta"]["warn_id"] == 1
    assert items[2]["meta"]["source"] == "manual"


def test_dedupe_prefers_warns_db_over_warn_manual_log():
    warns = [
        {
            "id": 7,
            "reason": "spam",
            "moderator_id": "10",
            "source": "manual",
            "created_at": "2026-02-01T15:30:00.123456+00:00",
            "expires_at": None,
            "removed": False,
            "removed_by": None,
            "removed_at": None,
        }
    ]
    events = [
        {
            "type": "warn_manual",
            "timestamp": "2026-02-01T15:30:00+00:00",
            "user_id": "100",
            "user_display": "fighter",
            "moderator_id": "10",
            "moderator_display": "mod",
            "reason": "spam",
            "extra": "",
        },
        {
            "type": "warn_manual",
            "timestamp": "2026-02-01T16:00:00+00:00",
            "user_id": "100",
            "user_display": "fighter",
            "moderator_id": "10",
            "moderator_display": "mod",
            "reason": "different reason",
            "extra": "",
        },
    ]

    items = case_timeline_core.build_case_timeline(warns, events, "100")
    kinds = [i["kind"] for i in items]
    assert kinds.count("warn") == 1
    assert kinds.count("warn_manual") == 1
    assert items[0]["kind"] == "warn_manual"
    assert items[0]["reason"] == "different reason"
    assert items[1]["id"] == "warn:7"


def test_build_case_timeline_respects_limit():
    warns = [
        {
            "id": i,
            "reason": f"r{i}",
            "moderator_id": None,
            "source": "manual",
            "created_at": f"2026-01-{i:02d}T00:00:00+00:00",
            "expires_at": None,
            "removed": False,
            "removed_by": None,
            "removed_at": None,
        }
        for i in range(1, 6)
    ]
    items = case_timeline_core.build_case_timeline(warns, [], 1, limit=3)
    assert len(items) == 3
    assert items[0]["meta"]["warn_id"] == 5


def test_serialize_timeline_user():
    class U:
        id = 42
        name = "alice"
        display_name = "Alice"
        display_avatar = type("A", (), {"url": "https://cdn.example/a.png"})()

    assert case_timeline_core.serialize_timeline_user(U()) == {
        "id": "42",
        "username": "alice",
        "display_name": "Alice",
        "avatar": "https://cdn.example/a.png",
    }
