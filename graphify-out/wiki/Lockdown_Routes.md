# Lockdown Routes

> 34 nodes

## Key Concepts

- **test_lockdown_core.py** (11 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **lockdown_core.py** (11 connections) — `lockdown_core.py`
- **lockdown.py** (8 connections) — `dashboard/backend/routes/lockdown.py`
- **activate_antispam()** (8 connections) — `lockdown_core.py`
- **lockdown_activate()** (7 connections) — `dashboard/backend/routes/lockdown.py`
- **Lockdown** (7 connections) — `lockdown.py`
- **_role()** (6 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **test_deactivate_restores_from_backup()** (6 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **.antispam()** (6 connections) — `lockdown.py`
- **deactivate_antispam()** (6 connections) — `lockdown_core.py`
- **lockdown_deactivate()** (5 connections) — `dashboard/backend/routes/lockdown.py`
- **test_activate_strips_permissions_and_saves_backup()** (5 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **antispam_status()** (5 connections) — `lockdown_core.py`
- **lockdown_status()** (4 connections) — `dashboard/backend/routes/lockdown.py`
- **test_activate_respects_exempts()** (4 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **test_activate_collects_errors_and_continues()** (4 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **Interaction** (4 connections)
- **._activate()** (4 connections) — `lockdown.py`
- **._deactivate()** (4 connections) — `lockdown.py`
- **load_backup()** (4 connections) — `lockdown_core.py`
- **_log()** (3 connections) — `dashboard/backend/routes/lockdown.py`
- **Request** (3 connections)
- **Response** (3 connections)
- **test_deactivate_without_backup_returns_none()** (3 connections) — `dashboard/backend/tests/test_lockdown_core.py`
- **lockdown.py** (3 connections) — `lockdown.py`
- *... and 9 more nodes in this community*

## Relationships

- [Test Fake Bot](Test_Fake_Bot.md) (6 shared connections)
- [Mass Role Assignment](Mass_Role_Assignment.md) (4 shared connections)
- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Test Fake Channels](Test_Fake_Channels.md) (1 shared connections)

## Source Files

- `dashboard/backend/routes/lockdown.py`
- `dashboard/backend/tests/test_lockdown_core.py`
- `lockdown.py`
- `lockdown_core.py`

## Audit Trail

- EXTRACTED: 151 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*