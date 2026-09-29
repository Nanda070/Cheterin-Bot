# Cheterin — internal architecture map

> **Internal engineering reference.**  
> **Not published on cheterin.online.**  
> For repository collaborators only. Do not add to React routes, public `pages/docs/`, footer, or aiohttp named static pages.

Canonical file: `docs/ARCHITECTURE.md` (this EN doc). Russian: [`docs/ARCHITECTURE.ru.md`](ARCHITECTURE.ru.md). Public [`README.md`](../README.md). Docs live only under `docs/` (no root stub pointers).

**Lookup shipped** (Sep 2026): SPA `lookup/` + API `lookup-api/`. Not imported and not started from `main.py`. Public: `https://cheterin.online/lookup`. Local run / proxy: `lookup/RUN.md`, `lookup-api/RUN.md`, `lookup-api/PROXY.md`. Operator leftover: CAPTCHA keys; rotate Lookup Discord tokens if ever exposed.

**Process model (current):** bot+dashboard and Lookup API run under **systemd** (`cheterin-bot.service`, `cheterin-lookup.service`). Former tmux sessions `chetmain` / `chetlookup` are legacy. See `deploy/systemd/`.

---

## 1. Identity

| | |
|:---|:---|
| **Product** | **Cheterin** — public multi-guild Discord bot + web dashboard in the **same** OS process |
| **Site / panel** | `https://cheterin.online` |
| **Organization** | Cheterin Group Ø |
| **Languages** | RU default, EN supported (bot `locales/`, panel `chetbot_ui_lang`) |
| **Presence** | `Playing /help • Cheterin` |
| **Prefix** | `command_prefix="!"` declared on `ChetBot`, but **no product prefix commands** — slash / interactions / panel |
| **Repository** | `https://github.com/Nanda070/Cheterin_Bot_Dashboard` |
| **License** | Apache-2.0 (`LICENSE`) |

One bot instead of a utility pile. Settings/data are **isolated by `guild_id`**. Config is browser-first. New guilds: modules **off by default** where `*_core.get_settings` defaults `enabled: False`.

---

## 2. Principles

1. **One bot, many servers** — not one instance per guild.
2. **Per-guild isolation** — `settings.db` key `(guild_id, module)`; SQLite rows carry `guild_id`.
3. **Browser-first config** — admins use the UI; Discord is the runtime for members.
4. **Modules opt-in** for feature modules.
5. **Cores vs cogs** — `*_core.py` = pure logic; cog = Discord I/O; `dashboard/backend/routes` = HTTP + ACL; frontend = UI.
6. **Dashboard does not own game phase machines** — Mafia/Bunker/Customs live in cores/cogs; panel is settings + overrides + public token action pages.
7. **Main guild privilege** — CTD (`memobb`), news-relay, super-admin tied to `MAIN_GUILD_ID` / `GUILD_ID`.
8. **Lookup stays isolated** — never wire Lookup into `main.py` or the bot package incorrectly.

---

## 3. Startup

Entrypoint: `python main.py` → `asyncio.run(main())`.

### 3.1. `ChetBot.setup_hook`

1. `settings_db.init()`
2. Slash i18n translator
3. `settings_migration.migrate_all(main_guild_id)`
4. Env → settings migrations where applicable
5. Load **52 extensions** (`bot.modules.*` — see Russian map §11 for the full ordered list)
6. Slash sync is **not** in `setup_hook` — happens in `on_ready`

### 3.2. `main()`

1. `start_dashboard(bot, main_guild_id)` — aiohttp on the same event loop
2. `bot.start(BOT_TOKEN)`
3. `finally`: dashboard cleanup

**Consequence:** if the bot process dies, the panel dies with it. Lookup is a **separate systemd unit**; restarting `cheterin-bot` does not stop Lookup.

### 3.3. `on_ready`

- Presence `/help • Cheterin`
- One-shot command sync per process (`COMMAND_SYNC_MODE`)

### 3.4. Guild lifecycle

| Event | Action |
|:---|:---|
| `on_guild_join` | mark guild active; optional per-guild sync; welcome embed with dashboard URL |
| `on_guild_remove` | mark inactive — settings **kept** |

---

## 4. Process model

Two OS processes on one Ubuntu host (Oracle). Nginx routes paths; CORS not required for same-host setup.

