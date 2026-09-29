# Cheterin — внутренняя архитектурная карта

> **Внутренний инженерный справочник.**  
> **Не публикуется на cheterin.online.**  
> Документ только для коллабораторов репозитория (программисты с доступом к коду).  
> Не добавлять в React-роуты, `dashboard/frontend/src/pages/docs/`, App.tsx, Landing, Docs.tsx, футер, нав, i18n публичного сайта и не раздавать как именованную статическую страницу через aiohttp.

Русская карта: `docs/ARCHITECTURE.ru.md`. Английская: [`docs/ARCHITECTURE.md`](ARCHITECTURE.md). Публичный `README.md` / `README.ru.md`. Документация только в `docs/` (корневых stub-указателей нет). Источник правды по структуре монолита «бот + панель» и отдельному процессу Lookup.

**Lookup shipped** (Sep 2026, прод Oracle): SPA `lookup/` + API `lookup-api/`. Не импортируется и не стартует из `main.py`. Публично: `https://cheterin.online/lookup`. Локальный запуск и reverse-proxy: `lookup/RUN.md`, `lookup-api/RUN.md`, `lookup-api/PROXY.md`. План Lookup закрыт и удалён; leftover оператора: ключи CAPTCHA; ротация Lookup-токенов при утечке.

---

## 1. Идентичность

| | |
|:---|:---|
| **Продукт** | **Cheterin** — публичный multi-guild Discord-бот + веб-панель в том же OS-процессе |
| **Сайт / панель** | `https://cheterin.online` |
| **Организация** | Cheterin Group Ø |
| **Языки** | RU по умолчанию, EN поддерживается (бот `locales/`, панель `chetbot_ui_lang`) |
| **Presence** | `Playing /help • Cheterin` (`discord.ActivityType.playing`) |
| **Prefix** | `command_prefix="!"` объявлен у `ChetBot`, но **продуктовых prefix-команд нет** — всё через slash / interactions / панель |
| **Репозиторий** | `https://github.com/Nanda070/Cheterin-Bot` |

Один бот вместо набора утилит. Настройки и данные **изолированы по `guild_id`**. Конфиг — browser-first (дашборд). Новые гильдии: модули **выключены по умолчанию** там, где в `*_core.get_settings` дефолт `enabled: False` (типичный паттерн engagement/игр).

---

## 2. Зачем / принципы

1. **Один бот, много серверов** — не отдельный инстанс на гильдию.
2. **Per-guild isolation** — `settings.db` ключ `(guild_id, module)`, отдельные SQLite с `guild_id` в строках.
3. **Browser-first config** — админы крутят модули в UI; Discord — рантайм для участников.
4. **Modules off by default** (для opt-in фич) — новый сервер не получает «всё включено».
5. **Cores vs cogs** — `*_core.py` = чистая логика (тесты, импорт из routes); cog = Discord I/O (slash, listeners, views); `dashboard/backend/routes` = HTTP + ACL; frontend pages = UI.
6. **Дашборд не переписывает правила игр** — фазовые машины Mafia/Bunker/Customs живут в cores/cogs; панель управляет настройками, админ-override и публичными token-страницами действий.
7. **Main guild privilege** — CTD (`memobb`), news-relay и супер-админ привязаны к `MAIN_GUILD_ID` / `GUILD_ID` (дефолт `1324239354154975252`).

---

## 3. Как стартует (when)

Точка входа: `python main.py` → `asyncio.run(main())`.

### 3.1. `ChetBot.setup_hook`

1. `settings_db.init()` — таблица `module_settings`.
2. `await self.tree.set_translator(slash_i18n.SlashI18nTranslator())` — локализации имён/описаний slash.
3. `settings_migration.migrate_all(main_guild_id)` — одноразовая миграция плоских `*_config.json` → settings_db (идемпотентно).
4. `bot_config.migrate_from_env_if_needed(main_guild_id)`.
5. `feedback_categories.migrate_from_env_if_needed(main_guild_id)`.
6. Загрузка **52 extensions** (порядок ниже, §9).
7. Slash sync **не** в `setup_hook` — список `self.guilds` ещё пуст; sync в `on_ready`.

### 3.2. `main()`

1. `start_dashboard(bot, main_guild_id)` — aiohttp runner в том же event loop.
2. `bot.start(BOT_TOKEN)`.
3. `finally`: `dashboard_runner.cleanup()`.

**Следствие:** если бот падает / рестартит — панель тоже. Lookup — **отдельный процесс** (systemd `cheterin-lookup.service`); рестарт `cheterin-bot` его не гасит.

### 3.3. `on_ready`

- Presence `/help • Cheterin`.
- Один раз за процесс: `_commands_synced` → `_sync_commands()` (`COMMAND_SYNC_MODE`).

### 3.4. Guild lifecycle

| Событие | Действие |
|:---|:---|
| `on_guild_join` | `settings_db.set_guild_active(True)`; при `per_guild` — мгновенный `sync_guild_commands`; приветственный embed (system channel → first text → DM owner) со ссылкой на `DASHBOARD_FRONTEND_URL` |
| `on_guild_remove` | `set_guild_active(False)` — настройки **не удаляются** |

---

## 4. Модель процесса

Два OS-процесса на одном Ubuntu-хосте (Oracle). Nginx режет пути; CORS не нужен.

```
                    nginx  cheterin.online
         /  /about /docs /api/* (панель)     /lookup/*     /api/lookup/*
                    │                            │                │
                    ▼                            ▼                ▼
┌───────────────────────────────────┐   ┌──────────────────────────────┐
│  Процесс A — python main.py       │   │  Процесс B — lookup-api      │
│  systemd cheterin-bot.service     │   │  systemd cheterin-lookup     │
│  ┌────────────┐  ┌──────────────┐ │   │  aiohttp 127.0.0.1:8090      │
│  │ ChetBot    │◄►│ aiohttp      │ │   │  TokenPool (не BOT_TOKEN)    │
│  │ cogs/tree  │  │ dashboard    │ │   │  static: lookup/dist         │
│  └────────────┘  │ SPA dist     │ │   │  (nginx alias, не main.py)   │
│   shared SQLite  └──────────────┘ │   └──────────────────────────────┘
└───────────────────────────────────┘
        update.sh → git pull, pip (bot + lookup-api), build dashboard + lookup,
                    systemctl restart cheterin-bot + cheterin-lookup
```

- **Нет CORS** — same-origin / reverse-proxy; сессия-cookie панели `chetbot_dashboard_session`.
- Shared memory/SQLite только внутри процесса A (бот ↔ HTTP панели).
- Health панели: `GET /api/health` → `{"status":"ok"}`.
- Health Lookup: `GET /api/lookup/health` → `ok`, `token_configured`, `token_count`.

### 4.1. Lookup (shipped, изолирован)

