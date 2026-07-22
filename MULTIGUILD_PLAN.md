# План перехода к фазе «общий доступ» (мульти-серверный бот уровня MEE6)

> Статус: **утверждён, ВЫПОЛНЕН (22.07.2026)** — фазы 0.1, 1, 2 (включая 2.4), 2b и 3 (3.1 + 3.2(1–5)) закрыты. Фаза 0.2 (масштаб: шардинг/Postgres) сознательно отложена до роста числа серверов. Этот файл — источник истины для всех сессий работ.
> Мейн-сервер (он же «Основной/Супер/Сервер 404»): **ID 1324239354154975252**.

## Принятые решения (зафиксированы с владельцем)

| Вопрос | Решение |
|---|---|
| Доступ к дашборду сервера | Право **Manage Server / Administrator** на этом сервере (модель MEE6, без .env-списков ролей) |
| Хранилище настроек модулей | Единый **SQLite `settings.db`**: таблица `(guild_id, module, json)` |
| Языки | Полный перевод RU/EN: UI (~550 строк) + сообщения бота (~1600) + карточки игр (~1240) + Docs (1819 строк) |
| Модель языка | Два независимых уровня: язык UI — личный выбор пользователя (кнопка в шапке, localStorage); язык бота — настройка сервера в панели |

## Текущее состояние (историческая справка на старте плана — УСТАРЕЛО)

> **Актуально на 22.07.2026:** фазы 0.1–3 выполнены (см. шапку). Ниже — снимок «до миграции» для контекста; не использовать как чеклист.

<details><summary>Снимок до миграции (не актуален)</summary>

- `main.py` требует `GUILD_ID` из .env; команды синхронизируются только на этот сервер (`tree.copy_global_to`).
- OAuth: scope только `identify`; callback жёстко проверяет членство на одном сервере + роли из `DASHBOARD_ACCESS_ROLE_IDS` (.env).
- `app["guild_id"]` — один на всё приложение; ~25 файлов роутов читают его.
- **10 плоских конфигов** без измерения guild: automod, bunker, daily_topic, family, mafia, xp (+ giveaways/supply data, lockdown backup).
- **Плоские data-файлы** без guild: events_data, brackets_data, reaction_roles, buttons_config, feedback_categories, invites_stats, moderation_log, news_relay, voice_panel, serverlog_config, streams_config, embed_templates, xp_card_bg.png.
- ~~**`stats.db`: `xp_members(user_id PK)` и `voice_sessions(user_id)` — БЕЗ guild_id вообще** (XP сейчас глобальный). `audit_log` — тоже без guild.~~ → **устранено в 2.2а**.
- Уже имеют guild_id: mafia.db/bunker.db (games), warns.db, private_rooms.db, family.db (частично).
- Супер-админ: хардкод роли `1505359848433516734`, проверяется на единственном сервере.
- CTD: `memobb.py` + `CTD_ROLE_ID`/`CTD_CHANNEL_ID` в config.json.
- Ретрансляция новостей: `news.py` + `news_relay.json`, страница в общем меню.

</details>

---

## Фаза 0 — Ускорение и устойчивость бота (перформанс и нагрузка, всё в одном месте)

> Статус: **0.1 ВЫПОЛНЕНО (21.07.2026), 0.2 сознательно отложено**. Найдено при разборе вопроса
> «насколько бот может виснуть/глючить при включении всех функций». Решение сессии 21.07: чинить 0.1
> точечно сейчас, отдельно от 0.2 (масштаб — шардинг/Postgres/health-метрики обсуждаются отдельно,
> когда встанет вопрос роста числа серверов). Объединяет находки ревью 20.07 (0.1) и то, что раньше
> было отдельной «Фазой 4» (0.2) — тематически один и тот же вопрос («не ложился от перенагрузки»).

### 0.1 Точечные фиксы (найдено 20.07, исправлено 21.07)

1. ✅ **Рендер PNG в Вордле блокировал весь event loop.** `wordle_card.render_playing_card` /
   `render_summary_card` вызывались напрямую в `wordle.py`, без `asyncio.to_thread` — в отличие от
   `/ранг` (`xp.py`), где рендер уже вынесен в поток. Pillow — синхронный CPU-bound код: на время
   отрисовки карточки блокировался весь бот на всех серверах. **Исправлено**: оба вызова обёрнуты в
   `asyncio.to_thread` в `wordle.py`.
