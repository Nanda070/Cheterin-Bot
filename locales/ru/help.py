MESSAGES: dict[str, str] = {
    "help.select_placeholder": "Выберите раздел…",
    "help.footer": "{category} · Стр. {page}/{max_pages} · Справка Cheterin",
    # Category select
    "help.cat.overview.emoji": "📌",
    "help.cat.overview.label": "Обзор",
    "help.cat.overview.desc": "Как бот работает для участников",
    "help.cat.levels.emoji": "🏆",
    "help.cat.levels.label": "Уровни",
    "help.cat.levels.desc": "XP, ранг, профиль, топ",
    "help.cat.economy.emoji": "🪙",
    "help.cat.economy.label": "Экономика",
    "help.cat.economy.desc": "Монеты, магазин, переводы",
    "help.cat.casino.emoji": "🎰",
    "help.cat.casino.label": "Казино",
    "help.cat.casino.desc": "Игры на монеты",
    "help.cat.fun.emoji": "🎮",
    "help.cat.fun.label": "Игры и Fun",
    "help.cat.fun.desc": "Вордл, рулетка, Мафия, Бункер",
    "help.cat.community.emoji": "🏠",
    "help.cat.community.label": "Сообщество",
    "help.cat.community.desc": "ДР, комнаты, семья, опросы",
    "help.cat.valchecker.emoji": "🎯",
    "help.cat.valchecker.label": "ValChecker",
    "help.cat.valchecker.desc": "Статистика Valorant",
    "help.cat.events.emoji": "🎉",
    "help.cat.events.label": "События",
    "help.cat.events.desc": "Розыгрыши, ивенты, feedback",
    # Pages
    "help.page.overview.title": "Cheterin — Справка",
    "help.page.overview.body": (
        "Гид для участников этого сервера. Разделы — в **меню** или стрелками **« ‹ › »**.\n\n"
        "Многие модули админы могут выключить: если команда пишет, что модуль отключён — "
        "здесь он недоступен.\n\n"
        "**Подсказка:** в статусе бота `Playing /help • Cheterin` — всегда можно открыть это меню."
    ),
    "help.page.overview.field1.name": "С чего начать",
    "help.page.overview.field1.value": (
        "• Пишите в чат и сидите в войсе → **XP** и иногда **монеты**\n"
        "• `/daily` → ежедневный бонус монет\n"
        "• `/ранг` / `/профиль` → ваши карточки\n"
        "• `/leaders` → топ по XP и голосу\n"
        "• `/help` → это меню (видно только вам)"
    ),
    "help.page.overview.field2.name": "Разделы",
    "help.page.overview.field2.value": (
        "🏆 Уровни · 🪙 Экономика · 🎰 Казино · 🎮 Игры и Fun\n"
        "🏠 Сообщество · 🎯 ValChecker · 🎉 События"
    ),
    "help.page.levels.title": "🏆 Уровни и профиль",
    "help.page.levels.body": (
        "XP за сообщения и время в голосовых. "
        "За уровни могут выдаваться роли, если админы настроили награды."
    ),
    "help.page.levels.field1.name": "Команды",
    "help.page.levels.field1.value": (
        "`/ранг` (`/rank`) — карточка ранга: уровень, XP, голос\n"
        "`/профиль` (`/profile`) — анимированный профиль (рамки и титулы из магазина)\n"
        "`/leaders` — интерактивный топ по **опыту** или **голосу** (те же « ‹ › »)"
    ),
    "help.page.levels.field2.name": "Как копится XP",
    "help.page.levels.field2.value": (
        "• Текстовый XP с кулдауном (не за каждое сообщение)\n"
        "• Голосовой XP, пока вы в войсе (правила AFK — от настроек сервера)\n"
        "• Часть каналов/ролей модуль может игнорировать"
    ),
    "help.page.economy.title": "🪙 Экономика",
    "help.page.economy.body": (
        "Серверные монеты: активность, daily, переводы и магазин ролей. "
        "Нужен включённый модуль «Экономика»."
    ),
    "help.page.economy.field1.name": "Команды",
    "help.page.economy.field1.value": (
        "`/daily` — ежедневный бонус; серия дней подряд увеличивает выплату\n"
        "`/баланс` (`/balance`) — свой баланс или чужой\n"
        "`/перевести` (`/transfer`) — перевод (комиссия/лимиты задают админы)\n"
        "`/магазин` (`/shop`) — роли за монеты\n"
        "`/косметика` (`/cosmetics`) — рамка и титул карточки ранга\n"
        "`/монеты-топ` (`/coins-top`) — топ по монетам"
    ),
    "help.page.economy.field2.name": "Важно",
    "help.page.economy.field2.value": (
        "• Монеты могут капать и за XP, если так настроено\n"
        "• Магазин вернёт монеты, если Discord не выдал роль\n"
        "• Staff-команды выдачи баланса здесь не перечислены"
    ),
    "help.page.casino.title": "🎰 Казино",
    "help.page.casino.body": (
        "Игры на монеты. Нужны **Экономика** и **Казино**. "
        "Играйте осознанно — баланс можно обнулить."
    ),
    "help.page.casino.field1.name": "Команды",
    "help.page.casino.field1.value": (
        "`/блэкджек` (`/blackjack`) — против дилера на ставку\n"
        "`/слоты` (`/slots`) — три барабана, совпадения дают выигрыш\n"
        "`/монетка` (`/coinflip`) — угадай сторону, ставка удваивается\n"
        "`/казино-топ` (`/casino-top`) — топ по победам и проигрышам"
    ),
    "help.page.casino.field2.name": "Ставки в русской рулетке",
    "help.page.casino.field2.value": (
        "`/русская-рулетка` может принимать ставку монет (если казино включено): "
        "выжил — умножил, проиграл — потерял ставку (и получил таймаут)."
    ),
    "help.page.fun.title": "🎮 Игры и развлечения",
    "help.page.fun.body": (
        "Мини-игры и лобби. Зависит от модулей Fun / Мафия / Бункер."
    ),
    "help.page.fun.field1.name": "Вордл и рулетка",
    "help.page.fun.field1.value": (
        "`/вордл` (`/wordle`) — `play` день · `training` · `stats` · `top`\n"
        "Доска дня видна только вам; в канал уходит цветная карточка без букв.\n\n"
        "`/русская-рулетка` — шанс растёт с каждым щелчком (1/6 → 1/1); "
        "есть шанс пустого барабана; проигравший получает таймаут. Опциональная ставка."
    ),
    "help.page.fun.field2.name": "Мафия и Бункер",
    "help.page.fun.field2.value": (
        "`/мафия-игра` (`/mafia-start`) — лобби «Мафия» (кнопки / личная ссылка)\n"
        "`/бункер-игра` (`/bunker-start`) — лобби «Бункер»\n"
        "Игра идёт на вашей веб-ссылке. Хост может управлять матчем из панели."
    ),
    "help.page.fun.field3.name": "Цитаты",
    "help.page.fun.field3.value": (
        "**Make it a Quote:** ответьте на сообщение и упомяните бота → PNG-цитата "
        "(если Fun / Quote включён)."
    ),
    "help.page.community.title": "🏠 Сообщество",
    "help.page.community.body": (
        "Повседневные инструменты: дни рождения, приватные комнаты, семья, поставки, опросы."
    ),
    "help.page.community.field1.name": "Дни рождения и опросы",
    "help.page.community.field1.value": (
        "`/set-birthday` — ваш ДР в формате `ММ-ДД` (объявления календаря сервера)\n"
        "`/poll` — быстрый опрос до 5 вариантов"
    ),
    "help.page.community.field2.name": "Приватные голосовые",
    "help.page.community.field2.value": (
        "Зайдите в голосовое лобби → бот создаст **вашу** комнату и перенесёт вас.\n"
        "Панель управления: открыть/закрыть, имя, лимит, кик, передача владения.\n"
        "Пустые комнаты удаляются сами."
    ),
    "help.page.community.field3.name": "Семья и поставки (Игры)",
    "help.page.community.field3.value": (
        "`/список` (`/roster`) — live-список семьи по ролям\n"
        "`/др` (`/birthday`) — дни рождения семьи (`add` / `set` / `remove`)\n"
        "`/реаки-поставка` (`/supply-run`) — staff создаёт сбор; запись кнопками\n"
        "`/семья-заявки` — заявка в семью, когда вывешена панель"
    ),
    "help.page.valchecker.title": "🎯 ValChecker — Valorant",
    "help.page.valchecker.body": (
        "Привязка Riot ID и статистика. Модуль должен быть **включён**: Игры → ValChecker. "
        "На хосте бота нужен ключ Henrik API."
    ),
    "help.page.valchecker.field1.name": "Аккаунт",
    "help.page.valchecker.field1.value": (
        "`/val-setup` — привязка / перепривязка Riot `Name#TAG`, **трекинг матчей** или отвязка\n"
        "Трекинг публикует новые матчи в канал матчей сервера."
    ),
    "help.page.valchecker.field2.name": "Статы и матчи",
    "help.page.valchecker.field2.value": (
        "`/val-profile` — обзор · статы · агенты · карты (переключение кнопками)\n"
        "`/val-match` — последний матч или история (`+5` подгружает ещё)\n"
        "`/val-compare` — сравнение двух игроков (линк или Riot ID)\n"
        "`/val-lb` — топ сервера по рангу / WR / ACS\n"
        "`/val-status` — инциденты, очереди или оба (выберите регион)"
    ),
    "help.page.valchecker.field3.name": "Советы",
    "help.page.valchecker.field3.value": (
        "• Чужих можно смотреть опциями `user:` или `riot_id:`\n"
        "• Отвязка в любой момент через `/val-setup`\n"
        "• При лимите API подождите минуту и повторите"
    ),
    "help.page.events.title": "🎉 События и обратная связь",
    "help.page.events.body": (
        "Розыгрыши, ивенты и сетки обычно постит staff панелями — "
        "вы жмёте **кнопки и реакции**, а не slash-команды."
    ),
    "help.page.events.field1.name": "Розыгрыши и ивенты",
    "help.page.events.field1.value": (
        "• Реакция / кнопка Join на эмбеде розыгрыша — участие\n"
        "• События и турниры — запись кнопками на посте\n"
        "• Сетки могут иметь публичную ссылку на турнирное дерево"
    ),
    "help.page.events.field2.name": "Feedback и тикеты",
    "help.page.events.field2.value": (
        "• **Панель обратной связи** в настроенном канале — идеи и жалобы\n"
        "• Тикеты поддержки (если включены) открывают приватную ветку со staff"
    ),
    "help.page.events.field3.name": "Ещё",
    "help.page.events.field3.value": (
        "Админы настраивают всё в веб-панели. "
        "Документация: cheterin.online/docs"
    ),
}
