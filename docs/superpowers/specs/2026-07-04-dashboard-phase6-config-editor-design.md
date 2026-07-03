# Phase 6: Dashboard Config Editor — Design

## Context

The bot currently reads ~16 configuration values via `os.getenv(...)` scattered across `main.py`, `spam.py`, `welcome.py`, `tempban.py`, `memobb.py`, and `button.py`: channel IDs, role IDs, two comma-separated ID lists, and two URLs. Every change requires manually editing `.env` and restarting the bot. This phase moves these values to a dashboard-editable JSON config, following the same pattern established for `feedback_categories.json`/`reaction_roles.json`/`events_data.json` in earlier phases.

`BOT_TOKEN`, `GUILD_ID`, and the dashboard's own Discord OAuth secrets stay in `.env` — they are structural/secret values, never migrated, never dashboard-editable.

## Storage: `bot_config.py`

A new module, mirroring `feedback_categories.py`'s established shape:

- `load_config() -> dict` / `save_config(data: dict) -> None` — no caching, always read/write fresh from `config.json`.
- `get(key: str, default=None)` — convenience wrapper around `load_config()[key]`, used at every call site that currently does `os.getenv(key, ...)`.
- `migrate_from_env_if_needed()` — called once from `main.py`'s `setup_hook`, before any cog that reads config loads. Unlike `feedback_categories.py`'s all-or-nothing migration (which builds one structured category object), this migration is per-key independent: if `config.json` doesn't exist, it's created with all 16 keys, each read via `os.getenv(KEY, "")` (or `[]` for the two list keys) — whichever env vars happen to be set populate the file; missing ones default to empty rather than blocking the whole migration.

JSON keys are the exact original env var names (e.g. `"LOG_CHANNEL_ID"`, `"SPAM_EXCEPTION_CHANNELS"`) — no renaming, so there's a direct, greppable correspondence between the old `.env` and the new `config.json`.

## The 16 keys, grouped

**Модерация/спам:** `LOG_CHANNEL_ID`, `SPAM_EXCEPTION_CHANNELS` (list), `TEMPBAN_CHANNEL_ID`, `SPAM_LOG_CHANNEL_ID`, `SPAM_LOG_ROLE_ID`

**Приветствия/онбординг:** `WELCOME_CHANNEL_ID`, `INVITE_LOG_CHANNEL_ID`, `ANNOUNCEMENTS_CHANNEL_ID`, `RULES_CHANNEL_ID`, `ROLES_CHANNEL_ID`, `SEARCH_PLAYERS_CHANNEL_ID`

**CTD:** `CTD_ROLE_ID`, `CTD_CHANNEL_ID`

**Кнопки/вебхуки:** `BUTTON_CREATE_ALLOWED_ROLES` (list), `BUTTON_WEBHOOK_URL`

**Прочее:** `SERVER_INVITE_LINK`

## Per-file refactor

Every `os.getenv("KEY")` call in the six affected files is replaced with `bot_config.get("KEY")`. Two call sites currently do `.split(",")` on a comma-separated env string (`spam.py`'s `SPAM_EXCEPTION_CHANNELS`, `button.py`'s `BUTTON_CREATE_ALLOWED_ROLES`) — these become genuine JSON arrays of ID strings in storage, and the parsing simplifies to reading the list directly (`int(x)` conversion still happens only at the Discord API call site, per the project's established convention).

**One deliberate fix bundled in**: `spam.py`'s `Spam.__init__` currently computes `self.exception_channels` once at cog construction time — so even today, a `.env` edit needs a full bot restart to take effect, not just because of the old `os.getenv` pattern but because it's cached on the instance. This moves to reading `bot_config.get("SPAM_EXCEPTION_CHANNELS")` fresh at the point of use (inside whatever method actually checks channel exceptions), matching this project's established "dashboard edits apply live, no bot restart" convention already used everywhere else.

## API

`GET /api/config` — returns all 16 current values (channel/role IDs and list-of-IDs as strings, matching the project's established string-ID convention at the API boundary; underlying storage is unaffected).

`PUT /api/config` — body is the same shape as the GET response (all 16 keys). Validation order: structural first (every provided key has the right type — string for scalars, array of strings for the two list keys; the two URL fields get a basic non-empty/format check, no Discord call), then Discord-existence for every channel/role ID field (`guild.get_channel`/`guild.get_role`, matching `_validate_category_relations`'s established pattern), then permission (`@require_dashboard_access`, already gating the whole handler). A field left blank/`null` is valid (an unconfigured feature) and skips the existence check for that field.

Both routes gated by `require_dashboard_access`.

## Frontend

One new page, "Конфигурация", wiring the existing disabled sidebar placeholder in `DashboardShell.tsx` to a live `/config` route (the exact same pattern Phase 5a used for the "События и голосования" placeholder). Fields grouped into the four sections above, each rendered with the appropriate control: channel IDs as a channel-picker `<select>`, role IDs as a role-picker `<select>`, the two list fields as multi-select checkboxes (reusing the channel/role lists already fetched elsewhere in the dashboard), URLs and the invite link as plain text inputs. A single "Сохранить" button submits the whole form via `PUT /api/config`.

## Testing

- `bot_config.py`: load/save round-trip; a dedicated no-caching regression test (external write via raw file I/O is picked up by `load_config()` without any process restart — same discipline as the Phase 4b/5a cache-removal regression tests); `migrate_from_env_if_needed()` tests covering full-env-present, partial-env-present (missing keys default to empty), and skip-if-file-exists.
- `GET`/`PUT /api/config`: structural-then-Discord-existence validation order (dedicated regression test, matching this project's standing pattern for this exact bug class), auth gate, a round-trip test proving a `PUT` is immediately visible to a subsequent `GET`.
- The six refactored bot-side files (`main.py`, `spam.py`, `welcome.py`, `tempban.py`, `memobb.py`, `button.py`) are event-listener/cog code — this project's standing convention (no `FakeInteraction`/event-simulation pattern exists, none gets invented) means these changes get zero new pytest coverage and are verified by careful, minimal diff reading instead, the same discipline applied to every previous phase's bot-side refactor.
- Frontend: the config page renders all fields grouped correctly, an edit-and-save round-trips through the API client, and validation errors from the route surface in the UI.

## Global constraints (carried over, still binding)

- No caching in `bot_config.py`.
- IDs (and the two list fields' entries) stored/serialized as strings; `int(...)`-conversion only at the exact Discord API call site.
- `BOT_TOKEN`/`GUILD_ID`/dashboard OAuth secrets never migrated, never dashboard-editable, stay in `.env`.
- Both routes gated by `require_dashboard_access`.
- Validation order: structural → Discord-existence → permission, everywhere.
- Never bare `git add -A`/`git add .`.
