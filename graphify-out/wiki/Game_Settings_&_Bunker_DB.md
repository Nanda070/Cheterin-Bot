# Game Settings & Bunker DB

> 117 nodes

## Key Concepts

- **bunker_db.py** (40 connections) — `bunker_db.py`
- **connect()** (30 connections) — `bunker_db.py`
- **test_bunker_routes.py** (27 connections) — `dashboard/backend/tests/test_bunker_routes.py`
- **bunker.py** (22 connections) — `dashboard/backend/routes/bunker.py`
- **test_bunker_db.py** (22 connections) — `dashboard/backend/tests/test_bunker_db.py`
- **test_bunker_cog.py** (20 connections) — `dashboard/backend/tests/test_bunker_cog.py`
- **_make_game()** (20 connections) — `dashboard/backend/tests/test_bunker_db.py`
- **build()** (20 connections) — `dashboard/backend/tests/test_bunker_routes.py`
- **get_game()** (18 connections) — `bunker_db.py`
- **update_game()** (16 connections) — `bunker_db.py`
- **add_player()** (15 connections) — `bunker_db.py`
- **get_player()** (15 connections) — `bunker_db.py`
- **create_game()** (14 connections) — `bunker_db.py`
- **build()** (12 connections) — `dashboard/backend/tests/test_bunker_cog.py`
- **get_settings()** (11 connections) — `bunker_core.py`
- **Request** (11 connections)
- **Response** (11 connections)
- **bunker_public_state()** (11 connections) — `dashboard/backend/routes/bunker.py`
- **test_full_round_vote_ends_game_at_capacity()** (10 connections) — `dashboard/backend/tests/test_bunker_cog.py`
- **test_game_detail_includes_players_and_announcements()** (10 connections) — `dashboard/backend/tests/test_bunker_routes.py`
- **init()** (9 connections) — `bunker_db.py`
- **list_alive_players()** (9 connections) — `bunker_db.py`
- **assign_character()** (9 connections) — `bunker_db.py`
- **upsert_vote()** (9 connections) — `bunker_db.py`
- **bunker_game_detail()** (9 connections) — `dashboard/backend/routes/bunker.py`
- *... and 92 more nodes in this community*

## Relationships

- [Test Fake Members](Test_Fake_Members.md) (27 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (14 shared connections)
- [Bunker Game Core](Bunker_Game_Core.md) (9 shared connections)
- [Test Fake Bot](Test_Fake_Bot.md) (8 shared connections)
- [Bunker Discord Cog](Bunker_Discord_Cog.md) (6 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (4 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (3 shared connections)
- [Feedback Panel Tests](Feedback_Panel_Tests.md) (2 shared connections)
- [Bot Entrypoint & Auth Middleware](Bot_Entrypoint_%26_Auth_Middleware.md) (1 shared connections)
- [Supply Module](Supply_Module.md) (1 shared connections)

## Source Files

- `bunker_core.py`
- `bunker_db.py`
- `dashboard/backend/routes/bunker.py`
- `dashboard/backend/tests/test_bunker_cog.py`
- `dashboard/backend/tests/test_bunker_core.py`
- `dashboard/backend/tests/test_bunker_db.py`
- `dashboard/backend/tests/test_bunker_public_routes.py`
- `dashboard/backend/tests/test_bunker_routes.py`

## Audit Trail

- EXTRACTED: 780 (100%)
- INFERRED: 1 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*