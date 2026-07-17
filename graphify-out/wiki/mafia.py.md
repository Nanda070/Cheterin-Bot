# mafia.py

> 15 nodes

## Key Concepts

- **mafia.py** (14 connections) — `dashboard/backend/routes/mafia.py`
- **mafia_public_state()** (12 connections) — `dashboard/backend/routes/mafia.py`
- **get_game()** (11 connections) — `mafia_db.py`
- **list_alive_players()** (8 connections) — `mafia_db.py`
- **mafia_public_action()** (7 connections) — `dashboard/backend/routes/mafia.py`
- **mafia_public_vote()** (7 connections) — `dashboard/backend/routes/mafia.py`
- **Request** (6 connections)
- **Response** (6 connections)
- **get_player_by_token()** (6 connections) — `mafia_db.py`
- **mafia_games_list()** (5 connections) — `dashboard/backend/routes/mafia.py`
- **_serialize_game_summary()** (4 connections) — `dashboard/backend/routes/mafia.py`
- **mafia_put()** (4 connections) — `dashboard/backend/routes/mafia.py`
- **mafia_get()** (3 connections) — `dashboard/backend/routes/mafia.py`
- **_is_id()** (2 connections) — `dashboard/backend/routes/mafia.py`
- **_display_name()** (2 connections) — `dashboard/backend/routes/mafia.py`

## Relationships

- [Mafia DB Tests](Mafia_DB_Tests.md) (20 shared connections)
- [Mafia Public Route Tests](Mafia_Public_Route_Tests.md) (5 shared connections)
- [test_mafia_routes.py](test_mafia_routes.py.md) (1 shared connections)
- [Mafia Core Tests](Mafia_Core_Tests.md) (1 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)
- [Mafia Discord Cog](Mafia_Discord_Cog.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/mafia.py`
- `mafia_db.py`

## Audit Trail

- EXTRACTED: 97 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*