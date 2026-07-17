# Bot Entrypoint & Auth Middleware

> 47 nodes

## Key Concepts

- **CTD** (9 connections) — `memobb.py`
- **Multi-Guild Migration Plan (MEE6-level)** (9 connections) — `MULTIGUILD_PLAN.md`
- **ChetBot** (8 connections) — `main.py`
- **Unified settings.db Per-Guild Storage** (7 connections) — `MULTIGUILD_PLAN.md`
- **Phase 2.2: Guild Dimension for Module Data** (6 connections) — `MULTIGUILD_PLAN.md`
- **memobb.py** (5 connections) — `memobb.py`
- **CTDCloseView** (5 connections) — `memobb.py`
- **CTDView** (5 connections) — `memobb.py`
- **Phase 3: RU/EN i18n Infrastructure** (5 connections) — `MULTIGUILD_PLAN.md`
- **.create_ticket()** (4 connections) — `memobb.py`
- **MAIN_GUILD_ID Constant** (4 connections) — `MULTIGUILD_PLAN.md`
- **Phase 2.3: OAuth Guilds Scope and Server Selection** (4 connections) — `MULTIGUILD_PLAN.md`
- **News Relay as Super-Admin Feature** (4 connections) — `MULTIGUILD_PLAN.md`
- **.close_ticket()** (3 connections) — `memobb.py`
- **Interaction** (3 connections)
- **.__init__()** (3 connections) — `memobb.py`
- **.on_ready()** (3 connections) — `memobb.py`
- **.ctd_setup()** (3 connections) — `memobb.py`
- **Phase 2.4: Bot Detached from GUILD_ID** (3 connections) — `MULTIGUILD_PLAN.md`
- **CTD Main-Guild Gate** (3 connections) — `MULTIGUILD_PLAN.md`
- **XP Global-to-Main Migration Decision** (3 connections) — `MULTIGUILD_PLAN.md`
- **.__init__()** (2 connections) — `memobb.py`
- **Button** (2 connections)
- **.__init__()** (2 connections) — `memobb.py`
- **setup()** (2 connections) — `memobb.py`
- *... and 22 more nodes in this community*

## Relationships

- [Bot Config Store](Bot_Config_Store.md) (1 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)
- [Game Settings & Bunker DB](Game_Settings_%26_Bunker_DB.md) (1 shared connections)
- [auth.py](auth.py.md) (1 shared connections)

## Source Files

- `MULTIGUILD_PLAN.md`
- `main.py`
- `memobb.py`

## Audit Trail

- EXTRACTED: 129 (96%)
- INFERRED: 5 (4%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*