```
                    nginx  cheterin.online
         /  /about /docs /api/* (panel)     /lookup/*     /api/lookup/*
                    │                            │                │
                    ▼                            ▼                ▼
┌───────────────────────────────────┐   ┌──────────────────────────────┐
│  Process A — python main.py       │   │  Process B — lookup-api      │
│  systemd: cheterin-bot.service    │   │  systemd: cheterin-lookup    │
│  ┌────────────┐  ┌──────────────┐ │   │  aiohttp 127.0.0.1:8090      │
│  │ ChetBot    │◄►│ aiohttp      │ │   │  TokenPool (not BOT_TOKEN)   │
│  │ cogs/tree  │  │ dashboard    │ │   │  static: lookup/dist         │
│  └────────────┘  │ SPA dist     │ │   │  (nginx alias, not main.py)  │
│   shared SQLite  └──────────────┘ │   └──────────────────────────────┘
└───────────────────────────────────┘
        update.sh → git pull, pip (bot + lookup-api), build dashboard + lookup,
                    systemctl restart cheterin-bot + cheterin-lookup
```

- Session cookie: `chetbot_dashboard_session`
- Panel health: `GET /api/health`
- Lookup health: `GET /api/lookup/health` → `ok`, `token_configured`, `token_count`
- Unit files: `deploy/systemd/` (operator installs once; agents do not touch the VPS)

### 4.1. Lookup (shipped, isolated)

| | |
|:---|:---|
| **SPA** | `lookup/` (Vite/React, `basename=/lookup`) |
| **API** | `lookup-api/` (`LOOKUP_DISCORD_TOKENS` preferred, else `LOOKUP_DISCORD_TOKEN`) |
| **TokenPool** | Round-robin; on HTTP 429 rotate immediately; after all tokens exhausted wait `min(Retry-After, 5s)` and retry once |
| **Guardrail** | Never uses `BOT_TOKEN` |
| **Plugins hub** | `/lookup/plugins` + nested tools |
| **DSA** | Home mode `/lookup?mode=dsa` |
| **Catalog** | Operator `lookup-api/plugins.json` |
| **CAPTCHA** | Code present; widget on only when operator sets provider keys |
| **Visual** | Same charcoal-red tokens as the public site |

---

## 5. Directory map

VALORANT-style layout (`bot/`, `docs/`, `scripts/`, `deploy/`), Lookup as a separate tree.

| Path | Purpose |
|:---|:---|
| `main.py` | Entrypoint: bot + dashboard |
| `bot/` | Bot package (`core/`, `modules/*`, `cards/`, `data/`) |
| `locales/ru/`, `locales/en/` | Bot strings |
| `dashboard/backend/` | aiohttp app, auth, routes, tests |
| `dashboard/frontend/` | React 19 + Vite + Tailwind |
| `lookup/` | Lookup SPA |
| `lookup-api/` | Lookup HTTP API + TokenPool |
| `docs/` | Internal architecture maps (EN + RU) |
| `deploy/systemd/` | `cheterin-bot` / `cheterin-lookup` unit files |
| `deploy/nginx-spa.notes.conf` | Path-split notes |
| `scripts/update.sh` + root `update.sh` | Full VPS update (bot + Lookup) |
| `tests/` | Root one-off bot tests |
| `.github/workflows/ci.yml` | pytest + frontend builds on push/PR to `main` |
| `.env` / `.env.example` | Bot/panel secrets template (empty placeholders) |
| `lookup-api/.env` | Lookup secrets (separate) |

Runtime SQLite / `card_bgs/` / `banner_rotation_assets/` resolve relative to **repo CWD** (WorkingDirectory of the bot unit).

---

## 6. Data layer (summary)

- **`settings.db`** — `module_settings` PK `(guild_id, module)`, JSON `data`
- Per-feature SQLite DBs (`*.db`) with `guild_id` columns where needed
- Module keys live in `*_core.MODULE_NAME` / related settings getters — full table in [`ARCHITECTURE.ru.md`](ARCHITECTURE.ru.md) §6.2

---

## 7. Layer pattern

| Layer | Responsibility |
|:---|:---|
| `*_core.py` | Pure logic, DB, settings |
| cog | Discord slash / listeners / views |
| `dashboard/backend/routes` | HTTP + ACL |
| frontend page | UI |

---

## 8. Auth and ACL

- Discord OAuth2 for the panel
- `has_dashboard_access` / `require_dashboard_access`
- Fernet-backed session cookie
- Super-admin / main-guild extras for CTD and news

---

## 9. i18n and timezone

- Bot: `locales/` + slash translator
- Panel / Lookup UI: `chetbot_ui_lang` (RU/EN)
- Schedules: **`timezone_core`** (IANA) — no new hardcoded MSK

---

## 10. Slash sync

Controlled by `COMMAND_SYNC_MODE` (`per_guild` / `global`) and optional hide-disabled / clear-global flags. Sync runs after ready, not during `setup_hook`.

---

## 11. Cog catalog

