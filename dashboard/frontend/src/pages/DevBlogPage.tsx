import { PublicLayout } from '../components/PublicLayout'
import { useLanguage } from '../context/LanguageContext'

/* ------------------------------------------------------------------ */
/* Blog data types                                                      */
/* ------------------------------------------------------------------ */
interface BulletItem {
  lead: string
  body: string
}

interface BlogEntry {
  date: string
  title: string
  bullets: BulletItem[]
}

/* ------------------------------------------------------------------ */
/* English entries                                                      */
/* ------------------------------------------------------------------ */
const BLOG_EN: BlogEntry[] = [
  {
    date: 'July 1, 2026',
    title: 'Project Birth: First Commit & Dashboard Phase 1',
    bullets: [
      {
        lead: 'History begins.',
        body: 'First Cheterin bot snapshot committed — existing working code enters version control as phase zero.',
      },
      {
        lead: 'Backend scaffolded.',
        body: 'Config validation, Discord OAuth2 (login / callback / logout / /me), Fernet session key derivation, and graceful startup written from scratch.',
      },
      {
        lead: 'Guild access control.',
        body: 'has_dashboard_access function with full test coverage; require_dashboard_access decorator shared across all protected API routes.',
      },
      {
        lead: 'Members API.',
        body: 'Search and pagination, per-member detail cards, ban and kick endpoints with Discord error mapping.',
      },
      {
        lead: 'Vite + React + TypeScript frontend.',
        body: 'Tailwind v4, typed fetch wrapper, vitest configuration, AuthContext, ProtectedRoute, and the first dashboard shell.',
      },
      {
        lead: 'Design system pass.',
        body: 'Unified charcoal-dark layout applied across login, access-denied, and dashboard shell pages on day one.',
      },
    ],
  },
  {
    date: 'July 2–3, 2026',
    title: 'Moderation, Roles & Embed Builder',
    bullets: [
      {
        lead: 'Lockdown module.',
        body: 'Antispam core extracted for reuse; lockdown activate/deactivate API routes with partial-failure audit logs.',
      },
      {
        lead: 'Mass role assignment.',
        body: 'Background job orchestration with TOCTOU-safe guard, member ID cap at 1000, and modal wired into the Members page.',
      },
      {
        lead: 'Reaction Roles.',
        body: 'Full CRUD with Discord channel/message validation, unicode emoji support, and server custom emoji picker.',
      },
      {
        lead: 'Embed builder.',
        body: 'Build/parse/validate with 6000-char aggregate budget, live preview pane, role buttons (up to 5), and both send and edit modes.',
      },
      {
        lead: 'Feedback module.',
        body: 'Cases list and detail view, approve/deny decisions, custom form-field categories, and one-click publish panel to Discord.',
      },
    ],
  },
  {
    date: 'July 4–7, 2026',
    title: 'Events, Brackets & Early Games',
    bullets: [
      {
        lead: 'Events and polls.',
        body: 'Discord join-button events, multiple-choice polls, and giveaways with auto winner pick and reroll.',
      },
      {
        lead: 'Tournament brackets.',
        body: 'Single and double elimination, round robin (up to 20 participants); public share link for spectators.',
      },
      {
        lead: 'Mafia game.',
        body: 'Bot cog with lobby start, night/day phases; personal player dashboard links for role cards, night actions, and daytime vote.',
      },
      {
        lead: 'Bunker game.',
        body: 'Character cards with profession/health/phobia/backpack; free trait reveals; special ability requests applied by host from the panel; card editor.',
      },
      {
        lead: 'Economy core.',
        body: 'Server currency earned from activity, role shop, peer transfers, daily rewards, weekly reports.',
      },
    ],
  },
  {
    date: 'July 8–14, 2026',
    title: 'Voice Rooms, Streams, Fun & More Modules',
    bullets: [
      {
        lead: 'Fun module.',
        body: 'Russian roulette (cylinder never respins — odds rise 1/6 → 1/1), emoji roulette, quote PNG generator (avatar + name + text).',
      },
      {
        lead: 'Wordle.',
        body: 'Daily Russian 5-letter Wordle with shared server board, per-player private cards, /wordle-stats, /wordle-top, and a daily announcement.',
      },
      {
        lead: 'Private voice rooms.',
        body: 'Join-lobby → auto-created room; control panel published to a Discord channel; voice activity statistics by hour, channel, and member.',
      },
      {
        lead: 'Casino.',
        body: 'Slots, blackjack, and coinflip with per-server economy integration and casino leaderboards.',
      },
      {
        lead: 'Stream alerts.',
        body: 'YouTube new-video alerts, TikTok video and LIVE alerts, Twitch live alerts — per-subscription embed and ping settings.',
      },
      {
        lead: 'Family module (GTA5RP).',
        body: 'Member roster by roles, join-ticket applications, birthday calendar with congrats announcements.',
      },
    ],
  },
  {
    date: 'July 15–22, 2026',
    title: 'Multi-Guild Isolation & Community Modules',
    bullets: [
      {
        lead: 'Multi-guild Phase 1.',
        body: 'Full per-guild settings isolation across every module; bot loads config by guild_id on each event without cross-contamination.',
      },
      {
        lead: 'Multi-guild Phase 2.',
        body: 'OAuth guild switcher in the dashboard, per-guild command sync, CTD and news main-guild privileges preserved.',
      },
      {
        lead: 'Community module stack.',
        body: 'Auto-reactions, scheduled messages, sticky messages, custom commands, starboard, timed roles — all configurable per guild.',
      },
      {
        lead: 'i18n foundation.',
        body: 'All dashboard strings dual-tracked in Russian and English; bot reply language set per guild from server settings.',
      },
      {
        lead: 'Multiguild isolation bugs fixed.',
        body: 'Additional community modules added; roulette empty-cylinder edge case resolved.',
      },
    ],
  },
  {
    date: 'July 24–25, 2026',
    title: 'UI Refresh & Credits',
    bullets: [
      {
        lead: 'Dashboard redesign.',
        body: 'New layout cards, sidebar navigation, and color system applied across every panel page.',
      },
      {
        lead: 'Credits page.',
        body: 'Team roster, open-source project credits, and contact links for Cheterin Group.',
      },
    ],
  },
  {
    date: 'August 2–3, 2026',
    title: 'ValChecker, /help & Games Dashboard',
    bullets: [
      {
        lead: 'ValChecker module.',
        body: 'Valorant stats, tracked match auto-posting, /val commands, and a hardened Henrik API poller with server-status alerts.',
      },
      {
        lead: '/help command.',
        body: 'Per-guild module-aware help embed; bot presence set to "Playing /help • Cheterin".',
      },
      {
        lead: 'Games dashboard section.',
        body: 'ValChecker settings, poller interval, match and alert channel selectors — all in a new Games tab.',
      },
      {
        lead: 'Runtime DB gitignore.',
        body: 'SQLite runtime databases removed from tracking so git pull no longer clobbers live data.',
      },
    ],
  },
  {
    date: 'August 12–17, 2026',
    title: 'TikTok Streams, Dynamic Banners & Customs',
    bullets: [
      {
        lead: 'TikTok LIVE.',
        body: '~2 min detection latency; fixed EU block pages and stale envelope state; first alert fires immediately after subscribe.',
      },
      {
        lead: 'Separate TikTok embed styles.',
        body: 'Independent embed color, template, and ping settings for LIVE alerts vs new video alerts per subscription.',
      },
      {
        lead: 'Dynamic server banner.',
        body: 'Auto-generated banner showing top active voice member, total member count, and who is currently in voice.',
      },
      {
        lead: 'Scheduled banner and icon rotation.',
        body: 'Upload a playlist of banners and icons; the bot rotates them on a configurable schedule managed from the dashboard.',
      },
      {
        lead: 'Customs module.',
        body: 'VALORANT custom lobbies: rank display, map voting, voice channel assignment, scores, and schedule management.',
      },
      {
        lead: 'Level-role replace.',
        body: 'Optional setting to remove the previous level role when a member levels up, keeping the role list clean.',
      },
      {
        lead: 'Guild-scoped VALORANT.',
        body: 'Customs roster with nickname display, banner controls, Premier applications, and role panels — all isolated per guild.',
      },
    ],
  },
  {
    date: 'August 19–22, 2026',
    title: 'Relations, Riot Verification & Discord v2 Embeds',
    bullets: [
      {
        lead: 'Relations module.',
        body: 'Pair HP from actions (hug, kiss, slap, pat, and more), romance level system up to 11, marriages with proposals, /relations commands.',
      },
      {
        lead: 'Relations validation fix.',
        body: 'Default level thresholds corrected; PUT validation no longer silently resets fields.',
      },
      {
        lead: 'Riot domain verification.',
        body: '/riot.txt endpoint and a second DH record at /dh added — required for Valorant API certification.',
      },
      {
        lead: 'Discord Components v2.',
        body: 'Embed builder now supports Components V2 messages (Container / Text Display layout) in addition to classic embeds.',
      },
      {
        lead: 'Twitch UI 2.0.',
        body: 'Subscription cards and the stream embed editor redesigned for clarity.',
      },
    ],
  },
  {
    date: 'September 6, 2026',
    title: 'Cheterin Lookup Launch',
    bullets: [
      {
        lead: 'Lookup SPA.',
        body: 'Standalone React app at /lookup — Discord user, bot, and server lookup, no panel login required, no bot membership needed.',
      },
      {
        lead: 'Lookup API.',
        body: 'Isolated Flask process with its own Discord token, rate-limit protection, and CAPTCHA gating for burst traffic.',
      },
      {
        lead: 'Plugins hub.',
        body: 'Unified catalog for built-in tools (Snowflake decoder, Permissions calculator, Avatars, Badges, Timestamps) and curated Vencord UserPlugins.',
      },
      {
        lead: 'Badge catalog.',
        body: 'Complete mezotv badge set — public flags, Nitro tiers, server boosts, special flairs, guild tag icons, Hall of Fame.',
      },
      {
        lead: 'DSA mode.',
        body: 'EU DSA Transparency Database (Discord Netherlands B.V.) integration — look up public Statements of Reasons by Discord ID.',
      },
      {
        lead: 'Charcoal-red kit.',
        body: 'Lookup adopts the same dark-red color system, brand mark, typography, and legal frame as the main Cheterin site.',
      },
      {
        lead: 'Dev Blog.',
        body: 'This page — full chronological history of Cheterin from first commit to launch.',
      },
    ],
  },
  {
    date: 'September 20–28, 2026',
    title: 'Lookup production: TokenPool, plugins & docs pipeline',
    bullets: [
      {
        lead: 'TokenPool.',
        body: 'lookup-api rotates multiple Discord tokens (LOOKUP_DISCORD_TOKENS) for round-robin resilience — still isolated from BOT_TOKEN and main.py.',
      },
      {
        lead: 'Plugins & Avatars polish.',
        body: 'Plugins hub nesting under /lookup/plugins, Avatars ID-only profile hash fetch, empty-catalog fixes.',
      },
      {
        lead: 'Engineer docs.',
        body: 'ARCHITECTURE.md and Lookup RUN/PROXY synced with production Oracle layout (chetmain / chetlookup).',
      },
      {
        lead: 'Ship pipeline.',
        body: 'Cursor rule: every product change → technical docs + Dev Blog + commit/push + update.sh deploy + production smoke.',
      },
    ],
  },
  {
    date: 'September 29, 2026',
    title: 'Bot package layout, legal refresh & cookie consent',
    bullets: [
      {
        lead: 'VALORANT-style bot/ tree.',
        body: 'Bot modules under bot/ (core, modules by domain, cards, data). main.py stays the entrypoint; dashboard and Lookup paths unchanged; Lookup still isolated.',
      },
      {
        lead: 'Docs folder.',
        body: 'ARCHITECTURE lives under docs/ only; deploy/ holds nginx process notes. Closed product plans are removed once shipped.',
      },
      {
        lead: 'Header legal strip.',
        body: 'Logged-in dashboard top nav keeps Documentation and Terms only; Privacy, Cookies, and Disclaimer move to legal-page subnav and the site footer.',
      },
      {
        lead: 'Legal subnav.',
        body: 'Shared charcoal-red tabs on Terms ↔ Privacy ↔ Cookies ↔ Disclaimer for easy cross-links.',
      },
      {
        lead: 'Cookie consent plaque.',
        body: 'Bottom banner (RU/EN) with Accept + Cookies policy link; stores chetbot_cookie_consent in localStorage; does not permanently block the app.',
      },
      {
        lead: 'Legal copy refresh.',
        body: 'Terms, Privacy, Cookies, and Disclaimer updated for bot + dashboard + Lookup, OAuth session, TokenPool, contacts (discord.gg/cheterin, turkapahf@gmail.com), last updated 29 September 2026.',
      },
      {
        lead: 'Secret hygiene.',
        body: '.env.example cleared to empty placeholders — no real tokens in the template.',
      },
    ],
  },
  {
    date: 'September 29, 2026',
    title: 'Public-prep: Apache-2.0, CI, docs i18n & systemd',
    bullets: [
      {
        lead: 'Apache License 2.0.',
        body: 'Root LICENSE with Copyright 2026 Cheterin Group — repo ready for public redistribution under Apache-2.0.',
      },
      {
        lead: 'GitHub Actions CI.',
        body: 'Push/PR to main runs dashboard backend pytest, lookup-api pytest, and production builds for dashboard + Lookup SPAs — no Discord secrets in CI.',
      },
      {
        lead: 'Docs i18n.',
        body: 'README.md English by default with README.ru.md; architecture maps as EN + RU under docs/ only (no root stubs).',
      },
      {
        lead: 'Contact email.',
        body: 'Public contact unified to turkapahf@gmail.com (footer, credits, legal).',
      },
      {
        lead: 'Full update.sh + systemd.',
        body: 'update.sh now builds dashboard and Lookup, installs lookup-api deps, and restarts cheterin-bot + cheterin-lookup units (deploy/systemd/). Replaces legacy tmux chetmain/chetlookup in docs; operator installs units on the VPS.',
      },
      {
        lead: 'Local Cursor rules.',
        body: '.cursor/rules/ gitignored and untracked — production SSH details stay on the operator machine only.',
      },
    ],
  },
]

