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
        body: 'Config validation, Discord OAuth2 (login / callback / logout / /me), Fernet session key derivation, and graceful startup.',
      },
      {
        lead: 'Guild access control.',
        body: 'has_dashboard_access with full test coverage; require_dashboard_access decorator shared across protected API routes.',
      },
      {
        lead: 'Members API.',
        body: 'Search and pagination, member detail cards, ban and kick with Discord error mapping.',
      },
      {
        lead: 'Vite + React + TypeScript frontend.',
        body: 'Tailwind v4, typed fetch, vitest, AuthContext, ProtectedRoute, and the first dashboard shell.',
      },
      {
        lead: 'Design system.',
        body: 'Charcoal-dark layout applied across login, access-denied, and shell pages on day one.',
      },
    ],
  },
  {
    date: 'July 2–3, 2026',
    title: 'Moderation, Roles & Embed Builder',
    bullets: [
      {
        lead: 'Lockdown module.',
        body: 'Antispam core extracted; activate/deactivate API routes with partial-failure audit logs.',
      },
      {
        lead: 'Mass role assignment.',
        body: 'Background job orchestration, TOCTOU-safe guard, 1000-member cap, modal in Members page.',
      },
      {
        lead: 'Reaction Roles.',
        body: 'Full CRUD with Discord channel/message validation; unicode and server custom emoji.',
      },
      {
        lead: 'Embed builder.',
        body: 'Build/parse/validate, 6000-char budget, live preview, role buttons (up to 5), send and edit modes.',
      },
      {
        lead: 'Feedback module.',
        body: 'Cases, approve/deny decisions, custom form-field categories, publish panel to Discord.',
      },
    ],
  },
  {
    date: 'July 4–7, 2026',
    title: 'Events, Brackets & Early Games',
    bullets: [
      {
        lead: 'Events and polls.',
        body: 'Join-button events, polls, giveaways with auto winner pick and reroll.',
      },
      {
        lead: 'Tournament brackets.',
        body: 'Single/double elimination, round robin; public share link for spectators.',
      },
      {
        lead: 'Mafia game.',
        body: 'Bot cog with lobby, night/day phases; personal player dashboard links.',
      },
      {
        lead: 'Bunker game.',
        body: 'Character cards, trait reveals, ability requests, card editor in the panel.',
      },
      {
        lead: 'Economy core.',
        body: 'Server currency, role shop, transfers, daily rewards, weekly reports.',
      },
    ],
  },
  {
    date: 'July 8–14, 2026',
    title: 'Voice Rooms, Streams, Fun & More Modules',
    bullets: [
      {
        lead: 'Fun module.',
        body: 'Russian roulette (odds rise 1/6 → 1/1), emoji roulette, quote PNG generator.',
      },
      {
        lead: 'Wordle.',
        body: 'Daily Russian Wordle, shared board, /wordle-stats, /wordle-top, daily announcement.',
      },
      {
        lead: 'Private voice rooms.',
        body: 'Join-lobby → auto-created room; control panel in Discord channel; voice stats.',
      },
      {
        lead: 'Casino.',
        body: 'Slots, blackjack, coinflip with economy integration and leaderboards.',
      },
      {
        lead: 'Stream alerts.',
        body: 'YouTube, TikTok LIVE + video, and Twitch live alerts with per-subscription embed settings.',
      },
      {
        lead: 'Family (GTA5RP).',
        body: 'Roster by roles, join tickets, birthday calendar.',
      },
    ],
  },
  {
    date: 'July 15–22, 2026',
    title: 'Multi-Guild Isolation & Community Modules',
    bullets: [
      {
        lead: 'Multi-guild Phase 1.',
        body: 'Per-guild settings isolation across every module; bot loads config by guild_id on each event.',
      },
      {
        lead: 'Multi-guild Phase 2.',
        body: 'OAuth guild switcher, per-guild command sync, CTD/news main-guild privileges preserved.',
      },
      {
        lead: 'Community modules.',
        body: 'Auto-reactions, scheduled messages, sticky messages, custom commands, starboard, timed roles.',
      },
      {
        lead: 'i18n foundation.',
        body: 'All strings dual-tracked in Russian and English; bot reply language per guild.',
      },
    ],
  },
  {
    date: 'July 24–25, 2026',
    title: 'UI Refresh & Credits',
    bullets: [
      {
        lead: 'Dashboard redesign.',
        body: 'New layout, sidebar navigation, and color system across every panel page.',
      },
      {
        lead: 'Credits page.',
        body: 'Team roster, project credits, and contact links for Cheterin Group.',
      },
    ],
  },
  {
    date: 'August 2–3, 2026',
    title: 'ValChecker, /help & Games Dashboard',
    bullets: [
      {
        lead: 'ValChecker module.',
        body: 'Valorant stats, tracked match auto-posting, /val commands, hardened Henrik API poller.',
      },
      {
        lead: '/help command.',
        body: 'Per-guild module-aware help; presence set to "Playing /help • Cheterin".',
      },
      {
        lead: 'Games dashboard section.',
        body: 'ValChecker settings, poller interval, match and alert channels in a new Games tab.',
      },
    ],
  },
  {
    date: 'August 12–17, 2026',
    title: 'TikTok Streams, Dynamic Banners & Customs',
    bullets: [
      {
        lead: 'TikTok LIVE.',
        body: '~2 min detection; fixed EU block pages, stale envelope, first alert fires on subscribe.',
      },
      {
        lead: 'Separate TikTok embed styles.',
        body: 'Independent embed/ping settings for LIVE alerts vs new video alerts per subscription.',
      },
      {
        lead: 'Dynamic server banner.',
        body: 'Top active voice member, member count, and who is in voice — auto-generated.',
      },
      {
        lead: 'Scheduled banner/icon rotation.',
        body: 'Upload playlist; bot rotates on a configurable schedule from the dashboard.',
      },
      {
        lead: 'Customs module.',
        body: 'VALORANT custom lobbies: ranks, map votes, voice, scores, schedules.',
      },
      {
        lead: 'Level-role replace.',
        body: 'Remove previous level role on level-up to keep the member role list clean.',
      },
      {
        lead: 'Guild-scoped VALORANT.',
        body: 'Customs roster, banner controls, Premier apps, role panels — all per-guild.',
      },
    ],
  },
  {
    date: 'August 19–22, 2026',
    title: 'Relations, Riot Verification & Discord v2 Embeds',
    bullets: [
      {
        lead: 'Relations module.',
        body: 'Pair HP from actions (hug, kiss, slap, pat…), romance level system to 11, marriages, /relations commands.',
      },
      {
        lead: 'Riot domain verification.',
        body: '/riot.txt and second DH record at /dh — required for Valorant API certification.',
      },
      {
        lead: 'Discord Components v2.',
        body: 'Embed builder supports Components V2 (Container / Text Display) alongside classic embeds.',
      },
      {
        lead: 'Twitch UI 2.0.',
        body: 'Subscription cards and stream embed editor redesigned.',
      },
    ],
  },
  {
    date: 'September 6, 2026',
    title: 'Cheterin Lookup Launch',
    bullets: [
      {
        lead: 'Lookup SPA.',
        body: 'Standalone React app at /lookup — Discord user, bot, and server lookup, no panel login required.',
      },
      {
        lead: 'Lookup API.',
        body: 'Isolated Flask process, its own Discord token, rate-limit protection, CAPTCHA gating for burst traffic.',
      },
      {
        lead: 'Plugins hub.',
        body: 'Catalog for built-in tools (Snowflake, Permissions, Avatars, Badges, Timestamps) and Vencord UserPlugins.',
      },
      {
        lead: 'Badge catalog.',
        body: 'Complete mezotv set — public flags, Nitro, boosts, flairs, guild tag icons, Hall of Fame.',
      },
      {
        lead: 'DSA mode.',
        body: 'EU DSA Transparency Database (Discord Netherlands B.V.) — look up public Statements of Reasons by Discord ID.',
      },
      {
        lead: 'Charcoal-red kit.',
        body: 'Same dark-red color system, brand mark, and legal frame as the main Cheterin site.',
      },
      {
        lead: 'Dev Blog.',
        body: 'This page — full project history from first commit to launch.',
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
        body: 'Первый снимок бота Cheterin — рабочий код входит в систему версий как нулевая фаза.',
      },
      {
        lead: 'Бэкенд с нуля.',
        body: 'Валидация конфига, Discord OAuth2, сессионный ключ Fernet, graceful startup.',
      },
      {
        lead: 'Контроль доступа.',
        body: 'has_dashboard_access с полным покрытием тестами; декоратор require_dashboard_access.',
      },
      {
        lead: 'Members API.',
        body: 'Поиск и пагинация, карточки участников, бан и кик с обработкой ошибок Discord.',
      },
      {
        lead: 'Vite + React + TypeScript.',
        body: 'Tailwind v4, типизированный fetch, vitest, AuthContext, ProtectedRoute, шелл панели.',
      },
      {
        lead: 'Дизайн-система.',
        body: 'Угольный dark-лейаут на страницах входа и оболочке панели с первого дня.',
      },
    ],
  },
  {
    date: '2–3 июля 2026 г.',
    title: 'Модерация, роли и embed-редактор',
    bullets: [
      {
        lead: 'Модуль Lockdown.',
        body: 'Ядро антиспама вынесено; API activate/deactivate с журналом частичных сбоев.',
      },
      {
        lead: 'Массовое назначение ролей.',
        body: 'Фоновые задачи, TOCTOU-блокировка, кап 1000 участников, модальное окно.',
      },
      {
        lead: 'Reaction Roles.',
        body: 'CRUD, валидация канала/сообщения Discord, unicode и кастомные эмодзи.',
      },
      {
        lead: 'Embed builder.',
        body: 'Сборка/парсинг/валидация, лимит 6000 символов, live-превью, кнопки ролей до 5.',
      },
      {
        lead: 'Модуль Feedback.',
        body: 'Кейсы, решения одобрить/отклонить, кастомные формы, публикация в Discord.',
      },
    ],
  },
  {
    date: '4–7 июля 2026 г.',
    title: 'События, сетки и первые игры',
    bullets: [
      {
        lead: 'События и опросы.',
        body: 'События с кнопками, опросы, раздачи с авто-выбором победителей и реролом.',
      },
      {
        lead: 'Турнирные сетки.',
        body: 'Одиночное/двойное выбывание, круговой турнир, публичная ссылка.',
      },
      {
        lead: 'Мафия.',
        body: 'Kog бота, ночные/дневные фазы, личные ссылки игроков.',
      },
      {
        lead: 'Бункер.',
        body: 'Карточки персонажей, открытие характеристик, заявки на способности, редактор.',
      },
      {
        lead: 'Ядро экономики.',
        body: 'Серверная валюта, магазин ролей, переводы, ежедневные награды.',
      },
    ],
  },
  {
    date: '8–14 июля 2026 г.',
    title: 'Войс-комнаты, стримы, Fun и другие модули',
    bullets: [
      {
        lead: 'Модуль Fun.',
        body: 'Русская рулетка (шансы растут 1/6 → 1/1), эмодзи-рулетка, цитаты PNG.',
      },
      {
        lead: 'Wordle.',
        body: 'Ежедневный русский Wordle, общее слово, /wordle-stats, /wordle-top, анонс.',
      },
      {
        lead: 'Приватные войс-комнаты.',
        body: 'Лобби → авто-комната, панель управления в Discord, статистика войса.',
      },
      {
        lead: 'Казино.',
        body: 'Слоты, блэкджек, орёл-решка с экономикой и таблицами лидеров.',
      },
      {
        lead: 'Стрим-алерты.',
        body: 'YouTube, TikTok LIVE + видео, Twitch — embed и ping на подписку.',
      },
      {
        lead: 'Семья (GTA5RP).',
        body: 'Ростер по ролям, заявки-тикеты, календарь дней рождения.',
      },
    ],
  },
  {
    date: '15–22 июля 2026 г.',
    title: 'Мультисерверность и модули сообщества',
    bullets: [
      {
        lead: 'Мультисерверность Phase 1.',
        body: 'Изоляция настроек по guild_id во всех модулях.',
      },
      {
        lead: 'Мультисерверность Phase 2.',
        body: 'Переключатель гильдий в OAuth, per-guild синхронизация команд.',
      },
      {
        lead: 'Модули сообщества.',
        body: 'Авто-реакции, плановые и sticky-сообщения, кастомные команды, звёздная доска, роли с таймером.',
      },
      {
        lead: 'Фундамент i18n.',
        body: 'Все строки на русском и английском; язык ответов бота per guild.',
      },
    ],
  },
  {
    date: '24–25 июля 2026 г.',
    title: 'Редизайн UI и страница авторов',
    bullets: [
      {
        lead: 'Редизайн панели.',
        body: 'Новый лейаут, навигация и цветовая система на всех страницах.',
      },
      {
        lead: 'Страница авторов.',
        body: 'Команда, кредиты проектов, контакты Cheterin Group.',
      },
    ],
  },
  {
    date: '2–3 августа 2026 г.',
    title: 'ValChecker, /help и секция Games',
    bullets: [
      {
        lead: 'Модуль ValChecker.',
        body: 'Статистика Valorant, трекинг матчей, /val команды, Henrik API поллер.',
      },
      {
        lead: 'Команда /help.',
        body: 'Справка по модулям per guild; присутствие «Playing /help • Cheterin».',
      },
      {
        lead: 'Секция Games в панели.',
        body: 'Настройки ValChecker, интервал поллера, каналы матчей и алертов.',
      },
    ],
  },
  {
    date: '12–17 августа 2026 г.',
    title: 'TikTok LIVE, динамические баннеры и Customs',
    bullets: [
      {
        lead: 'TikTok LIVE.',
        body: 'Задержка ~2 мин, исправлены EU-блокировки и envelope-статус, первый алерт сразу после подписки.',
      },
      {
        lead: 'Раздельные стили TikTok.',
        body: 'Отдельные embed/ping для LIVE и видео в рамках одной подписки.',
      },
      {
        lead: 'Динамический баннер.',
        body: 'Самый активный в войсе, количество участников, список в войсе.',
      },
      {
        lead: 'Ротация баннеров/иконок.',
        body: 'Плейлист и расписание ротации из панели.',
      },
      {
        lead: 'Customs.',
        body: 'VALORANT-лобби: ранги, карты, войс, счёт, расписание.',
      },
      {
        lead: 'Снятие роли уровня.',
        body: 'Опция убирать предыдущую роль при level-up.',
      },
      {
        lead: 'VALORANT per guild.',
        body: 'Customs-ростер, баннер, Premier, панели ролей — всё по guild.',
      },
    ],
  },
  {
    date: '19–22 августа 2026 г.',
    title: 'Relations, верификация Riot и Discord v2 Embeds',
    bullets: [
      {
        lead: 'Модуль Relations.',
        body: 'HP пар, романтика, браки, /relations команды, действия hug/kiss/slap/pat и др.',
      },
      {
        lead: 'Верификация Riot.',
        body: '/riot.txt и DH-запись — требование Valorant API.',
      },
      {
        lead: 'Discord Components v2.',
        body: 'Embed builder поддерживает Components V2 (Container / Text Display).',
      },
      {
        lead: 'Twitch UI 2.0.',
        body: 'Карточки подписок и редактор эмбедов переработаны.',
      },
    ],
  },
  {
    date: '6 сентября 2026 г.',
    title: 'Запуск Cheterin Lookup',
    bullets: [
      {
        lead: 'Lookup SPA.',
        body: 'Отдельное React-приложение на /lookup — поиск без входа в панель.',
      },
      {
        lead: 'Lookup API.',
        body: 'Изолированный Flask, свой Discord-токен, защита от rate-limit, CAPTCHA.',
      },
      {
        lead: 'Plugins hub.',
        body: 'Каталог инструментов Lookup и Vencord UserPlugins.',
      },
      {
        lead: 'Каталог бейджей.',
        body: 'Полный набор mezotv — флаги, Nitro, бусты, флеры, guild tags.',
      },
      {
        lead: 'Режим DSA.',
        body: 'EU DSA Transparency Database — Statement of Reasons по Discord ID.',
      },
      {
        lead: 'Charcoal-red кит.',
        body: 'Та же цветовая система и правовая рамка, что у основного сайта Cheterin.',
      },
      {
        lead: 'Dev Blog.',
        body: 'Эта страница — полная история с первого коммита.',
      },
    ],
  },
]

/* ------------------------------------------------------------------ */
/* Page component (LookupLayout is already applied in App.tsx)         */
/* ------------------------------------------------------------------ */
export function DevBlogPage() {
  const { lang } = useLanguage()
  const entries = lang === 'ru' ? BLOG_RU : BLOG_EN
  const isRu = lang === 'ru'

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-16 sm:px-6">
      {/* ── Header ── */}
      <div className="mb-14">
        <p className="text-[0.65rem] font-semibold uppercase tracking-[0.2em] text-primary/80">
          Cheterin · Dev Blog
        </p>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-foreground">
          {isRu ? 'История разработки' : 'Development History'}
        </h1>
        <p className="mt-3 max-w-lg text-sm leading-relaxed text-muted">
          {isRu
            ? 'Полная хронология Cheterin — от первого коммита до сегодня. Записи охватывают запуск панели, модули бота, мультисерверность, ValChecker, Lookup и многое другое.'
            : 'Full Cheterin timeline from first commit to today — dashboard launch, bot modules, multi-guild, ValChecker, Lookup, and more.'}
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
  )
}