| | |
|:---|:---|
| **SPA** | `lookup/` (Vite/React, `basename=/lookup`) |
| **API** | `lookup-api/` (`LOOKUP_DISCORD_TOKENS` предпочтительно, иначе `LOOKUP_DISCORD_TOKEN`) |
| **TokenPool** | Round-robin по списку; на HTTP 429 сразу следующий слот; после исчерпания всех — `min(Retry-After, 5s)` и ещё одна попытка. Коммит `33f8714`. |
| **Guardrail** | Никогда не берёт `BOT_TOKEN`. |
| **Plugins hub** | `/lookup/plugins` — каталог + вложенные tools: `snowflake`, `timestamp`, `permissions`, `badges`, `avatars`. Старые URL (`/lookup/snowflake` и т.д.) → redirect. |
| **DSA** | Режим домашней страницы `/lookup?mode=dsa` (`&id=`). `/lookup/dsa` и `/lookup/dsa/:id` только редиректят. Не отдельная primary-страница. |
| **Каталог** | Операторский `lookup-api/plugins.json` (заполнен). `GET /api/lookup/plugins`. |
| **Капча** | Код есть (`CaptchaGate`, `/api/lookup/captcha/verify`). Виджет живой только если оператор задал ключи провайдера. |
| **Цвет** | Тот же charcoal-red кит, что публичный сайт и панель: CSS-токены (`--color-background` `#0c0d10`, `--color-primary` `#a8283c`, …). Залогиненная панель **не** маскируется под lookup-карточки — только токены. |

---

## 5. Карта каталогов

Layout по образцу VALORANT (пакет `bot/`, docs/, scripts/, deploy/), с сохранением Lookup как отдельного дерева.

| Путь | Назначение |
|:---|:---|
| `main.py` | Entrypoint: Bot class, `load_extension` ×52 (`bot.modules.*`), on_ready/join/remove, start dashboard + bot |
| `bot/` | Пакет бота (не смешивать с Lookup) |
| `bot/config.py` | Бывший `bot_config.py` — каналы/роли / env migration |
| `bot/core/` | `settings_db`, migration, i18n, slash_*, embed_*, timezone, feedback_categories, … |
| `bot/modules/` | Доменные cogs + cores + dbs: `community`, `moderation`, `games`, `levels`, `voice`, `feedback`, `utility`, `valorant` |
| `bot/cards/` | Рендер карточек (profile/xp/quote/wordle/dynamic banner, …) |
| `bot/data/` | Крупные статические датасеты (bunker/wordle) |
| `locales/ru/`, `locales/en/` | Строки бота (пакет `locales` в корне) |
| `dashboard/backend/` | aiohttp app, auth, routes, middleware, session, static |
| `dashboard/backend/tests/` | pytest (см. `pytest.ini`) |
| `dashboard/frontend/` | React 19 + Vite + Tailwind |
| `dashboard/frontend/src/pages/` | Страницы панели (не путать с публичными docs) |
| `dashboard/frontend/src/pages/docs/` | **Публичная** документация сайта (`/docs`) — сюда ARCHITECTURE **не** класть |
| `lookup/` | Lookup SPA (Vite/React), basename `/lookup` — см. `lookup/RUN.md` |
| `lookup-api/` | Lookup HTTP API + `TokenPool` — см. `lookup-api/RUN.md`, `lookup-api/PROXY.md` |
| `lookup-api/plugins.json` | Операторский каталог плагинов (заполнен) |
| `lookup-api/tests/` | pytest Lookup API / TokenPool (`lookup-api/pytest.ini`) |
| `docs/ARCHITECTURE.md` | Этот файл (EN) / `docs/ARCHITECTURE.ru.md` (RU) |
| `deploy/` | nginx notes + `deploy/systemd/` unit-файлы |
| `scripts/` | `update.sh`, генераторы, selftest, `_reorg_bot.py` |
| `tests/` | Корневые one-off тесты бота (не dashboard) |
| `assets/` | Статика бота (например `assets/maps/`) |
| `update.sh` / `scripts/update.sh` | VPS: git pull, pip (bot+lookup-api), сборка dashboard + Lookup SPA, `systemctl restart` обоих unit |
| `graphify-out/` | Кэш анализа Graphify — **не** SoT, в `.gitignore` |
| `.env` / `.env.example` | Секреты бота/панели / шаблон (**пустые placeholders**). Lookup-секреты — `lookup-api/.env` |

Рантайм SQLite / `card_bgs/` / `banner_rotation_assets/` остаются **относительно CWD** (корень репо при `python main.py` / systemd WorkingDirectory) — пути в коде не завязаны на глубину `bot/`.

Lookup **изолирован**: не импортируется из `main.py` и не живёт внутри `bot/`.

---

## 6. Слой данных

### 6.1. `settings.db` — таблица `module_settings`

```sql
PRIMARY KEY (guild_id, module)
-- data TEXT JSON, updated_at TEXT
```

Кэш процесса: `{(guild_id, module): data}`; инвалидация в `put()`. После `put` вызывается `slash_modules.on_settings_put` (опциональный resync при hide-disabled).

Путь: `SETTINGS_DB_PATH` или `settings.db`.

### 6.2. Все ключи `module` (MODULE_NAME / settings keys)

| module | Источник |
|:---|:---|
| `bot_config` | `bot/config.py` |
| `language` | `language_core.py` |
| `timezone` | `timezone_core.py` |
| `xp` | `xp_core.py` |
| `economy` | `economy_core.py` |
| `casino` | `casino_core.py` |
| `family` | `family_core.py` |
| `supply` | `supply_core.py` |
| `welcome_messages` | `welcome_core.py` |
| `tempban_messages` | `tempban_core.py` |
| `spam` | `spam_core.py` |
| `automod` | `automod_core.py` |
| `antiraid` | `antiraid_core.py` |
| `verification` | `verification_core.py` |
| `giveaways` | `giveaway_core.py` |
| `daily_topic` | `daily_topic_core.py` |
| `fun` | `fun_core.py` |
| `wordle` | `wordle_core.py` |
| `mafia` | `mafia_core.py` |
| `bunker` | `bunker_core.py` |
| `quote` | `quote_core.py` |
| `starboard` | `starboard_core.py` |
| `auto_reactions` | `auto_reactions_core.py` |
| `sticky` | `sticky_core.py` |
| `sticky_roles` | `sticky_roles_core.py` |
| `scheduled_messages` | `scheduled_messages_core.py` |
| `custom_commands` | `custom_commands_core.py` |
| `invites` | `invites_core.py` |
| `birthdays` | `birthdays_core.py` |
| `owner_alerts` | `owner_alerts_core.py` |
| `bot_profile` | `bot_profile_core.py` |
| `banner_rotation` | `banner_rotation_core.py` |
| `valchecker` | `valchecker_core.py` |
| `customs` | `customs_core.py` |
| `premier` | `valorant_features_core.PREMIER_MODULE` |
| `valorant_panels` | `valorant_features_core.PANELS_MODULE` |
| `ideas` | `ideas_core.py` |
| `news` | `news.py` |
| `streams` | `streams.py` |
| `serverlog` | `serverlog.py` |
| `reaction_roles` | `reaction_roles.py` |
| `voice_panel` | `voice_rooms.py` |
| `buttons` | `button.py` |
| `embed_templates` | `embed_builder.py` |
| `feedback_categories` | `feedback_categories.py` |
| `feedback_panel` | `feedback_panel_core.py` |
| `relations` | `relations_core.py` |
| `_guild_meta` | `settings_db` (active flag) |

