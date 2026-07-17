# Dashboard App Bootstrap

> 89 nodes

## Key Concepts

- **load_dashboard_config()** (23 connections) — `dashboard/backend/config.py`
- **test_audit.py** (21 connections) — `dashboard/backend/tests/test_audit.py`
- **test_auth.py** (21 connections) — `dashboard/backend/tests/test_auth.py`
- **create_app()** (20 connections) — `dashboard/backend/app.py`
- **test_app.py** (16 connections) — `dashboard/backend/tests/test_app.py`
- **app.py** (16 connections) — `dashboard/backend/app.py`
- **FakeGuild** (14 connections) — `dashboard/backend/tests/test_auth.py`
- **FakeBot** (13 connections) — `dashboard/backend/tests/test_app.py`
- **FakeBot** (13 connections) — `dashboard/backend/tests/test_auth.py`
- **start_dashboard()** (13 connections) — `dashboard/backend/app.py`
- **_NullHttpSession** (12 connections) — `dashboard/backend/tests/test_auth.py`
- **test_config.py** (12 connections) — `dashboard/backend/tests/test_config.py`
- **make_app()** (11 connections) — `dashboard/backend/tests/test_auth.py`
- **build_app()** (10 connections) — `dashboard/backend/tests/test_audit.py`
- **DashboardConfig** (9 connections) — `dashboard/backend/config.py`
- **FakeMember** (9 connections) — `dashboard/backend/tests/test_auth.py`
- **ConfigError** (8 connections) — `dashboard/backend/config.py`
- **main.py** (8 connections) — `main.py`
- **setup_session()** (7 connections) — `dashboard/backend/session.py`
- **audit_middleware()** (7 connections) — `dashboard/backend/audit_middleware.py`
- **config.py** (6 connections) — `dashboard/backend/config.py`
- **session.py** (6 connections) — `dashboard/backend/session.py`
- **derive_fernet_key()** (6 connections) — `dashboard/backend/session.py`
- **test_callback_denies_when_role_missing()** (6 connections) — `dashboard/backend/tests/test_auth.py`
- **test_callback_succeeds_and_me_returns_user()** (6 connections) — `dashboard/backend/tests/test_auth.py`
- *... and 64 more nodes in this community*

## Relationships

- [Automod Route Tests](Automod_Route_Tests.md) (9 shared connections)
- [test_auto_roles_routes.py](test_auto_roles_routes.py.md) (4 shared connections)
- [Test Fake Bot](Test_Fake_Bot.md) (4 shared connections)
- [Audit Log & Stats DB](Audit_Log_%26_Stats_DB.md) (4 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (3 shared connections)
- [access_middleware.py](access_middleware.py.md) (3 shared connections)
- [Game Settings & Bunker DB](Game_Settings_%26_Bunker_DB.md) (3 shared connections)
- [Automod Cog](Automod_Cog.md) (3 shared connections)
- [Test Fake Members](Test_Fake_Members.md) (2 shared connections)
- [auth.py](auth.py.md) (1 shared connections)
- [Family DB Tests](Family_DB_Tests.md) (1 shared connections)
- [Automod Filter Core](Automod_Filter_Core.md) (1 shared connections)

## Source Files

- `dashboard/backend/app.py`
- `dashboard/backend/audit_middleware.py`
- `dashboard/backend/config.py`
- `dashboard/backend/session.py`
- `dashboard/backend/tests/test_app.py`
- `dashboard/backend/tests/test_audit.py`
- `dashboard/backend/tests/test_auth.py`
- `dashboard/backend/tests/test_config.py`
- `dashboard/backend/tests/test_session.py`
- `main.py`

## Audit Trail

- EXTRACTED: 440 (94%)
- INFERRED: 26 (6%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*