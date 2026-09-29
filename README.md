<p align="center">
  <img src="dashboard/frontend/public/favicon.svg" alt="Cheterin" width="72" height="72" />
</p>

<h1 align="center">Cheterin</h1>

<p align="center">
  <strong>Public multi-guild Discord bot with a web dashboard</strong> for living communities.<br />
  Moderation, levels, economy, events, games, and VALORANT tools — without cluttering chat.
</p>

<p align="center">
  <a href="README.ru.md">Русский</a> ·
  <a href="LICENSE">Apache-2.0</a>
</p>

<p align="center">
  <a href="https://cheterin.online"><img src="https://img.shields.io/badge/Panel-cheterin.online-a8283c?style=for-the-badge" alt="Panel" /></a>
  <a href="https://discord.gg/cheterin"><img src="https://img.shields.io/badge/Cheterin_Group-Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" alt="Discord" /></a>
  <a href="https://github.com/Nanda070/Cheterin_Bot_Dashboard"><img src="https://img.shields.io/badge/GitHub-Cheterin-181717?style=for-the-badge&logo=github" alt="GitHub" /></a>
</p>

<p align="center">
  <a href="https://cheterin.online">Panel</a> ·
  <a href="https://cheterin.online/docs">Docs</a> ·
  <a href="https://cheterin.online/about">About</a> ·
  <a href="https://cheterin.online/lookup">Lookup</a> ·
  <a href="https://cheterin.online/dev-blog">Dev Blog</a> ·
  <a href="https://cheterin.online/terms">Terms</a> ·
  <a href="https://cheterin.online/credits">Credits</a> ·
  <a href="https://discord.gg/cheterin">Cheterin Group</a>
</p>

---

## Why Cheterin

One bot instead of a pile of utilities. Cheterin runs on many Discord servers with **per-guild isolation**. Admins configure modules in the browser; members use slash commands and interactions in Discord.

| | |
|:---|:---|
| **Moderation** | Logs, antispam, automod, verification, antiraid, warns |
| **Community** | Levels & XP, welcomes, invites, sticky roles, birthdays |
| **Economy** | Server currency, shop, daily, casino |
| **VALORANT** | Premier applications, role panels, `/valorant`, ValChecker, Customs lobbies |
| **Games** | Family & supply (GTA5RP), Mafia, Bunker, Wordle, roulette, Relations |
| **Content** | Events, giveaways, polls, embeds, streams, banner/icon rotation |

In Discord: **`/help`**. Bot presence: `Playing /help • Cheterin`.  
Public Lookup (ID / invite, no dashboard login): [cheterin.online/lookup](https://cheterin.online/lookup).

---

## Getting started

1. Add the bot via [cheterin.online](https://cheterin.online).
2. Sign in to the panel with the same Discord account.
3. Pick a server and enable the modules you need — each guild is independent.
4. Details: [documentation](https://cheterin.online/docs).

Support: **[Cheterin Group](https://discord.gg/cheterin)** · Contact: **turkapahf@gmail.com**

---

## Repository layout

| Path | Role |
|:---|:---|
| `main.py` | Bot entrypoint + starts the dashboard in the same process |
| `bot/` | Bot package: `core/`, `modules/*`, `cards/`, `data/` |
| `dashboard/` | Web panel (aiohttp backend + Vite/React frontend) |
| `lookup/` + `lookup-api/` | Public Lookup SPA + API (**separate process**, not started from `main.py`) |
| `docs/` | Engineer docs (`ARCHITECTURE`, Lookup plan) — EN + RU |
| `scripts/` + `update.sh` | Full VPS update (bot + Lookup builds + systemd restart) |
| `deploy/systemd/` | `cheterin-bot` / `cheterin-lookup` unit files |
| `locales/` | Bot strings (RU/EN) |
| `LICENSE` | Apache License 2.0 |
| `.github/workflows/ci.yml` | CI: pytest + frontend builds |

Maps: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) (EN) · [`docs/ARCHITECTURE.ru.md`](docs/ARCHITECTURE.ru.md) (RU).

---

## Local development (high level)

**Bot + dashboard** (needs a filled root `.env` from `.env.example` — never commit secrets):

```bash
pip install -r requirements.txt
cd dashboard/frontend && npm ci && npm run build && cd ../..
python main.py
```

**Lookup** (isolated; use `lookup-api/.env` with `LOOKUP_DISCORD_TOKENS` or `LOOKUP_DISCORD_TOKEN`, never `BOT_TOKEN`):

```bash
# API
cd lookup-api && pip install -r requirements.txt && python app.py

# SPA (another terminal)
cd lookup && npm ci && npm run dev
```

Tests without Discord tokens:

```bash
pytest                          # dashboard/backend
cd lookup-api && pytest         # Lookup API / TokenPool
cd dashboard/frontend && npm ci && npm run build
cd lookup && npm ci && npm run build
```

---

## Deploy notes (operators)

Production site: [cheterin.online](https://cheterin.online).

- **Processes:** systemd **`cheterin-bot.service`** (`python main.py` = bot + dashboard) and **`cheterin-lookup.service`** (Lookup API on **8090**). SPA static: nginx `/lookup` → `lookup/dist`. Unit files: [`deploy/systemd/`](deploy/systemd/).
- **One-command update:** `bash ~/Cheterin_Bot_Dashboard/update.sh` — `git pull`, pip for bot + lookup-api, build **both** frontends, `systemctl restart` both units.
- Install units once on the host (see [`deploy/systemd/README.md`](deploy/systemd/README.md)). Agents do not SSH or enable units for you.

SSH host details and private keys live in **local-only** Cursor rules under `.cursor/rules/` (gitignored). Do not commit production IPs, key paths, or `.env` values.

---

## Contributing / ops hygiene

- License: [Apache-2.0](LICENSE) · Copyright © 2026 Cheterin Group.
- CI runs on push/PR to `main` (no private Discord tokens required).
- Keep Lookup out of `main.py`.
- Never commit `.env`, tokens, or SSH keys.
- Public contact email: `turkapahf@gmail.com`.

UI languages: **English** and **Russian**.

---

## Links

| | |
|:---|:---|
| **Panel** | [cheterin.online](https://cheterin.online) |
| **Docs** | [cheterin.online/docs](https://cheterin.online/docs) |
| **Dev Blog** | [cheterin.online/dev-blog](https://cheterin.online/dev-blog) |
| **Lookup** | [cheterin.online/lookup](https://cheterin.online/lookup) |
| **Credits** | [cheterin.online/credits](https://cheterin.online/credits) |
| **Repository** | [github.com/Nanda070/Cheterin_Bot_Dashboard](https://github.com/Nanda070/Cheterin_Bot_Dashboard) |
| **Cheterin Group** | [discord.gg/cheterin](https://discord.gg/cheterin) |
| **Org** | [github.com/orgs/ChetTeam](https://github.com/orgs/ChetTeam) |
| **Privacy / Terms** | [privacy](https://cheterin.online/privacy) · [terms](https://cheterin.online/terms) |
| **README (RU)** | [README.ru.md](README.ru.md) |

---

<p align="center">
  <sub>© 2026 Cheterin Group Ø · part of <a href="https://discord.gg/cheterin">Cheterin Group</a> · Apache-2.0</sub>
</p>