Дополнительно в миграции/legacy могут встречаться: `events`, `brackets`, `moderation_log`, `invites_stats`, `lockdown_backup` (см. `settings_migration.MODULE_FILE_MAP`).

### 6.3. Отдельные SQLite

| Файл (дефолт) | ENV override | Модуль |
|:---|:---|:---|
| `settings.db` | `SETTINGS_DB_PATH` | все module JSON |
| `stats.db` | `STATS_DB_PATH` | XP / voice time stats |
| `economy.db` | `ECONOMY_DB_PATH` | балансы, shop |
| `casino.db` | `CASINO_DB_PATH` | казино / лидерборд |
| `warns.db` | `WARNS_DB_PATH` | варны автомода |
| `moderation_bans.db` | `BAN_DB_PATH` | ban_db / tempban tracking |
| `mafia.db` | `MAFIA_DB_PATH` | игры мафии |
| `bunker.db` | `BUNKER_DB_PATH` | игры бункера |
| `family.db` | `FAMILY_DB_PATH` | ростер / тикеты семьи |
| `wordle.db` | `WORDLE_DB_PATH` | wordle stats |
| `private_rooms.db` | `VOICE_DB_PATH` | временные войсы |
| `invites.db` | `INVITES_DB_PATH` | трекинг инвайтов |
| `polls.db` | `POLLS_DB_PATH` | опросы |
| `timed_roles.db` | `TIMED_ROLES_DB_PATH` | временные роли |
| `birthdays.db` | `BIRTHDAYS_DB_PATH` | дни рождения |
| `starboard.db` | `STARBOARD_DB_PATH` | starboard posts |
| `relations.db` | `RELATIONS_DB_PATH` | relations / marriages |
| `verification.db` | `VERIFICATION_DB_PATH` | verification state |
| `valchecker.db` | `VALCHECKER_DB_PATH` | ValChecker profiles/poll |
| `sticky_roles.db` | `STICKY_ROLES_DB_PATH` | snapshots ролей |

### 6.4. JSON-in-settings (крупные payload’ы в `module_settings.data`)

Giveaways, supply, events, brackets, buttons, feedback/ideas cases, moderation log, custom commands, sticky messages, scheduled messages, streams, news, serverlog, automod filters/escalation, reaction roles panels, voice panel publish state, embed templates, banner rotation metadata — хранятся как JSON в settings (или гибрид settings + файлы ассетов для баннеров).

---

## 7. Паттерн слоёв

```
Discord event/slash  →  cog  →  *_core / *_db
HTTP request         →  route (+ ACL)  →  *_core / *_db
React page           →  api/client     →  /api/...
```

| Слой | Делает | Не делает |
|:---|:---|:---|
| `*_core.py` | валидация, defaults, enabled, бизнес-правила | HTTP, discord.py API |
| Cog | commands, listeners, views, DM, embed send | прямой SQL без db-helper |
| `routes/*.py` | JSON API, guild_id из session, права | дублировать правила игры |
| Frontend page | формы, табы, i18n UI | знать схему SQLite |

Тесты: pytest с фейками бота/гильдии в `dashboard/backend/tests`; frontend — `vitest run`.

---

## 8. Auth и ACL

### 8.1. OAuth

- Discord OAuth scopes: **identify + guilds**.
- Роуты: `/api/auth/login`, `/api/auth/discord/callback`, `/api/auth/me`, `/api/auth/guilds`, `/api/auth/select-guild`, `/api/auth/invite-url`, `/api/auth/logout`.
- Сессия: `EncryptedCookieStorage`, cookie `chetbot_dashboard_session`, `SESSION_SECRET` → Fernet key (SHA-256).
- `Secure` cookie: `DASHBOARD_COOKIE_SECURE` или auto при `https://` в `DASHBOARD_FRONTEND_URL`.

### 8.2. Доступ к серверу

- **Manage Server** (`0x20`) или **Administrator** (`0x8`) на выбранной гильдии.
- UI-фильтр: `manageable_guilds()` по битмаске OAuth; финальная проверка на API middleware.

### 8.3. Super-admin

- Резолв участника на **main guild** (`MAIN_GUILD_ID`, дефолт `1324239354154975252`).
- Administrator **или** роль из `SUPER_ADMIN_ROLE_IDS` (хардкод в `access.py`, сейчас `1505359848433516734`).
- UI: группа nav «superadmin» (`/superadmin`, `/health`, `/news`, `/ctd` main-guild-only).
- Клиентский guard неполный — режет **API** (дрейф §14.4 Lookup-плана).

### 8.4. Main-guild only продукты

- **CTD** (`memobb` / `/ctd` / `/api/ctd`)
- **News relay** (`news` / `/news` / `/api/news`)

### 8.5. Deprecated leftovers

- `has_dashboard_access(member, allowed_role_ids)` — DEPRECATED.
- `DASHBOARD_ACCESS_ROLE_IDS` — выведен из обихода; возможен legacy fallback в middleware если env задан.

---

## 9. i18n и timezone

| Контур | Механизм |
|:---|:---|
| Бот (эмбеды, тексты) | `locales/ru|en` + `i18n.guild_t(guild_id, key)` + `language_core` (`module=language`, `{"code":"ru"|"en"}`) |
| Панель UI | cookie/localStorage **`chetbot_ui_lang`** (`LanguageContext`); согласие на плашку cookies — **`chetbot_cookie_consent`** (`CookieBanner`) |
| Slash names/descriptions | `slash_i18n.SlashI18nTranslator` + `slash_registry` / gen scripts |
| Timezone | `timezone_core`: IANA, **default `Europe/Moscow`**; `module=timezone` |

Legacy алиасы `MOSCOW_TZ` / `_MSK` ещё встречаются в отдельных cores (см. §16 / Lookup §14.5) — боевые расписания должны идти через `timezone_core`.

---

## 10. Slash sync

| ENV | Смысл |
|:---|:---|
| `COMMAND_SYNC_MODE=per_guild` | **Дефолт.** Guild-команды на каждую гильдию — мгновенно |
| `COMMAND_SYNC_MODE=global` | Заготовка: один global sync + guild sync привилегий мейна (CTD) |
| `COMMAND_SYNC_HIDE_DISABLED=1` | Opt-in: не пушить root’ы выключенных модулей |
| `COMMAND_SYNC_CLEAR_GLOBAL=1` | Очистить старые global commands при per_guild |

`slash_modules.MODULE_ROOT_COMMANDS` связывает settings-модуль → английские root names (`levels`, `casino`, `val`, `mafia-start`, …). Без hide: слэши видны, рантайм отказывает если модуль off.