/* ------------------------------------------------------------------ */
/* Russian entries                                                      */
/* ------------------------------------------------------------------ */
const BLOG_RU: BlogEntry[] = [
  {
    date: '1 июля 2026 г.',
    title: 'Рождение проекта: первый коммит и Phase 1 панели',
    bullets: [
      {
        lead: 'История начинается.',
        body: 'Первый снимок бота Cheterin загружен в репозиторий — рабочий код входит в систему версий как нулевая фаза.',
      },
      {
        lead: 'Бэкенд с нуля.',
        body: 'Валидация конфига, Discord OAuth2 (логин / callback / logout / /me), сессионный ключ Fernet, graceful startup.',
      },
      {
        lead: 'Контроль доступа к гильдии.',
        body: 'Функция has_dashboard_access с полным покрытием тестами; декоратор require_dashboard_access для всех защищённых маршрутов API.',
      },
      {
        lead: 'Members API.',
        body: 'Поиск и пагинация, детальные карточки участников, бан и кик с корректной обработкой ошибок Discord.',
      },
      {
        lead: 'Frontend на Vite + React + TypeScript.',
        body: 'Tailwind v4, типизированный fetch, vitest, AuthContext, ProtectedRoute и первый шелл панели.',
      },
      {
        lead: 'Первая дизайн-система.',
        body: 'Единый угольный dark-лейаут на страницах входа, «доступ запрещён» и оболочке панели — с первого дня.',
      },
    ],
  },
  {
    date: '2–3 июля 2026 г.',
    title: 'Модерация, роли и embed-редактор',
    bullets: [
      {
        lead: 'Модуль Lockdown.',
        body: 'Ядро антиспама вынесено для повторного использования; API маршруты activate/deactivate с журналом частичных сбоев.',
      },
      {
        lead: 'Массовое назначение ролей.',
        body: 'Фоновая оркестрация задач с TOCTOU-безопасной блокировкой, кап 1000 участников, модальное окно на странице Members.',
      },
      {
        lead: 'Reaction Roles.',
        body: 'CRUD с валидацией канала/сообщения Discord, поддержка unicode и кастомных эмодзи сервера.',
      },
      {
        lead: 'Embed builder.',
        body: 'Сборка/парсинг/валидация с лимитом 6000 символов, live-превью, кнопки ролей (до 5), режимы отправки и редактирования.',
      },
      {
        lead: 'Модуль Feedback.',
        body: 'Список и детали кейсов, решения одобрить/отклонить, кастомные поля формы по категориям, публикация панели в Discord.',
      },
    ],
  },
  {
    date: '4–7 июля 2026 г.',
    title: 'События, сетки и первые игры',
    bullets: [
      {
        lead: 'События и опросы.',
        body: 'События с кнопками вступления в Discord, многовариантные опросы, раздачи с авто-выбором победителей и реролом.',
      },
      {
        lead: 'Турнирные сетки.',
        body: 'Одиночное и двойное выбывание, круговой турнир (до 20 участников); публичная ссылка-сетка для зрителей.',
      },
      {
        lead: 'Мафия.',
        body: 'Ког бота с лобби, ночными и дневными фазами; личные ссылки игроков на карточку роли, действия и голос.',
      },
      {
        lead: 'Бункер.',
        body: 'Карточки персонажей (профессия/здоровье/фобия/рюкзак), открытие характеристик, заявки на способности, редактор карточек.',
      },
      {
        lead: 'Ядро экономики.',
        body: 'Серверная валюта от активности, магазин ролей, переводы между участниками, ежедневные награды, еженедельные отчёты.',
      },
    ],
  },
  {
    date: '8–14 июля 2026 г.',
    title: 'Войс-комнаты, стримы, Fun и другие модули',
    bullets: [
      {
        lead: 'Модуль Fun.',
        body: 'Русская рулетка (барабан не перекручивается — шансы растут 1/6 → 1/1), эмодзи-рулетка, цитаты (PNG с аватаром, именем и текстом).',
      },
      {
        lead: 'Wordle.',
        body: 'Ежедневный русский Wordle с общим словом на сервер, личными досками, /wordle-stats, /wordle-top и ежедневным анонсом.',
      },
      {
        lead: 'Приватные войс-комнаты.',
        body: 'Войс-лобби → авто-создание комнаты; панель управления публикуется в канал Discord; статистика войса по часам, каналу и участнику.',
      },
      {
        lead: 'Казино.',
        body: 'Слоты, блэкджек и орёл-решка с интеграцией в серверную экономику и таблицами лидеров казино.',
      },
      {
        lead: 'Стрим-алерты.',
        body: 'Уведомления о новых видео YouTube, TikTok LIVE и видео, Twitch в эфире — отдельные embed и ping настройки на подписку.',
      },
      {
        lead: 'Семья (GTA5RP).',
        body: 'Ростер участников по ролям, заявки в семью через тикеты, календарь дней рождения с поздравлениями.',
      },
    ],
  },
  {
    date: '15–22 июля 2026 г.',
    title: 'Мультисерверность и модули сообщества',
    bullets: [
      {
        lead: 'Мультисерверность Phase 1.',
        body: 'Полная изоляция настроек по guild_id во всех модулях; бот загружает конфиг по guild_id при каждом событии.',
      },
      {
        lead: 'Мультисерверность Phase 2.',
        body: 'Переключатель гильдий в OAuth, per-guild синхронизация команд, привилегии CTD и новостей для главной гильдии сохранены.',
      },
      {
        lead: 'Модули сообщества.',
        body: 'Авто-реакции, плановые сообщения, sticky-сообщения, кастомные команды, звёздная доска, роли с таймером — всё per guild.',
      },
      {
        lead: 'Фундамент i18n.',
        body: 'Все строки панели дублируются на русском и английском; язык ответов бота задаётся per guild в настройках сервера.',
      },
      {
        lead: 'Исправлены баги мультисерверности.',
        body: 'Дополнительные модули сообщества добавлены; граничный кейс пустого барабана в рулетке устранён.',
      },
    ],
  },
  {
    date: '24–25 июля 2026 г.',
    title: 'Редизайн UI и страница авторов',
    bullets: [
      {
        lead: 'Редизайн панели.',
        body: 'Новый лейаут карточек, навигация в сайдбаре и цветовая система применены ко всем страницам панели.',
      },
      {
        lead: 'Страница авторов.',
        body: 'Состав команды, кредиты для открытых проектов и контактные ссылки Cheterin Group.',
      },
    ],
  },
  {
    date: '2–3 августа 2026 г.',
    title: 'ValChecker, /help и секция Games',
    bullets: [
      {
        lead: 'Модуль ValChecker.',
        body: 'Статистика Valorant, авто-публикация отслеженных матчей, команды /val, интеграция с Henrik API с защитой поллера.',
      },
      {
        lead: 'Команда /help.',
        body: 'Справка по модулям с учётом per-guild настроек; присутствие бота «Playing /help • Cheterin».',
      },
      {
        lead: 'Секция Games в панели.',
        body: 'Настройки ValChecker, интервал поллера, выбор каналов для матчей и алертов в новой вкладке Games.',
      },
      {
        lead: 'Рантайм-БД убраны из git.',
        body: 'SQLite-файлы с рантайм-данными исключены из трекинга, чтобы git pull не затирал живые данные.',
      },
    ],
  },
  {
    date: '12–17 августа 2026 г.',
    title: 'TikTok LIVE, динамические баннеры и Customs',
    bullets: [
      {
        lead: 'TikTok LIVE.',
        body: 'Задержка обнаружения ~2 мин; исправлены EU-страницы блокировки и устаревший envelope-статус; первый алерт сразу после подписки.',
      },
      {
        lead: 'Раздельные стили TikTok-embed.',
        body: 'Отдельные настройки embed, шаблона и пинга для LIVE-алертов и уведомлений о новых видео в рамках одной подписки.',
      },
      {
        lead: 'Динамический баннер сервера.',
        body: 'Авто-генерируемый баннер с самым активным участником войса, количеством участников и списком тех, кто в войсе.',
      },
      {
        lead: 'Ротация баннеров и иконок.',
        body: 'Загрузка плейлиста баннеров и иконок; бот ротирует их по настраиваемому расписанию из панели.',
      },
      {
        lead: 'Модуль Customs.',
        body: 'Кастомные лобби VALORANT: отображение рангов, голосование за карту, назначение войс-каналов, счёт и управление расписанием.',
      },
      {
        lead: 'Снятие ролей уровня.',
        body: 'Опция автоматически снимать предыдущую роль уровня при повышении, чтобы список ролей оставался чистым.',
      },
      {
        lead: 'VALORANT per guild.',
        body: 'Ростер Customs с никнеймами, контроль баннера, Premier-заявки и панели ролей — всё изолировано per guild.',
      },
    ],
  },
  {
    date: '19–22 августа 2026 г.',
    title: 'Relations, верификация Riot и Discord v2 Embeds',
    bullets: [
      {
        lead: 'Модуль Relations.',
        body: 'HP пар через действия (обнимашки, поцелуй, пощёчина, погладить и др.), система уровней до 11, браки с предложениями, команды /relations.',
      },
      {
        lead: 'Исправлена валидация Relations.',
        body: 'Правильные пороги уровней по умолчанию; PUT-валидация больше не сбрасывает поля молча.',
      },
      {
        lead: 'Верификация Riot.',
        body: 'Маршрут /riot.txt и второй DH-запись на /dh добавлены — требование для сертификации Valorant API.',
      },
      {
        lead: 'Discord Components v2.',
        body: 'Embed builder теперь поддерживает Components V2 (Container / Text Display) помимо классических эмбедов.',
      },
      {
        lead: 'Twitch UI 2.0.',
        body: 'Карточки подписок и редактор стрим-эмбедов переработаны для наглядности.',
      },
    ],
  },
  {
    date: '6 сентября 2026 г.',
    title: 'Запуск Cheterin Lookup',
    bullets: [
      {
        lead: 'Lookup SPA.',
        body: 'Отдельное React-приложение на /lookup — поиск пользователей, ботов и серверов Discord без входа в панель и без бота.',
      },
      {
        lead: 'Lookup API.',
        body: 'Изолированный Flask-процесс со своим Discord-токеном, защитой от rate-limit и CAPTCHA-гейтом для всплесков запросов.',
      },
      {
        lead: 'Plugins hub.',
        body: 'Единый каталог встроенных инструментов (декодер Snowflake, калькулятор прав, Аватары, Бейджи, Timestamps) и курируемых Vencord UserPlugins.',
      },
      {
        lead: 'Каталог бейджей.',
        body: 'Полный набор mezotv — публичные флаги, уровни Nitro, бусты сервера, специальные флеры, иконки guild tags, Hall of Fame.',
      },
      {
        lead: 'Режим DSA.',
        body: 'Интеграция с EU DSA Transparency Database (Discord Netherlands B.V.) — поиск публичных Statement of Reasons по Discord ID.',
      },
      {
        lead: 'Charcoal-red кит.',
        body: 'Lookup принял ту же тёмно-красную цветовую систему, бренд-марку, типографику и правовую рамку, что и основной сайт Cheterin.',
      },
      {
        lead: 'Dev Blog.',
        body: 'Эта страница — полная хронологическая история Cheterin с первого коммита по сегодня.',
      },
    ],
  },
  {
    date: '20–28 сентября 2026 г.',
    title: 'Lookup в проде: TokenPool, плагины и пайплайн docs',
    bullets: [
      {
        lead: 'TokenPool.',
        body: 'lookup-api крутит несколько Discord-токенов (LOOKUP_DISCORD_TOKENS) round-robin — по-прежнему отдельно от BOT_TOKEN и main.py.',
      },
      {
        lead: 'Plugins и Avatars.',
        body: 'Каталог плагинов под /lookup/plugins, поиск Avatars по ID, исправления пустого каталога.',
      },
      {
        lead: 'Инженерные docs.',
        body: 'ARCHITECTURE.md и Lookup RUN/PROXY синхронизированы с прод-раскладкой Oracle (chetmain / chetlookup).',
      },
      {
        lead: 'Пайплайн поставки.',
        body: 'Правило Cursor: каждое продуктовое изменение → техдоки + Dev Blog + commit/push + update.sh + smoke продакшена.',
      },
    ],
  },
  {
    date: '29 сентября 2026 г.',
    title: 'Пакет bot/, обновление legal и cookie-согласие',
    bullets: [
      {
        lead: 'Дерево bot/ как у VALORANT.',
        body: 'Модули бота в bot/ (core, modules по доменам, cards, data). Точка входа — main.py; dashboard и Lookup на прежних путях; Lookup изолирован.',
      },
      {
        lead: 'Папка docs/.',
        body: 'ARCHITECTURE только в docs/; deploy/ — заметки по nginx/процессам. Закрытые product-планы удаляются после ship.',
      },
      {
        lead: 'Шапка панели.',
        body: 'В верхней полосе залогиненной панели остаются Документация и Условия; Приватность, Cookies и Отказ — в поднавигации legal-страниц и футере.',
      },
      {
        lead: 'Legal-subnav.',
        body: 'Общие вкладки charcoal-red: Условия ↔ Приватность ↔ Cookies ↔ Отказ.',
      },
      {
        lead: 'Плашка cookies.',
        body: 'Нижний баннер (RU/EN) с «Принять» и ссылкой на политику; ключ chetbot_cookie_consent в localStorage; не блокирует приложение навсегда.',
      },
      {
        lead: 'Обновление legal-текстов.',
        body: 'Условия, Приватность, Cookies и Отказ актуализированы под бот + панель + Lookup, OAuth-сессию, TokenPool, контакты (discord.gg/cheterin, turkapahf@gmail.com); дата — 29 сентября 2026.',
      },
      {
        lead: 'Гигиена секретов.',
        body: '.env.example очищен до пустых placeholders — без реальных токенов в шаблоне.',
      },
    ],
  },
  {
    date: '29 сентября 2026 г.',
    title: 'Публичная подготовка: Apache-2.0, CI, docs i18n и systemd',
    bullets: [
      {
        lead: 'Apache License 2.0.',
        body: 'Корневой LICENSE с Copyright 2026 Cheterin Group — репозиторий готов к публичной раздаче под Apache-2.0.',
      },
      {
        lead: 'GitHub Actions CI.',
        body: 'На push/PR в main: pytest панели и lookup-api, production-сборки dashboard + Lookup SPA — без Discord-секретов в CI.',
      },
      {
        lead: 'Docs i18n.',
        body: 'README.md по умолчанию на английском + README.ru.md; архитектурные карты EN + RU только в docs/ (без корневых stub).',
      },
      {
        lead: 'Контактный email.',
        body: 'Публичный контакт сведён к turkapahf@gmail.com (футер, credits, legal).',
      },
      {
        lead: 'Полный update.sh + systemd.',
        body: 'update.sh собирает dashboard и Lookup, ставит deps lookup-api и рестартит unit cheterin-bot + cheterin-lookup (deploy/systemd/). В docs вместо tmux chetmain/chetlookup; unit на VPS ставит оператор.',
      },
      {
        lead: 'Локальные Cursor rules.',
        body: '.cursor/rules/ в gitignore и снят с трекинга — SSH/ops-детали только на машине оператора.',
      },
    ],
  },
]

