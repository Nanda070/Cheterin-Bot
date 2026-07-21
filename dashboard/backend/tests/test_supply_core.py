import supply_core

G = 404
G2 = 777


def test_is_valid_time():
    assert supply_core.is_valid_time("15:10")
    assert supply_core.is_valid_time("00:00")
    assert supply_core.is_valid_time("23:59")
    assert not supply_core.is_valid_time("24:00")
    assert not supply_core.is_valid_time("5:10")
    assert not supply_core.is_valid_time("15:60")
    assert not supply_core.is_valid_time("abc")


def test_create_and_get_supply():
    supply = supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    assert supply["id"] == "1"
    assert supply["status"] == "active"
    assert supply["limit"] == 5
    assert supply["guild_id"] == str(G)
    assert supply_core.get_supply(G, "1")["opponent"] == "Ballas"

    second = supply_core.create_supply(G, 2, "Vagos", 3, "16:00")
    assert second["id"] == "2"
    assert len(supply_core.list_active(G)) == 2


def test_supplies_isolated_per_guild():
    supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    other = supply_core.create_supply(G2, 1, "Vagos", 5, "15:10")
    # у каждого сервера своя последовательность id, начиная с 1
    assert other["id"] == "1"
    assert len(supply_core.list_active(G)) == 1
    assert len(supply_core.list_active(G2)) == 1
    assert supply_core.get_supply(G2, "1")["opponent"] == "Vagos"
    # сбор одного сервера не виден другому
    assert supply_core.get_supply(G2, "1")["opponent"] != supply_core.get_supply(G, "1")["opponent"]


def test_join_until_limit_then_reserve():
    supply = supply_core.create_supply(G, 1, "Ballas", 2, "15:10")
    assert supply_core.join_supply(G, supply["id"], 100) == "joined"
    assert supply_core.join_supply(G, supply["id"], 100) == "already"
    assert supply_core.join_supply(G, supply["id"], 101) == "joined"
    assert supply_core.join_supply(G, supply["id"], 102) == "reserve"

    stored = supply_core.get_supply(G, supply["id"])
    assert stored["participants"] == ["100", "101"]
    assert stored["reserve"] == ["102"]


def test_leave_promotes_from_reserve():
    supply = supply_core.create_supply(G, 1, "Ballas", 1, "15:10")
    supply_core.join_supply(G, supply["id"], 100)
    supply_core.join_supply(G, supply["id"], 101)

    result, promoted = supply_core.leave_supply(G, supply["id"], 100)
    assert result == "left"
    assert promoted == "101"

    stored = supply_core.get_supply(G, supply["id"])
    assert stored["participants"] == ["101"]
    assert stored["reserve"] == []


def test_leave_from_reserve_and_not_in_list():
    supply = supply_core.create_supply(G, 1, "Ballas", 1, "15:10")
    supply_core.join_supply(G, supply["id"], 100)
    supply_core.join_supply(G, supply["id"], 101)

    result, promoted = supply_core.leave_supply(G, supply["id"], 101)
    assert result == "left"
    assert promoted is None

    result, _ = supply_core.leave_supply(G, supply["id"], 999)
    assert result == "not_in_list"


def test_get_supply_by_message_scoped_per_guild():
    supply = supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    supply_core.update_supply(G, supply["id"], message_id="555")
    assert supply_core.get_supply_by_message(G, 555)["id"] == supply["id"]
    assert supply_core.get_supply_by_message(G, 111) is None
    # другой сервер не находит чужое сообщение
    assert supply_core.get_supply_by_message(G2, 555) is None


def test_close_supply_updates_stats_and_history():
    supply = supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    supply_core.join_supply(G, supply["id"], 100)
    supply_core.join_supply(G, supply["id"], 101)

    closed = supply_core.close_supply(G, supply["id"], status="finished")
    assert closed["status"] == "finished"
    assert closed["closed_at"] is not None

    assert supply_core.list_active(G) == []
    history = supply_core.list_history(G)
    assert len(history) == 1

    stats = supply_core.get_stats(G)
    assert {"user_id": "100", "count": 1} in stats
    assert {"user_id": "101", "count": 1} in stats

    # Повторное закрытие невозможно
    assert supply_core.close_supply(G, supply["id"]) is None


def test_cancel_does_not_update_stats():
    supply = supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    supply_core.join_supply(G, supply["id"], 100)
    supply_core.close_supply(G, supply["id"], status="cancelled")
    assert supply_core.get_stats(G) == []


def test_join_closed_supply():
    supply = supply_core.create_supply(G, 1, "Ballas", 5, "15:10")
    supply_core.close_supply(G, supply["id"])
    assert supply_core.join_supply(G, supply["id"], 100) == "closed"
    result, _ = supply_core.leave_supply(G, supply["id"], 100)
    assert result == "closed"