---

## 11. Каталог cogs (порядок `load_extension`)

Ниже — все 52 расширения из `main.py`. Для каждого: что / зачем / когда / как / привязки панели.

### 11.1. Сводная таблица bindings

| # | Cog | Core / helpers | settings module | DB | Page / tabs | API prefix |
|:---:|:---|:---|:---|:---|:---|:---|
| 1 | `feedback_menu` | `feedback_core`, `feedback_panel_core`, `feedback_categories` | `feedback_panel`, `feedback_categories` | JSON cases | `/feedback` (+ ideas tab) | `/api/feedback-*`, `/api/ideas` |
| 2 | `welcome` | `welcome_core` | `welcome_messages` | — | `/server-entry` welcome/greeting | `/api/welcome-settings` |
| 3 | `button` | — | `buttons` | JSON | (кнопки через builder/flows) | частично embed/reaction flows |
| 4 | `memobb` | — | через `bot_config`/CTD | — | `/ctd` (main) | `/api/ctd` |
| 5 | `lockdown` | `lockdown_core` | backup в migration | — | `/lockdown` moderation | `/api/lockdown/*` |
| 6 | `tempban` | `tempban_core` | `tempban_messages` | `ban_db` | `/lockdown?tab=tempban` | `/api/tempban-settings` |
| 7 | `spam` | `spam_core` | `spam` | — | `/lockdown?tab=antispam` | `/api/spam-settings` |
| 8 | `events` | `events_core` | events JSON | — | `/events` | `/api/events` |
| 9 | `reaction_roles` | — | `reaction_roles` | — | `/reaction-roles` | `/api/reaction-roles` |
| 10 | `news` | — | `news` | — | `/news` (superadmin) | `/api/news` |
| 11 | `voice_rooms` | VoiceManager+Panel | `voice_panel` | `private_rooms.db` | `/voice-rooms` | `/api/voice/*` |
| 12 | `supply` | `supply_core` | `supply` | — | `/family?tab=supply` | `/api/supply` |
| 13 | `serverlog` | — | `serverlog` | — | `/serverlog` | `/api/serverlog` |
| 14 | `voice_tracker` | stats | — | `stats.db` | `/voice-stats` | `/api/voice-stats` |
| 15 | `xp` | `xp_core` | `xp` | `stats.db` | `/levels`, public `/leaderboard` | `/api/xp`, `/api/public/leaderboard` |
| 16 | `streams` | — | `streams` | — | `/streams` | `/api/streams` |
| 17–19 | `family_*` | `family_core` | `family` | `family.db` | `/family` | `/api/family` |
| 20 | `mafia` | `mafia_core` | `mafia` | `mafia.db` | `/mafia`, `/mafia/:token` | `/api/mafia`, `/api/public/mafia` |
| 21 | `giveaways` | `giveaway_core` | `giveaways` | — | `/events?tab=giveaways` | `/api/giveaways` |
| 22 | `daily_topic` | `daily_topic_core` | `daily_topic` | — | `/fun?tab=dailyTopic` | `/api/daily-topic` |
| 23 | `automod` | `automod_core` | `automod` | `warns.db` | `/automod` | `/api/automod`, `/api/warns` |
| 24 | `bunker` | `bunker_core` | `bunker` | `bunker.db` | `/bunker`, `/bunker/:token` | `/api/bunker`, `/api/public/bunker` |
| 25 | `fun` | `fun_core` | `fun` | — | `/fun` | `/api/fun` |
| 26 | `moderation_commands` | `moderation_commands_core`, embed core | moderation_log JSON | — | `/members`, `/lockdown` | `/api/members`, mod actions |
| 27 | `wordle` | `wordle_core` | `wordle` | `wordle.db` | `/fun?tab=wordle` | `/api/wordle` |
| 28 | `economy` | `economy_core` | `economy` | `economy.db` | `/economy` | `/api/economy` |
| 29–30 | `casino`, `blackjack` | `casino_core`, `blackjack_core` | `casino` | `casino.db` | `/economy?tab=casino` | `/api/casino` |
| 31 | `antiraid` | `antiraid_core` | `antiraid` | — | `/lockdown?tab=antiraid` | `/api/antiraid` |
| 32 | `verification` | `verification_core` | `verification` | `verification.db` | `/lockdown?tab=verification` | `/api/verification` |
| 33 | `custom_commands` | `custom_commands_core` | `custom_commands` | — | `/settings?tab=customCommands` | `/api/custom-commands` |
| 34 | `scheduled_messages` | `scheduled_messages_core` | `scheduled_messages` | — | `/messages?tab=scheduled` | `/api/scheduled-messages` |
| 35 | `invites` | `invites_core` | `invites` | `invites.db` | `/server-entry?tab=invites` | `/api/invites` |
| 36 | `timed_roles` | — | — | `timed_roles.db` | `/members?tab=timedRoles` | `/api/timed-roles` |
| 37 | `birthdays` | `birthdays_core` | `birthdays` | `birthdays.db` | `/birthdays` | `/api/birthdays` |
| 38 | `polls` | — | — | `polls.db` | `/events?tab=polls` | `/api/polls` |
| 39 | `sticky` | `sticky_core` | `sticky` | — | `/messages?tab=sticky` | `/api/sticky` |
| 40 | `owner_alerts` | `owner_alerts_core` | `owner_alerts` | — | `/settings` general | `/api/owner-alerts`, `/api/setup-health` |
| 41 | `starboard` | `starboard_core` | `starboard` | `starboard.db` | `/messages?tab=starboard` | `/api/starboard` |
| 42 | `auto_reactions` | `auto_reactions_core` | `auto_reactions` | — | `/fun?tab=autoEmoji` | `/api/auto-reactions` |
| 43 | `quote` | `quote_core` | `quote` | — | `/fun?tab=quote` | `/api/quote` |
| 44 | `relations` | `relations_core` | `relations` | `relations.db` | `/relations` | `/api/relations` |
| 45 | `help_cog` | — | — | — | — (`/help` in Discord) | — |
| 46 | `valchecker` | `valchecker_core` | `valchecker` | `valchecker.db` | `/valorant?tab=valchecker` | `/api/valchecker` |
| 47 | `valorant_random` | — | commands via valorant API | — | (slash only; UI tab forced away) | `/api/valorant/commands` |
| 48 | `premier` | `valorant_features_core` | `premier` | — | API only (нет вкладки UI) | `/api/valorant/premier` |
| 49 | `valorant_panels` | `valorant_features_core` | `valorant_panels` | — | API only | `/api/valorant/panels` |
| 50 | `ideas` | `ideas_core` | `ideas` | — | `/feedback?tab=ideas` | `/api/ideas` |
| 51 | `banner_rotation` | `banner_rotation_core` | `banner_rotation` | assets on disk | `/banner-rotation` | `/api/banner-rotation` |
| 52 | `customs` | `customs_core` | `customs` | — | `/valorant?tab=customs` | `/api/customs` |