2. ✅ **SQLite без WAL, синхронный драйвер.** 10 отдельных `.db`-модулей (`economy_db`, `stats_db`,
   `wordle_db`, `bunker_db`, `mafia_db`, `warns_db`, `family_db`, `ban_db`, `voice_db`, `casino_db`)
   не включали `PRAGMA journal_mode=WAL`. **Исправлено**: во всех `connect()`/`db_connect()` добавлены
   `PRAGMA journal_mode=WAL` и `PRAGMA busy_timeout=5000`. Пересекается с пунктом «SQLite: WAL везде»
   в 0.2 — там же остаётся более масштабный `busy_timeout`/writer-паттерн под Postgres-переход.
3. ✅ **Только 2 из 9 фоновых `tasks.loop` были защищены от падения** (`wordle.py`, `daily_topic.py` —
   `try/except` + `@loop.error`). **Исправлено**: тот же паттерн (тело в `try/except`, `@loop.error`
   логирует и рестартует цикл) добавлен во все оставшиеся 8 циклов в 7 файлах: `voice_tracker.py`
   (`_tick`, `_prune`), `automod.py` (`_cleanup_repeat_cache`), `button.py` (`_cleanup_cooldowns`),
   `memobb.py` (`_auto_close_tickets`, CTD), `spam.py` (`_cleanup_cache`), `streams.py` (`_poll`),
   `family_birthdays.py` (`birthday_loop`).

**Итог 0.1**: все 3 находки устранены точечно, без изменения видимого поведения бота; полный прогон
1260 backend + 232 frontend тестов зелёный.

### 0.2 Для будущего масштаба (было «Фаза 4», актуально по мере роста числа серверов)

- `commands.AutoShardedBot` — включить заранее (без вреда на малых числах; Discord потребует шардинг с ~2500 серверов).
- `chunk_guilds_at_startup=False`, `member_cache_flags` по минимуму нужного; выборочный `guild.chunk()` там, где реально нужны полные списки (XP-лидерборд display, members-страница — переехать на fetch по запросу).
- SQLite: WAL везде, busy_timeout, один writer-паттерн; **точка перехода на Postgres — ~500+ активных серверов** (заложить слой доступа так, чтобы замена была локальной).
- Рейт-лимиты Discord: очереди для массовых операций (mass role assign уже фоновый — проверить на per-guild), глобальный limiter на announce-рассылки.
- **Организационное**: при 75+ серверах Discord требует верификацию бота (и одобрение privileged intents — members/message content, которые сейчас используются анти-спамом/XP). Подготовить описание использования интентов заранее.
- Health/метрики в супер-админ: число серверов, задержка gateway, размер БД.

**Статус 0.2**: сознательно отложено до момента реального роста числа серверов — точечные фиксы 0.1
(WAL, to_thread, loop.error) уже сделаны и не требуют этого захода как предпосылки.

---

## Фаза 1 — Подготовка и «уборка» фронтенда
> Статус: **ВЫПОЛНЕНО**. (Завершено в рамках текущей сессии 21.07). Ничего не ломает, сделано первой.

1. **Аудит всех страниц дашборда** (`dashboard/frontend/src/pages/*.tsx`): убрать формулировки «импортировано/перенесено из другого бота», «как в X-боте» и т.п.; каждой странице — вводный абзац «что это и зачем» (по образцу страниц Бункер/Мафия).
2. **Лимиты — явно на страницах**, рядом с полями ввода. Известные лимиты для выписывания:
   - Игры: таймеры 10–3600 сек; Мафия 5–99 игроков; Бункер 4–20 игроков, вместимость 1–20, заметка к спец. возможности ≤300 символов.
   - Ежедневная рубрика: формат времени HH:MM, число тем/времён.
   - Автомод: пороги фильтров, длительности мьютов (кап таймаута Discord — 28 дней), сроки сгорания варнов.
   - XP: множители, лимиты наград; welcome/embed-builder: лимиты Discord (title 256, description 4096, footer 2048, ≤25 полей).
   - Пройти каждую страницу и выписать лимиты из валидации роутов (`routes/*.py` — там источники истины).
