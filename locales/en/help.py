MESSAGES: dict[str, str] = {
    "help.select_placeholder": "Choose a section…",
    "help.footer": "{category} · Page {page}/{max_pages} · Cheterin Help",
    # Category select
    "help.cat.overview.emoji": "📌",
    "help.cat.overview.label": "Overview",
    "help.cat.overview.desc": "How the bot works for members",
    "help.cat.levels.emoji": "🏆",
    "help.cat.levels.label": "Levels",
    "help.cat.levels.desc": "XP, rank, profile, leaders",
    "help.cat.economy.emoji": "🪙",
    "help.cat.economy.label": "Economy",
    "help.cat.economy.desc": "Coins, shop, transfers",
    "help.cat.casino.emoji": "🎰",
    "help.cat.casino.label": "Casino",
    "help.cat.casino.desc": "Games for coins",
    "help.cat.fun.emoji": "🎮",
    "help.cat.fun.label": "Games & fun",
    "help.cat.fun.desc": "Wordle, roulette, Mafia, Bunker",
    "help.cat.community.emoji": "🏠",
    "help.cat.community.label": "Community",
    "help.cat.community.desc": "Birthdays, rooms, family, polls",
    "help.cat.relations.emoji": "💕",
    "help.cat.relations.label": "Relations",
    "help.cat.relations.desc": "Actions, HP, marriage and divorce",
    "help.cat.valchecker.emoji": "🎯",
    "help.cat.valchecker.label": "ValChecker",
    "help.cat.valchecker.desc": "Valorant stats & tracking",
    "help.cat.events.emoji": "🎉",
    "help.cat.events.label": "Events",
    "help.cat.events.desc": "Giveaways, events, feedback",
    # Pages
    "help.page.overview.title": "Cheterin — Help",
    "help.page.overview.body": (
        "Member guide for this server. Use the **menu** or **« ‹ › »** to switch sections.\n\n"
        "Most features can be turned off by admins — if a command says the module is disabled, "
        "it isn’t available here.\n\n"
        "**Tip:** bot status shows `Playing /help • Cheterin` so you can always find this menu."
    ),
    "help.page.overview.field1.name": "Quick start",
    "help.page.overview.field1.value": (
        "• Chat & sit in voice → earn **XP** and sometimes **coins**\n"
        "• `/daily` → daily coin bonus\n"
        "• `/levels rank` / `profile` → your cards\n"
        "• `/levels leaders` → server XP & voice top\n"
        "• `/help` → this menu (ephemeral, only you see it)"
    ),
    "help.page.overview.field2.name": "Sections",
    "help.page.overview.field2.value": (
        "🏆 Levels · 🪙 Economy · 🎰 Casino · 🎮 Games & fun\n"
        "🏠 Community · 💕 Relations · 🎯 ValChecker · 🎉 Events"
    ),
    "help.page.levels.title": "🏆 Levels & profile",
    "help.page.levels.body": (
        "Earn XP by sending messages and spending time in voice. "
        "Level-ups may grant roles when admins configured rewards."
    ),
    "help.page.levels.field1.name": "Commands",
    "help.page.levels.field1.value": (
        "Group `/levels` (`/уровни`):\n"
        "• `rank` — rank card: level, XP, voice time\n"
        "• `profile` — animated profile card (frames & titles from the shop)\n"
        "• `leaders` — interactive top by **XP** or **voice** (same « ‹ › » controls)\n"
        "• `manage` — staff: add / set / clear XP (Manage Server required)"
    ),
    "help.page.levels.field2.name": "How XP works",
    "help.page.levels.field2.value": (
        "• Text XP on a short cooldown (not every message)\n"
        "• Voice XP while connected (idle rules depend on server settings)\n"
        "• Some channels/roles may be ignored by the module"
    ),
    "help.page.economy.title": "🪙 Economy",
    "help.page.economy.body": (
        "Server coins for activity, daily claims, transfers, and the role shop. "
        "Requires the Economy module."
    ),
    "help.page.economy.field1.name": "Commands",
    "help.page.economy.field1.value": (
        "`/daily` — daily bonus; streak days in a row increase the payout\n"
        "`/balance` (`/баланс`) — your balance or someone else’s\n"
        "`/transfer` (`/перевести`) — send coins (fee/limits set by admins)\n"
        "`/shop` (`/магазин`) — buy roles with coins\n"
        "`/cosmetics` (`/косметика`) — equip rank-card frame & title you own\n"
        "`/coins-top` (`/монеты-топ`) — richest members"
    ),
    "help.page.economy.field2.name": "Notes",
    "help.page.economy.field2.value": (
        "• Coins can also drop from XP activity if admins enabled it\n"
        "• Shop refunds automatically if Discord can’t grant the role\n"
        "• Staff may use grant tools — those are not listed here"
    ),
    "help.page.casino.title": "🎰 Casino",
    "help.page.casino.body": (
        "Coin games. Needs **Economy** and **Casino** enabled. "
        "Play responsibly — balances can go to zero."
    ),
    "help.page.casino.field1.name": "Commands",
    "help.page.casino.field1.value": (
        "Group `/casino` (`/казино`):\n"
        "• `blackjack` — hit/stand vs the dealer; stake coins\n"
        "• `slots` — three reels; matching symbols pay out\n"
        "• `coinflip` — pick a side; win doubles your stake\n"
        "• `top` — wins / losses leaderboard"
    ),
    "help.page.casino.field2.name": "Russian roulette bets",
    "help.page.casino.field2.value": (
        "`/russian-roulette` can take an optional coin stake when Casino + Economy are on: "
        "survive to multiply, or lose the bet (and take the timeout if you “die”)."
    ),
    "help.page.fun.title": "🎮 Games & fun",
    "help.page.fun.body": (
        "Mini-games and lobbies. Availability depends on Fun / Mafia / Bunker modules."
    ),
    "help.page.fun.field1.name": "Wordle & roulette",
    "help.page.fun.field1.value": (
        "`/wordle` (`/вордл`) — `play` daily · `training` · `stats` · `top`\n"
        "Daily board is private; the channel gets a color card without letters.\n\n"
        "`/russian-roulette` (`/русская-рулетка`) — odds rise each click (1/6 → 1/1); "
        "empty-cylinder chance; loser gets a timeout. Optional coin bet."
    ),
    "help.page.fun.field2.name": "Mafia & Bunker",
    "help.page.fun.field2.value": (
        "`/mafia-start` (`/мафия-игра`) — open a Mafia lobby (join via buttons / personal link)\n"
        "`/bunker-start` (`/бункер-игра`) — open a Bunker lobby\n"
        "Gameplay continues on your private web link. Hosts can manage the match from the dashboard."
    ),
    "help.page.fun.field3.name": "Quotes",
    "help.page.fun.field3.value": (
        "**Make it a Quote:** reply to a message and mention the bot → PNG quote card "
        "(if Fun / Quote is enabled)."
    ),
    "help.page.community.title": "🏠 Community",
    "help.page.community.body": (
        "Everyday server tools — birthdays, private voice rooms, family roster, supplies, polls."
    ),
    "help.page.community.field1.name": "Birthdays & polls",
    "help.page.community.field1.value": (
        "`/set-birthday` — your birthday as `MM-DD` (server calendar announcements)\n"
        "`/poll` — quick poll with up to 5 options"
    ),
    "help.page.community.field2.name": "Private voice rooms",
    "help.page.community.field2.value": (
        "Join the lobby voice channel → the bot creates **your** room and moves you there.\n"
        "Use the control panel (open/close, rename, limit, kick, transfer ownership).\n"
        "Empty rooms are deleted automatically."
    ),
    "help.page.community.field3.name": "Family & supplies (Games)",
    "help.page.community.field3.value": (
        "`/roster` (`/список`) — live family member list by roles\n"
        "`/др` / `/birthday` — family birthday list (`add` / `set` / `remove`)\n"
        "`/supply-run` (`/реаки-поставка`) — staff starts a supply sign-up; join with buttons\n"
        "`/family-applications` — apply to join the family when the panel is posted"
    ),
    "help.page.relations.title": "💕 Relations",
    "help.page.relations.body": (
        "Interactive actions between members raise relationship HP and pair level (up to 11). "
        "Propose, marry, divorce, and go on dates. "
        "The module must be enabled in the dashboard."
    ),
    "help.page.relations.field1.name": "Actions",
    "help.page.relations.field1.value": (
        "Group `/relations` (`/отношения`):\n"
        "`hug` · `kiss` · `slap` · `pat` · `highfive` · `cuddle` · `poke`\n"
        "Each grants HP (admin-configured), with per-pair cooldown and a daily limit. "
        "Married pairs get a spouse HP bonus."
    ),
    "help.page.relations.field2.name": "Card & top",
    "help.page.relations.field2.value": (
        "`/relations card` [member] — pair card; omit member to see your marriages\n"
        "`/relations top` — top pairs on the server"
    ),
    "help.page.relations.field3.name": "Romance",
    "help.page.relations.field3.value": (
        "`/relations marry` — proposal with buttons\n"
        "`divorce` · `marriages-top` · `ship` · `date` (bonus HP with spouse)\n"
        "Min level, married role, and announces — Dashboard → Romance."
    ),
    "help.page.valchecker.title": "🎯 ValChecker — Valorant",
    "help.page.valchecker.body": (
        "Link your Riot ID and check stats. Module must be **enabled** under Games → ValChecker. "
        "Needs Henrik API on the bot host."
    ),
    "help.page.valchecker.field1.name": "Account",
    "help.page.valchecker.field1.value": (
        "Group `/val`:\n"
        "`setup` — link / relink Riot `Name#TAG`, toggle **match tracking**, or unlink\n"
        "Tracking posts new competitive (and similar) matches to the server’s match channel."
    ),
    "help.page.valchecker.field2.name": "Stats & matches",
    "help.page.valchecker.field2.value": (
        "`/val profile` — overview · stats · agents · maps (nav buttons — only you can use them)\n"
        "`/val match` — latest match or recent history (`+5` loads more)\n"
        "`/val compare` — compare two linked users or Riot IDs\n"
        "`/val lb` — guild leaderboard by rank / WR / ACS\n"
        "`/val status` — incidents, queue times, or both (pick a region)"
    ),
    "help.page.valchecker.field3.name": "Tips",
    "help.page.valchecker.field3.value": (
        "• You can look up others with `user:` or `riot_id:` options\n"
        "• Unlink anytime in `/val setup`\n"
        "• Rate limits: if the API is busy, wait a minute and retry"
    ),
    "help.page.events.title": "🎉 Events & feedback",
    "help.page.events.body": (
        "Giveaways, events, brackets, and feedback are usually posted by staff as panels — "
        "you interact with **buttons and reactions**, not slash commands."
    ),
    "help.page.events.field1.name": "Giveaways & events",
    "help.page.events.field1.value": (
        "• React / press Join on a giveaway embed to enter\n"
        "• Event / tournament posts: sign up with the buttons\n"
        "• Brackets may have a public link to follow the tree"
    ),
    "help.page.events.field2.name": "Feedback & tickets",
    "help.page.events.field2.value": (
        "• Use the **feedback panel** in the configured channel for ideas / reports\n"
        "• Support tickets (if enabled) open a private thread with staff"
    ),
    "help.page.events.field3.name": "More help",
    "help.page.events.field3.value": (
        "Admins configure everything in the web dashboard. "
        "Public docs: cheterin.online/docs"
    ),
}