### 11.2. Детали по cog (what / why / when / how)

#### 1. `feedback_menu`
- **Что:** панель обратной связи (категории, кейсы, решения модераторов).
- **Зачем:** тикеты жалоб/предложений без ручного хаоса в чате.
- **Когда:** slash/panel publish; interaction submit; dashboard decide.
- **Как:** категории в settings; кейсы JSON; publish panel в канал.
- **UI:** `/feedback`; ideas — соседний поток (§ ниже).

#### 2. `welcome`
- **Что:** welcome/goodbye/DM шаблоны; трекинг инвайтов на join.
- **Когда:** `on_member_join` / `on_member_remove`, invite create/delete, `on_ready`.
- **UI:** `/server-entry` tabs welcome, greeting, autoroles (autoroles — отдельный route).

#### 3. `button`
- **Что:** конструктор persistent buttons / role buttons.
- **Когда:** `/button_create`-подобные команды, `on_interaction`.
- **Settings:** `buttons`.

#### 4. `memobb` (CTD)
- **Что:** Cheterin Ticket Desk / CTD setup на main guild.
- **Когда:** `ctd_setup`, loops/`on_ready`.
- **Ограничение:** только main guild + super-admin UI.

#### 5. `lockdown`
- **Что:** антиспам-локдаун каналов (activate/deactivate/status).
- **Когда:** slash `antispam`/`off`/`status`; dashboard POST activate/deactivate.
- **UI:** `/lockdown` tab moderation + settings.

#### 6. `tempban`
- **Что:** временные баны / предупреждающие сообщения в канале.
- **Когда:** `on_message` в tempban-канале; `on_ready` restore.
- **Дрейф:** mention-exempt роли всё ещё из **ENV**, не из панели.

#### 7. `spam`
- **Что:** антиспам (mentions, исключения каналов/ролей).
- **Когда:** `on_message`, interactions.
- **UI:** `/lockdown?tab=antispam`.

#### 8. `events`
- **Что:** регистрация на события, notify, close.
- **Когда:** slash event setup/manage; dashboard CRUD; `on_ready` restore views.
- **UI:** `/events` tab events.

#### 9. `reaction_roles`
- **Что:** роли по реакциям на сообщениях.
- **Когда:** `on_raw_reaction_add/remove`; dashboard CRUD.
- **UI:** `/reaction-roles` (MessageBuilder).

#### 10. `news`
- **Что:** релей новостей с источника на целевые каналы (main guild).
- **Когда:** `on_message` в source.
- **UI:** `/news` super-admin.

#### 11. `voice_rooms`
- **Что:** VoiceManager (личные комнаты) + PanelManager (панель управления).
- **Когда:** `on_voice_state_update`, channel update, publish panel.
- **DB:** `private_rooms.db`. **Settings:** `voice_panel`.

#### 12. `supply`
- **Что:** GTA5RP-поставки семьи (создание/закрытие/отмена).
- **UI:** `/family?tab=supply`.

#### 13. `serverlog`
- **Что:** аудит-лог сервера (сообщения, мемберы, роли, каналы, voice, invites, …).
- **Когда:** большой набор listeners (см. grep on_*).
- **UI:** `/serverlog`.

#### 14. `voice_tracker`
- **Что:** учёт времени в войсе → stats.
- **Когда:** voice state + ready restore.
- **UI:** `/voice-stats`.

#### 15. `xp`
- **Что:** уровни, rank/profile cards, leaders, manage XP.
- **Когда:** `on_message` XP gain; slash `/levels` group; member remove cleanup.
- **UI:** `/levels`; публичный `/leaderboard/:guildId`.

#### 16. `streams`
- **Что:** алерты Twitch/YouTube/TikTok.
- **Когда:** polling loop; dashboard CRUD + test.
- **ENV:** `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET` (опционально).

#### 17–19. `family_roster`, `family_tickets`, `family_birthdays`
- **Что:** ростер семьи GTA5RP, заявки-тикеты, дни рождения семьи.
- **Когда:** member update/remove; slash birthday; ticket submit.
- **UI:** `/family` tabs settings/roster/tickets/birthdays/supply.

#### 20. `mafia`
- **Что:** лобби и фазовая игра «Мафия».
- **Когда:** slash start/stop; game loop; личные ссылки на web-action.
- **Public:** `/mafia/:token` → `/api/public/mafia/{token}`.

#### 21. `giveaways`
- **Что:** розыгрыши start/end/reroll.
- **UI:** `/events?tab=giveaways`.

#### 22. `daily_topic`
- **Что:** ежедневная тема в канал (по TZ гильдии).
- **UI:** `/fun?tab=dailyTopic`; API post-now.

#### 23. `automod`
- **Что:** фильтры, escalation, warn slash.
- **Когда:** `on_message`; `/warn`.
- **UI:** `/automod`; warns на `/members`.

#### 24. `bunker`
- **Что:** игра «Бункер» (карты, фазы, способности, голосование).
- **Public:** `/bunker/:token` → `/api/public/bunker/{token}`.

#### 25. `fun`
- **Что:** развлекательные механики (в т.ч. russian-roulette slash mapping).
- **Когда:** message triggers; settings enabled.
- **UI:** `/fun` general.

#### 26. `moderation_commands`
- **Что:** `/ban` `/kick` `/mute` `/unmute` `/unban` `/clear`.
- **UI:** зеркало действий на `/members` + case timeline.

#### 27. `wordle`
- **Что:** Wordle play/training/stats/top.
- **UI:** `/fun?tab=wordle`.

#### 28. `economy`
- **Что:** daily, balance, transfer, shop, cosmetics, weekly.
- **UI:** `/economy` settings/balances.

#### 29–30. `casino` + `blackjack`
- **Что:** slots, coinflip, blackjack, casino top.
- **UI:** `/economy?tab=casino`.

#### 31. `antiraid`
- **Что:** защита от массовых join.
- **Когда:** `on_member_join`.
- **UI:** `/lockdown?tab=antiraid`.

#### 32. `verification`
- **Что:** верификация новичков, publish panel, `/verify_setup`.
- **UI:** `/lockdown?tab=verification`.

#### 33. `custom_commands`
- **Что:** текстовые триггеры → ответы (message listener).
- **UI:** `/settings?tab=customCommands` (+ preview view).

#### 34. `scheduled_messages`
- **Что:** отложенные/периодические посты по TZ.
- **UI:** `/messages?tab=scheduled`.

#### 35. `invites`
- **Что:** статистика инвайтов, join attribution.
- **UI:** `/server-entry?tab=invites`.

#### 36. `timed_roles`
- **Что:** временная выдача ролей (`/timed-role`); панель list/delete **без create**.
- **UI:** `/members?tab=timedRoles`.

#### 37. `birthdays`
- **Что:** серверные ДР (`/set-birthday`), анонсы.
- **UI:** `/birthdays` календарь.