3. **Docs.tsx**: удалить разделы «Супер-админ» и «Для разработчиков» (id `superadmin`, `developers`/`dev`) из публичной документации; супер-админ функции описываются только внутри самой панели супер-админа.

Приёмка: ни одного упоминания стороннего происхождения функционала; на каждой странице с полями — видимые лимиты; в Docs нет двух разделов.

---

## Фаза 2 — Мульти-серверное ядро (пункты ТЗ №6, №7)

### 2.1 Хранилище настроек: `settings_db.py` (✅ ВЫПОЛНЕНО)

- Новый модуль `settings_db.py`: таблица `module_settings (guild_id INTEGER, module TEXT, data TEXT/json, updated_at, PRIMARY KEY(guild_id, module))`. SQLite с `PRAGMA journal_mode=WAL` и `busy_timeout`.
- API: `get(guild_id, module, default)` / `put(guild_id, module, data)` — заменяет все `load_config/save_config` в `*_core.py`.
- Каждый `*_core.get_settings()` → `get_settings(guild_id)`. Кэш mtime-паттерн уходит; вместо него простой in-memory кэш `{(guild_id, module): data}` со сбросом при put.
- **Миграция**: одноразовый скрипт при старте — все существующие плоские JSON (automod, bunker, daily_topic, family, mafia, xp, serverlog, streams, welcome-настройки из config.json и т.д.) записываются как настройки guild_id=1324239354154975252, файлы переименовываются в `*.migrated.bak`.

### 2.2 Данные модулей: guild-измерение

Таблица преобразований (каждый пункт — отдельный подшаг с тестами):

| Хранилище | Сейчас | Что делаем |
|---|---|---|
| `stats.db` xp_members | ✅ PK (guild_id, user_id) | **ВЫПОЛНЕНО (2.2а)**: миграция старых строк → guild 404 в `stats_db.init()`; все `xp_*` получили guild_id; лидерборды/ранги per-guild; тесты `test_stats_db.py` (изоляция + миграция) |
| `stats.db` voice_sessions | ✅ + guild_id | **ВЫПОЛНЕНО (2.2а)**: миграция `ADD COLUMN guild_id DEFAULT 404`; `voice_session_add`/`voice_sessions_since` per-guild, prune глобальный |
| `stats.db` audit_log | ✅ + guild_id | **ВЫПОЛНЕНО (2.2а)**: `audit_add`/`audit_list`/`audit_count` per-guild; middleware пишет `request.app["guild_id"]` |
| `xp_card_bg.png` | ✅ `card_bgs/card_bg_<guild_id>.png` | **ВЫПОЛНЕНО (2.2а)**: `xp_core.get_card_bg_path(guild_id)`, `xp_card.render` берёт фон по guild_id |
| `events_data.json`, `brackets_data.json` | ✅ settings.db (events/brackets) | per-guild (2.1) |
| `reaction_roles.json`, `buttons_config.json`, `embed_templates.json` | ✅ settings.db | **2.2б**: `buttons`/`embed_templates` — чинили сломанную half-миграцию (load читал плоский файл + отсутствовал import settings_db) + тесты CRUD |
| `feedback_categories.json`, `invites_stats.json`, `moderation_log.json` | ✅ settings.db | per-guild (2.1) |
| `supply_data.json`, `giveaways_data.json` | ✅ settings.db | **2.2б ВЫПОЛНЕНО**: `supply_core`/`giveaway_core` переведены на per-guild (guild_id в каждой функции, запись `guild_id` в записи, таймеры/recovery когов по (guild_id, id), роуты + тесты изоляции) |
| `voice_panel.json` | ✅ settings.db | **2.2б ВЫПОЛНЕНО**: состояние панели — синглтон мейн-сервера в settings_db (voice_rooms) + тест |
| `antispam_backup.json`, `serverlog_config.json`, `streams_config.json` | ✅ settings.db | per-guild (2.1) |
| `config.json` (bot_config: ID каналов/ролей) | плоский | per-guild (module='config'); CTD-ключи — см. Фазу 2b |
| mafia/bunker/warns/private_rooms БД | ✅ проверено (2.2б) | guild_id есть; поиск по глобально-уникальным ключам (game id/message_id/channel_id, warn id) — межсерверных утечек нет, recovery использует сохранённый guild_id |
| family БД | ✅ per-guild (2.2б) | **ВЫПОЛНЕНО**: `roster_msg`/`birthday_msg` → PK `guild_id`; `pending_forms`/`tickets`/`birthdays` → композитный PK `(guild_id, user_id)`; идемпотентная миграция старой схемы → guild 404; guild_id проведён через family_db/tickets/roster/birthdays коги и роут + тесты изоляции/миграции |

