# Mafia DB Tests

> 43 nodes

## Key Concepts

- **mafia_db.py** (37 connections) — `mafia_db.py`
- **connect()** (29 connections) — `mafia_db.py`
- **test_mafia_db.py** (18 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **_make_game()** (17 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **add_player()** (9 connections) — `mafia_db.py`
- **upsert_night_action()** (8 connections) — `mafia_db.py`
- **create_game()** (7 connections) — `mafia_db.py`
- **upsert_day_vote()** (7 connections) — `mafia_db.py`
- **test_list_alive_players_excludes_eliminated()** (6 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_assign_player_role_and_get_by_token()** (6 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **_now()** (6 connections) — `mafia_db.py`
- **get_player()** (6 connections) — `mafia_db.py`
- **test_get_game_by_lobby_and_vote_message()** (5 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_remove_player()** (5 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_upsert_night_action_overwrites()** (5 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_set_night_action_result()** (5 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **get_night_action()** (5 connections) — `mafia_db.py`
- **get_night_actions()** (5 connections) — `mafia_db.py`
- **test_get_active_game_in_channel_filters_by_status()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_list_active_games_excludes_finished_and_cancelled()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_add_player_rejects_duplicate()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_get_night_actions_filters_by_role()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_upsert_day_vote_overwrites()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_get_day_vote_single_row()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- **test_round_events_roundtrip()** (4 connections) — `dashboard/backend/tests/test_mafia_db.py`
- *... and 18 more nodes in this community*

## Relationships

- [mafia.py](mafia.py.md) (20 shared connections)
- [Mafia Public Route Tests](Mafia_Public_Route_Tests.md) (17 shared connections)
- [test_mafia_routes.py](test_mafia_routes.py.md) (6 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)
- [Mafia Discord Cog](Mafia_Discord_Cog.md) (1 shared connections)

## Source Files

- `dashboard/backend/tests/test_mafia_db.py`
- `mafia_db.py`

## Audit Trail

- EXTRACTED: 270 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*