#### 38. `polls`
- **Что:** `/poll`; панель list/get/end **без create**.
- **UI:** `/events?tab=polls`.

#### 39. `sticky`
- **Что:** sticky-сообщения (репост при on_message).
- **UI:** `/messages?tab=sticky`.

#### 40. `owner_alerts`
- **Что:** алерты владельцу (mass ban, missing perms, module errors, weekly digest).
- **Когда:** `on_member_ban` + health checks.
- **UI:** `/settings` general + setup-health.

#### 41. `starboard`
- **Что:** порог реакций → пост в starboard-канал.
- **UI:** `/messages?tab=starboard`.

#### 42. `auto_reactions`
- **Что:** автоэмодзи на сообщения по правилам.
- **UI:** `/fun?tab=autoEmoji`.

#### 43. `quote`
- **Что:** цитирование / quote channel flow.
- **UI:** `/fun?tab=quote`.

#### 44. `relations`
- **Что:** social actions (hug/kiss/…) + marriages top.
- **UI:** `/relations`.

#### 45. `help_cog`
- **Что:** `/help` — короткая справка + ссылка на docs/панель.
- **Панели нет.**

#### 46. `valchecker`
- **Что:** Henrik API — setup/profile/match/compare/status; polling.
- **ENV:** `HENRIK_API_KEY`.
- **UI:** `/valorant?tab=valchecker`.

#### 47. `valorant_random`
- **Что:** `/valorant` random agent/map/skin/… (часто EN-only, дрейф i18n).
- **UI-вкладки commands нет** (query форсится на customs).

#### 48. `premier`
- **Что:** Premier applications / notifications.
- **API живой; отдельной вкладки ValorantPage нет** (дрейф docs/What’s New).

#### 49. `valorant_panels`
- **Что:** publish ролевых панелей VALORANT.
- **API `/api/valorant/panels`; UI-вкладки нет.**

#### 50. `ideas`
- **Что:** модерируемые идеи (канал → cases → decide).
- **UI:** `/feedback?tab=ideas` (**не** VALORANT).

#### 51. `banner_rotation`
- **Что:** ротация баннера/иконки гильдии (в т.ч. dynamic window).
- **UI:** `/banner-rotation`.

#### 52. `customs`
- **Что:** VALORANT кастомки — лобби, команды, карты, voice, score, schedules, blacklist.
- **Когда:** богатый набор interactions + voice.
- **UI:** `/valorant?tab=customs`.

---

## 12. Dashboard-only (без отдельного load_extension)

| Фича | Page | API | Core |
|:---|:---|:---|:---|
| Embed builder / templates | MessageBuilder / embed flows | `/api/embed-messages`, `/api/embed-templates` | `embed_builder.py` |
| Brackets | `/events?tab=brackets`, `/brackets/:id`, public `/bracket/:token` | `/api/brackets`, `/api/public/brackets` | `brackets.py` / events |
| Bot profile | `/settings?tab=botProfile` | `/api/bot-profile` | `bot_profile_core` |
| Preview templates | redirect → settings customCommands preview | `/api/preview/template` | `preview_core` |
| Modules sidebar flags | (shell) | `GET /api/modules` | getters в `routes/modules.py` |
| Audit log панели | `/settings?tab=audit` | `/api/audit` | audit middleware |
| Mass-role jobs | `/members` | `/api/roles/{id}/mass-assign`, job status | moderation routes |
| Case timeline | member detail | `/api/members/{id}/case-timeline` | `case_timeline_core` |
| Language / timezone | `/settings` general | `/api/language`, `/api/timezone` | language/timezone cores |
| Auto-roles | `/server-entry?tab=autoroles` | `/api/auto-roles` | welcome/config |
| Sticky roles | `/server-entry?tab=stickyRoles` | `/api/sticky-roles` | `sticky_roles_core` |
| Superadmin guilds / host health | `/superadmin`, `/health` | `/api/superadmin/*` | — |
| Config (каналы/роли bot_config) | lockdown/settings | `/api/config` | `bot_config` |

---

## 13. Frontend routing

### 13.1. Публичные маршруты (без shell / без Manage Server)

| Path | Страница |
|:---|:---|
| `/login` | Login |
| `/about` | Landing (витрина бота; кнопка Lookup → `/lookup`, без hero-поиска) |
| `/docs`, `/docs/:sectionId` | Docs (упоминание Lookup в публичных секциях) |
| `/dev-blog` | История разработки |
| `/terms`, `/privacy`, `/cookies`, `/disclaimer`, `/credits` | Legal / credits — один комплект на бот и Lookup. Legal-страницы делят `LegalSubnav` (Условия ↔ Приватность ↔ Cookies ↔ Отказ). Верхняя шапка залогиненной панели показывает только Документация + Условия; остальные legal — в футере и subnav. Cookie-плашка: `CookieBanner` + localStorage `chetbot_cookie_consent`. |
| `/sans`, `/snowdin`, `/waterfall`, `/core`, `/judgment` | easter eggs |
| `/bracket/:token` | Public bracket |
| `/mafia/:token` | Public mafia action |
| `/bunker/:token` | Public bunker action |
| `/leaderboard`, `/leaderboard/:guildId` | Public XP board (`:guildId` нужен для данных) |
| `/access-denied` | AccessDenied |
| `*` | NotFound |

Публичный chrome (шапка/футер) **единый** на `/about`, `/docs`, `/dev-blog`, legal. Legal-страницы: `LegalSubnav` + обновлённые тексты (Sep 2026). Cookie-плашка в корне `App.tsx`. Lookup SPA имеет свой `SiteFooter` с теми же корневыми legal URL. `ARCHITECTURE.md` в эти маршруты **не** кладётся.

### 13.2. Shell (`/` + `DashboardShell` через `PublicLandingOrDashboard`)

Гость на `/` → лендинг-поведение; залогиненный с гильдией → shell.

Вложенные пути: `members`, `lockdown`, `reaction-roles`, `feedback`, `events`, `brackets/:id`, `family`, `mafia`, `bunker`, `fun`, `messages`, `birthdays`, `relations`, `automod`, `server-entry`, `voice-rooms`, `news`, `levels`, `economy`, `streams`, `serverlog`, `voice-stats`, `settings`, `ctd`, `superadmin`, `health`, `banner-rotation`, `valorant`, …

Много **redirects** со старых URL (`/casino` → economy tab, `/giveaways` → events, `/welcome` → server-entry, …) — см. `App.tsx`.

### 13.3. `NAV_GROUPS` (sidebar)

1. **home** — `/`
2. **engage** — levels, economy, voice-stats
3. **people** — relations, birthdays, voice-rooms, events, feedback, messages, reaction-roles
4. **play** — fun, mafia, bunker, valorant, family, streams
5. **server** — lockdown, automod, serverlog, server-entry, members, banner-rotation, settings
6. **superadmin** (flag) — superadmin, health, news, ctd (mainGuildOnly)