### 2.3 Авторизация и выбор сервера (пункт №6) — ✅ ВЫПОЛНЕНО (21.07.2026)

- OAuth scope: `identify guilds`. В сессии дополнительно храним `access_token`/`refresh_token`/`expires_at` (cookie-сессия шифрованная).
- **Callback больше не проверяет членство одного сервера** — просто логинит и редиректит на `/servers`.
- Новые эндпоинты:
  - `GET /api/auth/guilds` — список серверов пользователя из Discord API (`/users/@me/guilds`), фильтр `permissions & MANAGE_GUILD|ADMINISTRATOR`, каждому флаг `has_bot` (по `bot.get_guild`). Кэш 60 сек на пользователя (рейт-лимиты Discord).
  - `POST /api/auth/select-guild {guild_id}` — серверная проверка: бот на сервере И пользователь реально имеет Manage Server там (resolve_guild_member + guild_permissions — не доверяем только OAuth-списку). Пишет `session["active_guild_id"]`.
  - `GET /api/auth/invite-url?guild_id=` — `https://discord.com/oauth2/authorize?client_id=…&scope=bot%20applications.commands&permissions=<битмаска>&guild_id=…` (битмаску прав собрать по фактическим нуждам модулей: manage_roles, manage_channels, ban/kick/moderate_members, manage_messages, send/embed/attach, connect/move_members, view_audit_log, manage_webhooks).
- `access_middleware`/`require_dashboard_access`: берёт `active_guild_id` из сессии → `request["guild_id"]`; проверка = Manage Server/Admin на этом сервере. `DASHBOARD_ACCESS_ROLE_IDS` удаляется из REQUIRED_KEYS (.env, .env.example, config.py, тесты).
- Механическая замена в ~25 роутах: `request.app["guild_id"]` → `request["guild_id"]`.
- Супер-админ: проверка всегда против МЕЙН-сервера (константа `MAIN_GUILD_ID = 1324239354154975252` в `access.py`) + существующая роль.
- **Frontend**: страница `/servers` (карточки серверов: иконка, имя, «Настроить» или «Добавить бота»); в шапке DashboardShell — переключатель текущего сервера (dropdown, ведёт на select-guild + перезагрузка данных). `/api/auth/me` возвращает и активный сервер.

### 2.4 Бот: отвязка от GUILD_ID (пункт №7) — ✅ ВЫПОЛНЕНО (21.07.2026)

- ✅ `main.py`: `GUILD_ID` больше не обязателен (helper `get_main_guild_id()`: `GUILD_ID` → `MAIN_GUILD_ID` → дефолт мейна). Убраны `copy_global_to`/`clear_commands(guild=None)`; теперь глобальный `tree.sync()` + одноразовая очистка старых guild-скоуп команд мейна (`clear_commands(guild=main)` + пустой `sync(guild=main)`), чтобы участники мейна не видели дубли. Миграция плоских конфигов/ENV привязана к мейн-серверу.
- ✅ Коги читают настройки по `guild_id` из события: `tempban`, `welcome`, `daily_topic`, `giveaways`, `supply`, `family`, `reaction_roles` — все per-guild.
- ✅ Планировщики цикл по `bot.guilds`: daily_topic (расписание), tempban (recovery-разбан на всех серверах), giveaways/supply/family (уже итерировали гильдии).
- ✅ Приветствия (`welcome.py`): канал/тумблеры/тексты строго из настроек сервера события; захардкоженное имя «Server 404» в приветственной ЛС → `guild.name`. Покрыто `test_welcome_cog.py` (публичное сообщение, ЛС-заголовок, тумблеры, изоляция между серверами).
- ✅ `tempban`: текст ЛС об исключении теперь использует `guild.name` вместо захардкоженного «404 : Server Not Found».
- ✅ `reaction_roles`: очистка «мёртвых» записей перенесена из `setup()` (один `GUILD_ID`) в `on_ready` — по всем `bot.guilds`, один раз за процесс.
- ✅ `feedback_menu`: категории/счётчики кейсов per-guild — `get_feedback_categories(guild_id)`; панель-`View` строится под сервер публикации, коллбэк резолвит категорию по `interaction.guild_id`; on_ready регистрирует `View` для каждого сервера с категориями. Исправлен баг вызова `get_next_case_id` (не хватало `guild_id`).
- ✅ `on_guild_join`: реактивирует настройки (`settings_db.set_guild_active(True)`) + приветствие в system channel/владельцу со ссылкой на дашборд. `on_guild_remove`: `set_guild_active(False)` — настройки помечаются неактивными, не удаляются.
- Восстановление игр (mafia/bunker recover_games) уже guild-aware через games.guild_id.