Ordered `load_extension` list is maintained in `main.py` (~52 extensions under `bot.modules.*`). Treat `main.py` as source of truth; the long Russian table in [`ARCHITECTURE.ru.md`](ARCHITECTURE.ru.md) §11 mirrors domains: community, moderation, games, levels, voice, feedback, utility, valorant.

---

## 12–14. Dashboard-only, frontend routing, game web flows

- Some features are HTTP/UI-only without a dedicated extension load
- Public site routes live in `dashboard/frontend` (`/about`, `/docs`, `/dev-blog`, legal, credits)
- Panel shell routes in `App.tsx` / `DashboardShell`
- Mafia / Bunker / brackets: Discord lobby → personal dashboard token URLs → public `/api/public/...` actions

---

## 15. Tests and deploy

| | |
|:---|:---|
| Backend tests | Root `pytest.ini` → `dashboard/backend/tests` |
| Frontend panel | `npm run build` (`tsc -b && vite build`); `npm test` = vitest |
| Lookup API | `lookup-api/pytest.ini` (`pythonpath = .`) → `lookup-api/tests/` |
| Lookup SPA | `npm run build` (no vitest) |
| CI | `.github/workflows/ci.yml` — checkout/setup v4; no Discord secrets |
| Docker | **Not** in repo |
| Prod processes | **systemd** `cheterin-bot` + `cheterin-lookup` |
| `update.sh` | git pull; pip bot + lookup-api; build both frontends; `systemctl restart` both units |
| Nginx | `/lookup` → `lookup/dist`; `/api/lookup/*` → `:8090`; rest → bot process |
| Panel port | `DASHBOARD_PORT` (often 8080) behind reverse proxy |
| Lookup API port | `LOOKUP_API_PORT` default `8090`, bind `127.0.0.1` |

---

## 16. Environment variables (names only)

**Never paste secret values into docs.**

Core: `BOT_TOKEN`, `DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET`, `DISCORD_OAUTH_REDIRECT_URI`, `SESSION_SECRET`, `DASHBOARD_PORT`, `DASHBOARD_FRONTEND_URL`, `DASHBOARD_FRONTEND_DIST`, `GUILD_ID` / `MAIN_GUILD_ID`.

Lookup (`lookup-api/.env`): `LOOKUP_DISCORD_TOKENS` (preferred) or `LOOKUP_DISCORD_TOKEN`; optional CAPTCHA keys; `LOOKUP_API_HOST` / `LOOKUP_API_PORT`; client ID presets for the permissions calculator.

---

## 17. History (done)

| Topic | Status |
|:---|:---|
| Multi-guild | Done |
| Language RU/EN | Done |
| Timezone IANA (no MSK hardcode) | Done |
| Lookup launch + TokenPool | Done (Sep 2026) |
| Public-prep: Apache-2.0, CI, docs i18n | Done (Sep 2026) |
| systemd units + full `update.sh` | Documented in repo (operator installs on VPS) |

---

## 18. Lookup in production

Lookup product plan is **closed** (phases 0–10 shipped); historical plan files removed. Code is **shipped**.

- Paths: `/lookup`, `/lookup/about`, `/lookup/user|bot|server/...`, `/lookup/plugins/...`, `/api/lookup/...`
- Operator leftover: CAPTCHA provider keys; rotate Lookup tokens in Discord Developer Portal if ever exposed
- Locked product decisions (invite-only server, separate Discord app tokens, no Group DM / no recent feed, charcoal-red UI) stay as implemented behavior — do not reopen without an explicit product call

---

## 19. Conventions for new work

1. Logic → `*_core.py`; Discord → cog; HTTP → routes; UI → page
2. Guild settings → `settings_db` + stable `MODULE_NAME`
3. Time → `timezone_core`
4. Strings → locales / panel dictionaries
5. Tests with temp DB paths
6. **Do not** embed Lookup in `main.py`
7. **Do not** publish this architecture file on the marketing site
8. Secrets only in ENV; never commit `.env` or tokens
9. Production host/IP/SSH key paths stay in **local** `.cursor/rules/` (gitignored)

---

## 20. Quick “where to look”

| Question | File |
|:---|:---|
| Load order | `main.py` |
| HTTP wiring | `dashboard/backend/app.py` |
| ACL | `dashboard/backend/access.py` |
| Settings | `bot/core/settings_db.py` |
| UI routes | `dashboard/frontend/src/App.tsx` |
| Lookup SPA | `lookup/src/App.tsx` |
| Lookup API / TokenPool | `lookup-api/app.py` |
| systemd | `deploy/systemd/` |
| VPS update | `update.sh` → `scripts/update.sh` |
| Proxy | `lookup-api/PROXY.md` |

---

*End of map. Update when load_extension list, MODULE_NAME set, public routes, or process model change.*