Скрытие по `GET /api/modules` keys:  
`levels`, `economy`, `casino`, `family`, `messages`, `birthdays`, `starboard`, `autoReactions`, `fun`, `relations`, `dailyTopic`, `mafia`, `bunker`, `automod`, `customCommands`, `valchecker`, `customs`, `bannerRotation`.

### 13.4. Важные составные страницы / tabs

| Page | Tabs |
|:---|:---|
| `/settings` | general, botProfile, customCommands, audit |
| `/lockdown` | moderation, settings, antiraid, antispam, tempban, verification |
| `/server-entry` | welcome, greeting, autoroles, stickyRoles, invites |
| `/events` | events, giveaways, polls, brackets |
| `/messages` | messages, starboard, scheduled, sticky |
| `/fun` | general, autoEmoji, wordle, quote, dailyTopic |
| `/economy` | settings, casino, balances |
| `/family` | settings, roster, tickets, birthdays, supply |
| `/valorant` | **customs**, **valchecker** only (panels/premier/commands query → customs) |
| `/feedback` | cases + ideas |

---

## 14. Game web flows (Mafia / Bunker)

1. Админ включает модуль и настраивает канал/роли в панели.
2. Участники стартуют игру слэшем в Discord (лобби).
3. Бот шлёт **персональные** ссылки: `{DASHBOARD_FRONTEND_URL}/mafia|{bunker}/{token}`.
4. Браузер бьёт **публичные** API без cookie-админ ACL:  
   `/api/public/mafia/{token}` (action/vote),  
   `/api/public/bunker/{token}` (reveal/vote/ability).
5. Фазовая логика остаётся в core/cog; веб — thin client действий игрока.
6. Аналогично brackets: share token → `/bracket/:token` → `/api/public/brackets/{token}`.

---

## 15. Тесты и деплой

| | |
|:---|:---|
| Backend tests (бот/панель) | корневой `pytest.ini` → `testpaths = dashboard/backend/tests`, `asyncio_mode = auto` |
| Frontend tests (панель) | `npm test` → `vitest run` в `dashboard/frontend` |
| Lookup API tests | `lookup-api/pytest.ini` → `lookup-api/tests/` (`test_token_pool.py`, `test_api.py`) |
| Lookup SPA | нет vitest; `npm run build` = `tsc -b && vite build`, lint = oxlint |
| Docker | **Нет** в репозитории |
| Прод | Ubuntu на Oracle Cloud. Бот+панель — один процесс (`python main.py`, systemd **`cheterin-bot.service`**). Lookup API — отдельный (`python app.py` в `lookup-api/`, systemd **`cheterin-lookup.service`**). |
| `update.sh` | `bash ~/Cheterin_Bot_Dashboard/update.sh` → git pull, pip bot+lookup-api, сборка `dashboard/frontend` + `lookup/`, `systemctl restart` `cheterin-bot` + `cheterin-lookup`. |
| Nginx | `/lookup` + `/lookup/*` → `lookup/dist` (Vite `base: '/lookup/'`); `/api/lookup/*` → `127.0.0.1:8090`; остальное (about/docs/legal/панель) → процесс A. Пример: `lookup-api/PROXY.md`. |
| Статика панели | `DASHBOARD_FRONTEND_DIST` → aiohttp `setup_static_routes` (не отдельный nginx-only app для панели). |
| Стек Python (бот) | `requirements.txt`: discord.py, dotenv, aiohttp, aiohttp-session, cryptography, Pillow, psutil, tzdata, pytest* |
| Lookup API deps | `lookup-api/requirements.txt` (свой venv допустим) |
| Frontend | React 19, Vite, Tailwind — отдельно `dashboard/frontend` и `lookup/` |
| Порт панели | `DASHBOARD_PORT` (часто 8080) за reverse-proxy |
| Порт Lookup API | `LOOKUP_API_PORT` (дефолт 8090, bind `127.0.0.1`) |

---

## 16. Переменные окружения (концептуально)

**Не копировать секретные значения из `.env` / `.env.example` сюда.** Только имена и смысл.

### Обязательные / ядро

| Key | Смысл |
|:---|:---|
| `BOT_TOKEN` | Discord bot token |
| `DISCORD_CLIENT_ID` / `DISCORD_CLIENT_SECRET` | OAuth приложения панели |
| `DISCORD_OAUTH_REDIRECT_URI` | Callback URL |
| `SESSION_SECRET` | Шифрование cookie-сессии |
| `DASHBOARD_PORT` | Порт aiohttp |
| `DASHBOARD_FRONTEND_URL` | Публичный origin (ссылки в эмбедах, Secure cookie) |
| `DASHBOARD_FRONTEND_DIST` | Путь к собранному SPA |
| `GUILD_ID` / `MAIN_GUILD_ID` | Main guild (CTD/news/super-admin/миграция) |

### Опциональные продукт/интеграции

| Key | Смысл |
|:---|:---|
| `HENRIK_API_KEY` | ValChecker / Henrik |
| `TWITCH_CLIENT_ID` / `TWITCH_CLIENT_SECRET` | Streams Helix (YouTube/TikTok могут без них) |
| `COMMAND_SYNC_MODE` | `per_guild` \| `global` |
| `COMMAND_SYNC_HIDE_DISABLED` | hide slash roots |
| `COMMAND_SYNC_CLEAR_GLOBAL` | wipe global cmds |
| `DASHBOARD_COOKIE_SECURE` | force Secure cookie |
| `DASHBOARD_ACCESS_ROLE_IDS` | legacy, не использовать |
| `*_DB_PATH` | override путей SQLite |
| `BUTTON_WEBHOOK_*` | webhook для button collector |
| Каналы/роли `LOG_CHANNEL_ID`, `WELCOME_CHANNEL_ID`, `CTD_*`, `SPAM_*`, … | исторический ENV → миграция в `bot_config` / spam settings; часть tempban exempt всё ещё ENV |

### Lookup (`lookup-api/.env`, не процесс бота)

Имена только. Значения — в `lookup-api/.env.example`, не сюда.

| Key | Смысл |
|:---|:---|
| `LOOKUP_DISCORD_TOKENS` | Предпочтительно: comma-list bot-токенов Lookup; round-robin + 429 rotate |
| `LOOKUP_DISCORD_TOKEN` | Fallback на один токен, если multi не задан |
| `LOOKUP_API_HOST` / `LOOKUP_API_PORT` | Bind (дефолт `127.0.0.1:8090`) |
| `LOOKUP_CLIENT_ID` / `CHETERIN_CLIENT_ID` | Пресеты калькулятора прав (не секреты) |
| `LOOKUP_CAPTCHA_ENABLED` | `true` только после ключей провайдера |
| `LOOKUP_CAPTCHA_SITE_KEY` / `LOOKUP_CAPTCHA_SECRET` | Ключи Turnstile/hCaptcha — **оператор, leftover** |
| `LOOKUP_CAPTCHA_PROVIDER` | `turnstile` (дефолт) или hCaptcha |

---

## 17. История (сделано)