> ~~Примечание (долг, вне 2.4): `feedback_menu.create_feedback_case` пишет кейсы в `bot.feedback_cases` (плоский стор + `update_file`), тогда как чтение/решение/восстановление идут через `settings_db` per-guild — предсуществующая рассинхронизация хранилищ, устранять отдельной задачей.~~ → **УСТРАНЕНО (21.07.2026)**: `create_feedback_case` пишет кейс в `settings_db.put(guild.id, "feedback_cases", …)`; счётчик обращений участника в `routes/moderation.py` (`serialize_member_detail`) читает из `settings_db` per-guild (`request["guild_id"]`), а не из плоского `bot.feedback_cases`. Тест `test_member_detail.py` сидит через `settings_db`.
>
> **Дополнительно (21.07.2026):** там же в `serialize_member_detail` инвайт-статистика читалась из несуществующего в проде `bot.stats` → карточка участника в дашборде падала с 500. Исправлено на per-guild `settings_db.get(guild_id, "invites_stats").stats` (совпадает с записью в `welcome.py`). Атрибуты `bot.stats`/`bot.feedback_cases`/`bot.update_file` в проде больше не используются (остались только в фейках тестов).

### Приёмка Фазы 2
- Бот работает одновременно на ≥2 серверах с разными настройками каждого модуля; действия на сервере A ничего не меняют на B.
- Логин → выбор сервера → настройка; человек без Manage Server видит «нет доступа» именно к этому серверу; кнопка «Добавить бота» работает.
- Все 870+ существующих тестов адаптированы (fakes: несколько FakeGuild), новые тесты изоляции per-guild.

---

## Фаза 2b — Привилегии мейн-сервера (пункты ТЗ №4, №5) — ✅ ВЫПОЛНЕНО (21.07.2026)

**Итог:** CTD и ретрансляция новостей стали привилегиями основного сервера; тесты зелёные (backend 1330, frontend 245).

- **CTD** (`memobb.py`): команда `/ctd_setup` привязана к мейну через `@app_commands.guilds` (+ рантайм-гард `_is_main_guild` во всех вьюхах/командах, авто-закрытие тикетов по `MAIN_GUILD_ID`). `main.py`: глобальный `tree.sync()` + отдельный `sync(guild=main)` пушит команды-привилегии мейна и заодно вычищает старые guild-дубли. Ключи `CTD_*` убраны из `/api/config`; заведён отдельный роут `/api/ctd` (доступен только когда активный сервер == мейн приложения, иначе `not_main_guild`) и страница «Тикеты CTD» (пункт меню виден по `is_main_guild`). В `/api/auth/me` добавлен флаг `is_main_guild`.
- **Ретрансляция** (`news.py`): роут `/api/news` переведён на `require_super_admin`; настройки читаются/пишутся под мейн-сервером (`request.app["guild_id"]`), целевые и лог-каналы валидируются на принадлежность мейну (`target_channel_not_found` / `log_channel_id_not_found`). Источником может быть любой сервер. `_main_guild_id()` резолвится единообразно с `main.get_main_guild_id()`. В дашборде «Ретрансляция новостей» перенесена в раздел «Супер-админ».
- **Docs**: разделы CTD и ретрансляции помечены как функции основного сервера (Note-блоки), инструкция по CTD ссылается на отдельный раздел вместо общей конфигурации.

<details><summary>Исходное ТЗ фазы</summary>

