# Audit Log & Stats DB

> 30 nodes

## Key Concepts

- **stats_db.py** (31 connections) — `stats_db.py`
- **connect()** (22 connections) — `stats_db.py`
- **init()** (6 connections) — `stats_db.py`
- **audit_list()** (4 connections) — `dashboard/backend/routes/audit.py`
- **xp_all_members()** (4 connections) — `stats_db.py`
- **xp_set_xp()** (3 connections) — `stats_db.py`
- **xp_reset_member()** (3 connections) — `stats_db.py`
- **xp_member_count()** (3 connections) — `stats_db.py`
- **xp_rank_of()** (3 connections) — `stats_db.py`
- **voice_sessions_since()** (3 connections) — `stats_db.py`
- **voice_sessions_prune()** (3 connections) — `stats_db.py`
- **audit_count()** (3 connections) — `stats_db.py`
- **isolated_db()** (2 connections) — `dashboard/backend/tests/test_audit.py`
- **get_db_path()** (2 connections) — `stats_db.py`
- **xp_get_member()** (2 connections) — `stats_db.py`
- **xp_upsert_member()** (2 connections) — `stats_db.py`
- **xp_add_voice()** (2 connections) — `stats_db.py`
- **xp_set_level()** (2 connections) — `stats_db.py`
- **xp_reset_all()** (2 connections) — `stats_db.py`
- **xp_leaderboard()** (2 connections) — `stats_db.py`
- **voice_session_add()** (2 connections) — `stats_db.py`
- **audit_add()** (2 connections) — `stats_db.py`
- **audit_list()** (2 connections) — `stats_db.py`
- **Request** (1 connections)
- **Response** (1 connections)
- *... and 5 more nodes in this community*

## Relationships

- [xp.py](xp.py.md) (5 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (4 shared connections)
- [test_xp_routes.py](test_xp_routes.py.md) (4 shared connections)
- [access_middleware.py](access_middleware.py.md) (3 shared connections)
- [VoiceTracker](VoiceTracker.md) (2 shared connections)
- [XPCog](XPCog.md) (2 shared connections)
- [format_voice_time()](format_voice_time%28%29.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/audit.py`
- `dashboard/backend/tests/test_audit.py`
- `stats_db.py`

## Audit Trail

- EXTRACTED: 117 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*