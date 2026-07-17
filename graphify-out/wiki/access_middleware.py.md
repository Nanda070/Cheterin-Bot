# access_middleware.py

> 11 nodes

## Key Concepts

- **access_middleware.py** (30 connections) — `dashboard/backend/access_middleware.py`
- **require_dashboard_access()** (26 connections) — `dashboard/backend/access_middleware.py`
- **voice_stats.py** (6 connections) — `dashboard/backend/routes/voice_stats.py`
- **require_super_admin()** (5 connections) — `dashboard/backend/access_middleware.py`
- **audit.py** (5 connections) — `dashboard/backend/routes/audit.py`
- **superadmin.py** (4 connections) — `dashboard/backend/routes/superadmin.py`
- **superadmin_guilds()** (3 connections) — `dashboard/backend/routes/superadmin.py`
- **Guard an aiohttp handler with the Phase 1 session -> member -> role check.** (1 connections) — `dashboard/backend/access_middleware.py`
- **Гейт для списка серверов бота — намеренно хардкод-роль, см. access.py.** (1 connections) — `dashboard/backend/access_middleware.py`
- **Request** (1 connections)
- **Response** (1 connections)

## Relationships

- [test_access.py](test_access.py.md) (5 shared connections)
- [resolve_guild_member()](resolve_guild_member%28%29.md) (4 shared connections)
- [Supply Module](Supply_Module.md) (3 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (3 shared connections)
- [Audit Log & Stats DB](Audit_Log_%26_Stats_DB.md) (3 shared connections)
- [auto_roles.py](auto_roles.py.md) (2 shared connections)
- [Tournament Brackets](Tournament_Brackets.md) (2 shared connections)
- [config.py](config.py.md) (2 shared connections)
- [Embed Builder Routes](Embed_Builder_Routes.md) (2 shared connections)
- [events.py](events.py.md) (2 shared connections)
- [family.py](family.py.md) (2 shared connections)
- [Feedback Cases](Feedback_Cases.md) (2 shared connections)

## Source Files

- `dashboard/backend/access_middleware.py`
- `dashboard/backend/routes/audit.py`
- `dashboard/backend/routes/superadmin.py`
- `dashboard/backend/routes/voice_stats.py`

## Audit Trail

- EXTRACTED: 83 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*