1. **CTD** (`memobb.py`): ког активен только при `guild.id == MAIN_GUILD_ID`; страница CTD-настроек в дашборде видна только когда выбран мейн-сервер; ключи CTD из общего config-роута убрать.
2. **Ретрансляция новостей** (`news.py`):
   - Страницу «Ретрансляция новостей» убрать из общего меню; перенести в раздел «Супер-админ» (доступ по существующей супер-админ проверке).
   - Логика: слушать источники на ЛЮБЫХ серверах (source_guild_id — любой), публиковать ТОЛЬКО в каналы мейн-сервера (валидация target_channel_id ∈ мейн).
   - `news_relay.json` → settings.db под guild_id мейна.
3. Docs: упоминания CTD/ретрансляции пометить как «функции основного сервера» или убрать из публичных доков.

</details>

---

## Фаза 3 — Двуязычность RU/EN (пункт ТЗ №2)

### 3.1 Инфраструктура — ✅ ВЫПОЛНЕНО (22.07.2026)

- **Frontend**: `src/i18n/{ru,en}.ts`, `translate()`, `LanguageProvider`, `useT()`, `LanguageToggle` (RU/EN в шапке дашборда и PublicLayout), выбор UI-языка в `localStorage`.
- **Backend/бот**: `i18n.py` + `locales/{ru,en}.py`, `language_core.py` (settings.db module `language`), роут `GET/PUT /api/language`.
- **Дашборд**: страница «Настройки сервера» (`/settings`) — выбор языка бота для текущего сервера.
- **Публичные игры**: `language` в `/api/public/mafia/{token}` и `/api/public/bunker/{token}` (язык сервера игры).
- **Shell переведён**: навигация DashboardShell, ServerSelect, PublicLayout header/footer.

### 3.1 (исходное ТЗ)
- **Frontend**: лёгкий самописный словарь (`src/i18n/ru.ts`, `src/i18n/en.ts`, хук `useT()`), контекст `LanguageProvider`, выбор в localStorage, кнопка RU/EN в шапке DashboardShell. Без тяжёлых библиотек.
- **Backend/бот**: `i18n.py` — `t(key, lang, **fmt)`; словари `locales/ru.py`, `locales/en.py`. Язык сервера: `settings.db (guild_id, 'language')`, дефолт `ru`; настройка на странице «Настройки сервера».
- Публичные страницы игроков (мафия/бункер по токену): язык = язык сервера игры (передаётся в public-state).

### 3.2 Объёмы работ (порциями, каждая — сессия)
1. UI дашборда: ~550 строк → ключи словаря (страница за страницей, тесты по обоим языкам выборочно).
2. Сообщения бота: ~1600 строк по когам (embeds, ответы команд, ЛС).
3. **Slash-команды**: базовые имена → английские (`/bunker-game`, `/mafia-game`, `/giveaway`…), русские — через `name_localizations`/`description_localizations` (`discord.app_commands.locale_str`). ВНИМАНИЕ: смена базовых имён = новые команды для пользователей; объявить заранее.
4. Карточки игр: `bunker_data.py` — каждая запись получает `name_en` (и `effect_en`, `description_en` где есть); генерация персонажа сохраняет оба языка в карточку, отображение по языку.
5. Docs.tsx: структура секций дублируется EN-версией; переключатель языка работает и на /docs (публичной).

### Приёмка: переключение в дашборде мгновенно меняет весь UI; сервер с language=en получает все сообщения бота на английском, включая карточки Бункера и имена команд.

---

## Порядок выполнения (по сессиям)

