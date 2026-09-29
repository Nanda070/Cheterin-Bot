# Cheterin Lookup — product plan (EN)

> **Status (Sep 2026, after Lookup launch + Oracle deploy):** shipped at `https://cheterin.online/lookup`.  
> **Implemented:** phases **0–10**; TokenPool (`LOOKUP_DISCORD_TOKENS` round-robin + 429 rotate); operator-filled `plugins.json`; plugins hub `/lookup/plugins`; DSA as home mode `?mode=dsa`; legal `/cookies` `/disclaimer`; unified footers; charcoal-red CSS tokens; nginx `/lookup` + `/api/lookup`; **systemd** `cheterin-lookup.service` (API) + static SPA; bot+dashboard = one process under **`cheterin-bot.service`**; full `update.sh` builds both frontends and restarts both units.  
> **Operator remaining:** CAPTCHA provider keys; rotate Lookup Discord tokens in the Developer Portal if ever exposed.  
> Locked decisions below are **unchanged** — do not reopen without an explicit product decision.

Full historic plan text (Russian, detailed phases): [`CHETERIN_LOOKUP_PLAN.ru.md`](CHETERIN_LOOKUP_PLAN.ru.md).

This file is a **product plan**, not a code spec. Public URL: `https://cheterin.online/lookup`.

Screen-layout reference (not colors/copy): [dclookup.id](https://www.dclookup.id/). Visual language: **charcoal + dark red** — same kit as the rest of Cheterin.

---

## 1. Goal

Public Lookup is a separate Cheterin ecosystem product: open Discord data by ID / invite plus utilities (permissions, assets, badges, snowflake, DSA, plugin catalog).

It must:

- live at `cheterin.online/lookup` without dashboard login;
- **not depend on the Cheterin bot process** (panel shares `main.py` with the bot — Lookup must survive bot restarts);
- use a **separate Discord Application** / tokens, never `BOT_TOKEN`;
- share charcoal-red UI tokens with the public chrome;
- speak **RU / EN** via `chetbot_ui_lang`;
- stay honest about what Discord’s API returns.

`/about` remains the **bot showcase** in `dashboard/frontend`. Lookup SPA owns `/lookup/*`.

---

## 2. Locked decisions (summary)

1. Server lookup **invite-only** (vanity = code). No bare guild ID.
2. i18n RU + EN; default Russian; key `chetbot_ui_lang`.
3. Extra tools: DSA + Snowflake; no Group DM lookup.
4. Plugins: operator-curated catalog only.
5. `/about` has no search field; link out to `/lookup`.
6. `/lookup/about` is Lookup-product about, not a bot duplicate.
7. One legal set (Terms / Privacy / Cookies / Disclaimer) for both products.
8. No public recent-searches feed.
9. Separate Discord Application token(s).
10. Visual + copy quality is a product requirement.
11. One palette everywhere.
12. Header brand name: **Cheterin**.
13. Folders: `lookup/` + `lookup-api/` at repo root.
14. API on same host under `/api/lookup/...`.
15. Bot lookup = full public card when Discord allows.
16. Permissions calculator: invite URL + Client ID + config presets.
17. Asset download: Discord CDN primary; same-origin proxy fallback.
18. No fake status dashboards on the hero.
19. Rate limit UX: 429 then CAPTCHA after threshold.
20. DSA: prefer official public sources; no fake violations.
21. Mention Lookup in footer and `/docs`.
22. Keep about/credits easter eggs.
23. Cache TTLs + abuse logs hashed (not a public feed).

Details and phase history: Russian plan.

---

## 3. Process / deploy (actual)

| Piece | How |
|:---|:---|
| Bot + dashboard | `systemd` unit `cheterin-bot.service` → `python main.py` |
| Lookup API | `systemd` unit `cheterin-lookup.service` → `lookup-api` `:8090` |
| Lookup SPA | nginx → `lookup/dist` |
| Update | `bash ~/Cheterin_Bot_Dashboard/update.sh` — pull, pip both, build both SPAs, `systemctl restart` both units |
| Units in repo | `deploy/systemd/` |

Legacy tmux names `chetmain` / `chetlookup` are retired in docs; operators migrating should stop tmux and enable the units (see `deploy/systemd/README.md`). **Do not import Lookup into `main.py`.**

---

## 4. Operator leftover

| | |
|:---|:---|
| CAPTCHA keys | `LOOKUP_CAPTCHA_ENABLED` + site/secret keys |
| Token rotation | Discord Developer Portal if tokens leaked |

`plugins.json` is operator-filled. Nginx path split is documented in `lookup-api/PROXY.md`.