| Тема | Статус |
|:---|:---|
| Multi-guild (`settings.db`, guild picker, active flag) | Done (`MULTIGUILD_PLAN.md` удалён) |
| Language RU/EN (бот + панель + slash translator) | Done |
| Timezone IANA вместо хардкода MSK | Done (см. workspace rule guild-timezone) |
| What’s New панели | `2026.09.2` (plugins hub, badges, DSA, Dev Blog), `2026.09.1` (Lookup launch), `2026.08.2` … `2026.08.5` в `whatsNew.ts` |
| Lookup launch + Oracle deploy | Done (Sep 2026): SPA+API в проде, TokenPool `33f8714`, nginx `/lookup` + `/api/lookup`, systemd `cheterin-lookup` |

История фич панели = `dashboard/frontend/src/whatsNew.ts`, не корневой CHANGELOG.

---

## 18. Lookup в проде и дрейф монолита

План Lookup **закрыт** (фазы 0–10 shipped; файлы плана удалены). Locked decisions не переоткрывать без явного product-решения. Код и прод — **shipped**.

### 18.1. Что уже в коде и на Oracle

- SPA + API на корне: `lookup/` + `lookup-api/` (не внутри `dashboard/`);
- `main.py` Lookup не импортирует и не стартует;
- **TokenPool:** `LOOKUP_DISCORD_TOKENS` (comma-list) предпочтительнее `LOOKUP_DISCORD_TOKEN`; 429 rotate (`33f8714`); никогда `BOT_TOKEN`;
- nginx: `/lookup` → `lookup/dist`, `/api/lookup` → `:8090`; systemd `cheterin-lookup`;
- публичный chrome: `/about`, `/docs`, `/dev-blog`, `/terms` `/privacy` `/cookies` `/disclaimer` `/credits`; единые футеры;
- панель и Lookup делят charcoal-red **токены**, не layout карточек Lookup.

| Path | Назначение |
|:---|:---|
| `/lookup` | Hero: режимы `user` / `bot` / `server` / `dsa` (`?mode=` + `?id=`) |
| `/lookup/about` | About продукта Lookup (не витрина бота) |
| `/lookup/user/:id`, `/lookup/bot/:id`, `/lookup/server/:code` | Карточки |
| `/lookup/plugins` | Хаб: каталог + tabs tools |
| `/lookup/plugins/snowflake`, `.../timestamp`, `.../permissions`, `.../badges`, `.../avatars` | Tools |
| `/lookup/dsa`, `/lookup/dsa/:id` | Redirect на `/?mode=dsa` |
| `/lookup/dev-blog` | Dev blog внутри Lookup SPA (канон сайта — корневой `/dev-blog`) |
| `/api/lookup/health`, `/config`, `/plugins`, `/dsa`, `/dsa/{id}`, `/user/{id}`, `/bot/{id}`, `/server/{code}`, `/cdn/...`, `POST /captcha/verify` | API |

### 18.2. Leftover оператора (не пробелы кода)

| | |
|:---|:---|
| CAPTCHA ключи | `LOOKUP_CAPTCHA_ENABLED` + `LOOKUP_CAPTCHA_SITE_KEY` + `LOOKUP_CAPTCHA_SECRET` — виджет не появится, пока не заданы |
| Ротация токенов в Portal | Если Lookup-токены светились в чате — сменить в Discord Developer Portal (пул в ENV уже умеет несколько) |

`plugins.json` оператор **заполнил**. Nginx/DNS на Oracle — **сделаны**.

### 18.3. Дрейф монолита (§14 плана) — Lookup его не закрывает

| Область | Факт |
|:---|:---|
| Legal | `/cookies`, `/disclaimer` **есть** (фаза 9 сдана) |
| VALORANT UI | только customs + valchecker; premier/panels API живы без вкладок |
| What’s New / docs | текст про Premier/panels/ideas на VALORANT tab **не совпадает** с UI |
| Ideas | живут в `/feedback?tab=ideas` |
| i18n | valorant random / premier / panels / ideas EN-only; MassAssign RU вне i18n; … |
| Auth leftovers | `has_dashboard_access`, `DASHBOARD_ACCESS_ROLE_IDS` |
| Audit labels | многие мутации → `audit.action.other` |
| Polls / timed-roles UI | нет create |
| Tempban exempt | ENV |
| `MOSCOW_TZ` aliases | legacy в части cores |
| Prefix `!` | объявлен, не используется продуктово |
| CTD/news | только main guild — продукт, не баг |

---

## 19. Конвенции для новой работы

1. **Логика → `*_core.py`**, Discord → cog, HTTP → `dashboard/backend/routes`, UI → page. Не дублировать правила.
2. Настройки гильдии → `settings_db` + стабильный `MODULE_NAME`; дефолты в `get_settings`.
3. Время суток / расписания → **`timezone_core`**, не хардкод MSK и не новые `MOSCOW_TZ` алиасы.
4. Строки бота → `locales/ru|en` + `i18n`; slash → registry/i18n; панель → `chetbot_ui_lang` словари.
5. Тесты cores/routes с временными `*_DB_PATH` и очисткой `_cache` settings.
6. Новые модули: opt-in `enabled`, запись в `MODULE_SETTINGS_GETTERS` если нужен sidebar hide, при необходимости `MODULE_ROOT_COMMANDS`.
7. **Не** встраивать Lookup в `main.py` / текущий dashboard process.
8. **Не** публиковать этот `ARCHITECTURE.md` на сайт и не линковать из маркетингового README.
9. Main-guild фичи помечать явно (CTD, news).
10. Секреты только в ENV; никогда не коммитить `.env` и не вставлять токены в docs.

---

## 20. Быстрый чеклист «куда смотреть»

| Вопрос | Файл |
|:---|:---|
| Порядок загрузки бота | `main.py` |
| HTTP app wiring | `dashboard/backend/app.py` |
| Права | `dashboard/backend/access.py`, middleware |
| Slash ↔ modules | `slash_modules.py` |
| Настройки | `bot/core/settings_db.py` |
| UI routes | `dashboard/frontend/src/App.tsx` |
| Sidebar | `DashboardShell.tsx` `NAV_GROUPS` |
| Публичные docs сайта | `pages/docs/` + `Docs.tsx` — **не** этот файл |
| Lookup SPA routes | `lookup/src/App.tsx` |
| Lookup API / TokenPool | `lookup-api/app.py` `TokenPool` |
| Plugins catalog | `lookup-api/plugins.json` |
| Lookup run / proxy | `lookup/RUN.md`, `lookup-api/RUN.md`, `lookup-api/PROXY.md` |
| VPS bot+Lookup | `update.sh` → `scripts/update.sh` (systemd `cheterin-bot` + `cheterin-lookup`) |
| Lookup leftover (CAPTCHA / токены) | §18 этой карты |
| What’s New | `whatsNew.ts` |

---

*Конец внутренней карты. Обновляйте при смене load_extension списка, MODULE_NAME, публичных маршрутов или process model.*
