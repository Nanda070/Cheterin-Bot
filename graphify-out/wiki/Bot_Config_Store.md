# Bot Config Store

> 23 nodes

## Key Concepts

- **bot_config.py** (21 connections) — `bot_config.py`
- **load_config()** (17 connections) — `bot_config.py`
- **save_config()** (13 connections) — `bot_config.py`
- **get()** (12 connections) — `bot_config.py`
- **test_bot_config.py** (11 connections) — `dashboard/backend/tests/test_bot_config.py`
- **migrate_from_env_if_needed()** (6 connections) — `bot_config.py`
- **welcome.py** (6 connections) — `dashboard/backend/routes/welcome.py`
- **test_put_config_preserves_foreign_keys()** (6 connections) — `dashboard/backend/tests/test_config_routes.py`
- **update_welcome_settings()** (5 connections) — `dashboard/backend/routes/welcome.py`
- **get_welcome_settings()** (4 connections) — `dashboard/backend/routes/welcome.py`
- **test_migrate_from_env_if_needed_skips_if_file_exists()** (4 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_save_then_load_roundtrips()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_get_returns_default_when_key_missing()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_get_returns_stored_value()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_migrate_from_env_if_needed_creates_file_from_env()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_migrate_from_env_if_needed_defaults_missing_keys_to_empty()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_migrate_from_env_if_needed_parses_list_keys_from_comma_separated_env()** (3 connections) — `dashboard/backend/tests/test_bot_config.py`
- **Request** (2 connections)
- **Response** (2 connections)
- **test_load_config_returns_empty_dict_when_file_missing()** (2 connections) — `dashboard/backend/tests/test_bot_config.py`
- **test_load_config_reads_fresh_after_external_write()** (2 connections) — `dashboard/backend/tests/test_bot_config.py`
- **isolated_config_file()** (1 connections) — `dashboard/backend/tests/test_bot_config.py`
- **PUT /api/config не должен затирать ключи других разделов (авто-роли, приветствия** (1 connections) — `dashboard/backend/tests/test_config_routes.py`

## Relationships

- [test_config_routes.py](test_config_routes.py.md) (5 shared connections)
- [Automod Route Tests](Automod_Route_Tests.md) (5 shared connections)
- [auto_roles.py](auto_roles.py.md) (4 shared connections)
- [config.py](config.py.md) (4 shared connections)
- [test_auto_roles_routes.py](test_auto_roles_routes.py.md) (3 shared connections)
- [Supply Module](Supply_Module.md) (3 shared connections)
- [voice_rooms.py](voice_rooms.py.md) (3 shared connections)
- [Button Forms](Button_Forms.md) (2 shared connections)
- [voice_logs.py](voice_logs.py.md) (2 shared connections)
- [access_middleware.py](access_middleware.py.md) (2 shared connections)
- [Automod Cog](Automod_Cog.md) (1 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)

## Source Files

- `bot_config.py`
- `dashboard/backend/routes/welcome.py`
- `dashboard/backend/tests/test_bot_config.py`
- `dashboard/backend/tests/test_config_routes.py`

## Audit Trail

- EXTRACTED: 133 (100%)
- INFERRED: 0 (0%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*