| # | Сессия | Содержание |
|---|---|---|
| 0 | Фаза 0.1 | ✅ ВЫПОЛНЕНО (21.07.2026) — to_thread, WAL, loop.error; 0.2 (масштаб) отложено |
| 1 | Фаза 1 | ✅ ВЫПОЛНЕНО (21.07.2026) — тексты, лимиты, чистка Docs |
| 2 | 2.1 | ✅ ВЫПОЛНЕНО (21.07.2026) — settings_db + миграция конфигов + перевод *_core на guild_id |
| 3 | 2.2а | ✅ ВЫПОЛНЕНО (21.07.2026) — stats.db (XP/voice/audit) + xp_card_bg per-guild + миграция → guild 404 + test_stats_db.py |
| 4 | 2.2б | ✅ ВЫПОЛНЕНО (21.07.2026) — supply/giveaway/voice_panel → settings_db per-guild; починена half-миграция buttons/embed_templates; проверены mafia/bunker/warns/private_rooms; **family полностью переведена на per-guild** (композитные PK + миграция → 404) |
| 5 | 2.3 | ✅ ВЫПОЛНЕНО (21.07.2026) — OAuth `identify guilds` + токены/refresh; логин без проверки членства → `/servers`; `/api/auth/{guilds,select-guild,invite-url}`; доступ = Manage Server (роль-списки опциональны, переходный грант); per-request `guild_id` (guild_context_middleware, ~200 call sites); супер-админ на мейне; фронтенд ServerSelect + гейт выбора сервера |
| 6 | 2.4 | ✅ ВЫПОЛНЕНО (21.07.2026) — коги/планировщики per-guild, global sync, on_guild_join / on_guild_remove |
| 7 | 2b | ✅ ВЫПОЛНЕНО (21.07.2026) — CTD gate (guild-bound `/ctd_setup` + `/api/ctd` только на мейне) + news → супер-админ с валидацией целевых каналов мейна + `is_main_guild` в me + Docs-пометки |
| 8 | 3.1+3.2(1) | ✅ ВЫПОЛНЕНО (22.07.2026) — i18n infra + модульные словари (`shell`, `common`, `auth`, `activity`, `admin`, `community`); все страницы дашборда через `useT()`; Login/AccessDenied/NotFound/Leaderboard; переключатель RU/EN в шапке; 253 frontend + 1340 backend тестов |
| 9 | 3.2(2) | ✅ ВЫПОЛНЕНО (22.07.2026) — все коги бота на `i18n.lang_for()` + модульные `locales/{ru,en}/*` (~30 модулей); `guild_t()` / `module_disabled()` / `pick_random()`; core-хелперы (`economy_core.bet_error`, `casino_core.bet_error`, `wordle_core.guess_error`); исключено из scope: `bunker_data.py` (→ 3.2(4)), slash-имена (→ 3.2(3)); **1343** backend-тестов |
| 10 | 3.2(3) | ✅ ВЫПОЛНЕНО (22.07.2026) — `slash_i18n.py` + `slash_registry.py` + `locales/{ru,en}/slash.py`; `name_localizations` / `description_localizations` для всех slash-команд и групп (~59 ключей); генератор `scripts/gen_slash_locales.py` |
| 11 | 3.2(4) | ✅ ВЫПОЛНЕНО (22.07.2026) — `bunker_data_en.py` + `bunker_localize.py`; генерация карточек с RU+EN полями; отображение по `language` (бот, public API, card-pools) |
| 12 | 3.2(5) | ✅ ВЫПОЛНЕНО (22.07.2026) — Docs RU/EN: `sectionsRu.tsx` / `sectionsEn.tsx`, переключатель на `/docs` |

## Риски и страховки

1. **Все пользователи дашборда должны перелогиниться** после смены OAuth-scope (сессии со старым scope без токена guilds — принудительный logout).
2. **Глобальные команды распространяются до 1 часа**; старые guild-команды мейна очистить, иначе дубли в списке.
3. Смена имён команд на EN (Фаза 3) — «переучивание» пользователей мейна; объявить в новостях сервера.
4. Перед каждой миграцией БД — автоматический бэкап файла (`*.bak-<дата>`); миграции идемпотентны (по образцу bunker_db PRAGMA-миграции).
5. Мейн-сервер не должен деградировать ни в один момент: каждая сессия заканчивается полным прогоном тестов + ручной проверкой ключевых флоу мейна.
6. XP-миграция: весь текущий (глобальный) XP присваивается мейн-серверу — согласовано по умолчанию, other-серверы начинают с нуля.

## Соответствие пунктам ТЗ

| Пункт ТЗ | Где в плане |
|---|---|
| 1. Чистка текстов, описания, лимиты | Фаза 1 |
| 2. RU/EN + кнопка | Фаза 3 |
| 3. Убрать супер-админ/разработчиков из доков | Фаза 1 |
| 4. CTD только на мейне | Фаза 2b |
| 5. Ретрансляция → супер-админ, публикация только на мейн | Фаза 2b |
| 6. Выбор сервера при входе + добавление бота | Фаза 2.3 |
| 7. Независимость модулей от мейна | Фаза 2.1–2.4 |
| «Не ложился от перенагрузки» | Фаза 0 |
