# auth.py

> 21 nodes

## Key Concepts

- **auth.py** (14 connections) — `dashboard/backend/auth.py`
- **test_discord_oauth.py** (11 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **callback()** (8 connections) — `dashboard/backend/auth.py`
- **DiscordOAuthError** (8 connections) — `dashboard/backend/discord_oauth.py`
- **exchange_code_for_token()** (8 connections) — `dashboard/backend/discord_oauth.py`
- **fetch_discord_identity()** (8 connections) — `dashboard/backend/discord_oauth.py`
- **me()** (6 connections) — `dashboard/backend/auth.py`
- **discord_oauth.py** (5 connections) — `dashboard/backend/discord_oauth.py`
- **Request** (4 connections)
- **Response** (4 connections)
- **login()** (3 connections) — `dashboard/backend/auth.py`
- **logout()** (3 connections) — `dashboard/backend/auth.py`
- **stub_discord_server()** (3 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **test_exchange_code_for_token_failure_raises()** (3 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **test_fetch_discord_identity_failure_raises()** (3 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **ClientSession** (2 connections)
- **fake_token_endpoint()** (2 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **fake_identity_endpoint()** (2 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **test_exchange_code_for_token_success()** (2 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **test_fetch_discord_identity_success()** (2 connections) — `dashboard/backend/tests/test_discord_oauth.py`
- **Exception** (1 connections)

## Relationships

- [test_access.py](test_access.py.md) (6 shared connections)
- [resolve_guild_member()](resolve_guild_member%28%29.md) (4 shared connections)
- [Dashboard App Bootstrap](Dashboard_App_Bootstrap.md) (1 shared connections)
- [Bot Entrypoint & Auth Middleware](Bot_Entrypoint_%26_Auth_Middleware.md) (1 shared connections)

## Source Files

- `dashboard/backend/auth.py`
- `dashboard/backend/discord_oauth.py`
- `dashboard/backend/tests/test_discord_oauth.py`

## Audit Trail

- EXTRACTED: 94 (92%)
- INFERRED: 8 (8%)
- AMBIGUOUS: 0 (0%)

---

*Part of the graphify knowledge wiki. See [index](index.md) to navigate.*