/* ------------------------------------------------------------------ */
/* Page                                                                 */
/* ------------------------------------------------------------------ */
export function DevBlogPage() {
  const { lang } = useLanguage()
  const entries = lang === 'ru' ? BLOG_RU : BLOG_EN
  const isRu = lang === 'ru'

  return (
    <PublicLayout>
      <div className="mx-auto w-full max-w-3xl px-4 py-16 sm:px-6">
        {/* ── Header ── */}
        <div className="mb-14">
          <p className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-primary/80">
            {isRu ? 'Cheterin · Dev Blog' : 'Cheterin · Dev Blog'}
          </p>
          <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
            {isRu ? 'История разработки' : 'Development History'}
          </h1>
          <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted">
            {isRu
              ? 'Полная хронология Cheterin — от первого коммита до сегодня. Записи охватывают ключевые этапы: запуск панели, модули бота, мультисерверность, ValChecker, Lookup, legal/cookies и многое другое.'
              : 'Full Cheterin timeline from first commit to today — dashboard launch, bot modules, multi-guild isolation, ValChecker, Lookup, legal/cookies, and more.'}
          </p>
        </div>

        {/* ── Timeline ── */}
        <div className="relative">
          {/* Vertical rail */}
          <div className="absolute left-0 top-2 bottom-0 w-px bg-border/50" aria-hidden />

          <div className="flex flex-col gap-0">
            {entries.map((entry, idx) => (
              <div key={idx} className="relative pl-7 pb-12 last:pb-0">
                {/* Red dot */}
                <div className="absolute -left-[4px] top-[6px] h-2.5 w-2.5 rounded-full border-2 border-primary bg-background" />

                {/* Date cap */}
                <p className="text-[0.63rem] font-semibold uppercase tracking-[0.2em] text-muted/70">
                  {entry.date}
                </p>

                {/* Section title */}
                <h2 className="mt-1 text-base font-semibold leading-snug text-foreground">
                  {entry.title}
                </h2>

                {/* Bullet list */}
                <ul className="mt-3 space-y-2">
                  {entry.bullets.map((b, bi) => (
                    <li key={bi} className="flex items-baseline gap-2 text-sm text-muted">
                      <span className="mt-px shrink-0 text-primary/70" aria-hidden>
                        •
                      </span>
                      <span>
                        <strong className="font-medium text-foreground/85">{b.lead}</strong>{' '}
                        {b.body}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </div>
    </PublicLayout>
  )
}
