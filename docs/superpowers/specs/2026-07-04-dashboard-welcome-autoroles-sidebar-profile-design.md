# Dashboard: Sidebar Profile Block, Welcome Toggles, Auto-Roles — Design

## Context

The user shared reference screenshots of a third-party Discord bot dashboard (ProBot) and asked to port a subset of its structure/functionality into this dashboard. After clarifying scope, this covers three independent pieces:

1. A sidebar profile block (avatar + username), mirroring ProBot's server-branding block but showing the logged-in user instead.
2. A "Welcome & Goodbye"-inspired page ("Приветствие и прощание") adding two toggles to the bot's existing, currently-unconditional join messages: whether to post in the configured channel, and whether to DM the new member.
3. An "Auto Roles"-inspired page ("Авто-роли") — a genuinely new bot capability: automatically granting one or more roles to every new member on join.

Everything else visible in the reference screenshots (Server Settings, Embed Messages, Get Premium, Utility, Auto Responder, Leveling System, Colors, Starboard, Temporary Channels, Moderation, Logs, Self-Assignable Roles, Automod, and everything marked "Premium"/"New") is explicitly out of scope. The reference's extra Welcome & Goodbye toggles (send-image-on-join, goodbye-message-on-leave) and Auto Roles' separate bot-role list are also explicitly out of scope, confirmed with the user during brainstorming.

## Sidebar profile block

A new block at the top of `DashboardShell.tsx`'s `<aside>`, above the existing `SECTIONS` nav list: the logged-in user's avatar (or a fallback initial circle, matching the existing header dropdown's fallback pattern) and username, read from the same `useAuth()` hook already used by the header dropdown. This is purely additive — the header's existing avatar+username dropdown (with the "Выйти" logout item) is untouched.

## New nav entries

Two new entries added to `DashboardShell.tsx`'s `SECTIONS` array: "Приветствие и прощание" → `/welcome`, "Авто-роли" → `/auto-roles`.

## Settings storage

Both features are simple settings and reuse `bot_config.py`'s existing generic `load_config()`/`save_config()`/`get(key, default)` (built in Phase 6) rather than a new parallel config system. New keys are read/written directly by name — they don't need to be added to `CONFIG_KEYS`/`LIST_KEYS`, since that list only governs the one-time env-var migration for the original 16 settings, and these three keys never existed as env vars:

- `WELCOME_CHANNEL_ENABLED` (bool, default `true`) — preserves the bot's current always-on channel-message behavior until explicitly turned off.
- `WELCOME_DM_ENABLED` (bool, default `true`) — same reasoning for the DM.
- `AUTO_ROLE_IDS` (list of role-ID strings, default `[]`) — brand-new capability, inert until configured.

The channel itself stays configured on the existing Конфигурация page (`WELCOME_CHANNEL_ID`) — the new toggle only gates whether a send happens into that already-configured channel; it does not duplicate the channel picker.

## Bot-side changes (`welcome.py`)

In `on_member_join`:
- The existing channel-send block (currently unconditional whenever `WELCOME_CHANNEL_ID` is set) is wrapped in `if bot_config.get("WELCOME_CHANNEL_ENABLED", True):`.
- The existing DM-send block (currently unconditional) is wrapped in `if bot_config.get("WELCOME_DM_ENABLED", True):` — when disabled, `dm_sent` stays `False` and the existing DM-log embed still posts (reporting "not sent because disabled" is not distinguished from "Discord blocked it"; both surface as the same "❌ Отказано" status, since the log's purpose is auditing delivery, not diagnosing why).
- A new block grants auto-roles: if `bot_config.get("AUTO_ROLE_IDS", [])` is non-empty, resolve each ID via `guild.get_role(...)` (skipping any that no longer exist), and call `member.add_roles(*roles, reason="Авто-роль при входе")` for the resolved set, swallowing `discord.Forbidden` the same way the rest of this file already does for permission failures.

No automated tests for these `on_member_join` changes — event-listener cog code has zero pytest coverage anywhere in this project (no `FakeInteraction`/event-simulation harness exists). Verified via manual line-by-line diff review against the pre-change source, the same method used for every prior change to this class of code (`spam.py`, `tempban.py`).

## New dashboard pages

- **`Welcome.tsx`** ("Приветствие и прощание", route `/welcome`): two toggles — "Отправлять приветствие в канал" and "Отправлять приветствие в личные сообщения" — with a short note that the channel itself is chosen on the Конфигурация page. Backed by a new `dashboard/backend/routes/welcome.py`: `GET /api/welcome-settings` returns `{channel_enabled, dm_enabled}`; `PUT /api/welcome-settings` updates both.
- **`AutoRoles.tsx`** ("Авто-роли", route `/auto-roles`): a checkbox list of the server's roles (reusing the existing checkbox-list pattern already used on `Config.tsx`/`FeedbackCategories.tsx`), saving the selected set as `AUTO_ROLE_IDS`. Backed by a new `dashboard/backend/routes/auto_roles.py`: `GET /api/auto-roles` returns `{role_ids: [...]}`; `PUT /api/auto-roles` validates and saves the selected role IDs, reusing the existing role-assignability check pattern (`_is_role_assignable`: not `@everyone`, not managed, below the bot's own top role) already established in `dashboard/backend/routes/moderation.py`/`embed_builder.py`.

Both new routes are gated by the existing `require_dashboard_access` decorator, matching every other dashboard route.

## Scope

New files: `dashboard/backend/routes/welcome.py`, `dashboard/backend/routes/auto_roles.py`, `dashboard/frontend/src/pages/Welcome.tsx`, `dashboard/frontend/src/pages/AutoRoles.tsx`. Modified: `welcome.py` (root, bot-side), `dashboard/frontend/src/pages/DashboardShell.tsx` (profile block + nav entries), `dashboard/frontend/src/App.tsx` (routes), `dashboard/frontend/src/api/client.ts` (new types + functions). No changes to `bot_config.py` itself (its existing generic functions are reused as-is), no changes to the existing Конфигурация page, no changes to `config.py`'s route (the new settings are exposed via their own dedicated routes, not the generic Config CRUD).

## Testing

- Backend: unit/route tests for `GET`/`PUT /api/welcome-settings` (defaults, auth-gating, persistence) and `GET`/`PUT /api/auto-roles` (defaults, auth-gating, role-assignability validation, persistence).
- Frontend: tests for `Welcome.tsx` (renders current toggle state, saves changes) and `AutoRoles.tsx` (renders role checkboxes, saves selection), plus the sidebar profile block (renders avatar/username) and the two new nav entries navigating correctly.
- `welcome.py`'s bot-side changes: manual line-by-line diff review only, per this project's standing convention for event-listener cog code.
