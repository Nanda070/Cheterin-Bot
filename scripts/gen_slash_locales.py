"""One-off generator for locales/{ru,en}/slash.py — run from repo root."""

from pathlib import Path

ENTRIES = [
    ("userinfo", "userinfo", "userinfo", "Показать сводку по участнику сервера", "Show a member summary"),
    ("rank", "rank", "ранг", "Показать карточку ранга участника", "Show a member rank card"),
    ("leaders", "leaders", "leaders", "Показать таблицу лидеров", "Show the leaderboard"),
    ("xp_group", "xp", "xp", "Изменить количество опыта участника", "Change a member's XP amount"),
    ("xp_add", "add", "add", "Добавить (или отнять) опыт участнику", "Add or remove XP from a member"),
    ("xp_set", "set", "set", "Установить точное количество опыта участнику", "Set exact XP for a member"),
    ("xp_clear", "clear", "clear", "Обнулить опыт участника", "Reset a member XP to zero"),
    ("wordle", "wordle", "вордл", "Слово дня: 6 попыток угадать слово из 5 букв", "Daily Wordle: guess the 5-letter word in 6 tries"),
    ("wordle_training", "wordle-training", "вордл-тренировка", "Тренировочный Вордл со случайным словом (без статистики)", "Practice Wordle with a random word (no stats)"),
    ("wordle_stats", "wordle-stats", "вордл-стата", "Ваша статистика Вордла: победы, стрики, распределение", "Your Wordle stats: wins, streaks, distribution"),
    ("wordle_top", "wordle-top", "вордл-топ", "Топ игроков сервера в Вордл", "Server Wordle leaderboard"),
    ("russian_roulette", "russian-roulette", "русская-рулетка", "Спустить курок: барабан не прокручивается, с каждым щелчком шанс растёт. Можно ставить монеты", "Pull the trigger: odds rise each click. Optional coin bet"),
    ("emoji_roulette", "emoji-roulette", "эмодзи-рулетка", "Крутануть рулетку и получить случайное эмодзи сервера", "Spin the wheel for a random server emoji"),
    ("verify_setup", "verify_setup", "verify_setup", "Опубликовать панель верификации в текущем канале", "Post the verification panel in this channel"),
    ("ctd_setup", "ctd_setup", "ctd_setup", "Установить панель тикетов CTD", "Set up the CTD ticket panel"),
    ("family_applications", "family-applications", "семья-заявки", "Развернуть панель создания заявки в семью", "Post the family application panel"),
    ("roster", "roster", "список", "Создать live-сообщение со списком участников семьи", "Create a live family roster message"),
    ("birthday_add", "birthday-add", "добавить-др", "Добавить свой день рождения", "Add your birthday"),
    ("birthday_set", "birthday-set", "установить-др", "Установить день рождения участнику", "Set a member birthday"),
    ("birthday_remove", "birthday-remove", "удалить-др", "Удалить день рождения", "Remove a birthday"),
    ("supply_run", "supply-run", "реаки-поставка", "Создать сбор на поставку", "Start a supply collection"),
    ("antispam", "antispam", "antispam", "Включить / выключить антиспам-режим для ролей", "Enable or disable antispam mode for roles"),
    ("bunker_start", "bunker-start", "бункер-игра", "Создать лобби игры «Бункер»", "Create a Bunker game lobby"),
    ("bunker_stop", "bunker-stop", "бункер-стоп", "Остановить лобби/игру «Бункер» в этом канале", "Stop the Bunker lobby or game in this channel"),
    ("mafia_start", "mafia-start", "мафия-игра", "Создать лобби игры «Мафия»", "Create a Mafia game lobby"),
    ("mafia_stop", "mafia-stop", "мафия-стоп", "Остановить лобби/игру «Мафия» в этом канале", "Stop the Mafia lobby or game in this channel"),
    ("ban", "ban", "ban", "Забанить пользователя на сервере", "Ban a user from the server"),
    ("kick", "kick", "kick", "Кикнуть участника с сервера", "Kick a member from the server"),
    ("mute", "mute", "mute", "Выдать участнику таймаут (максимум 28 дней)", "Timeout a member (up to 28 days)"),
    ("unmute", "unmute", "unmute", "Досрочно снять таймаут с участника", "Remove a member timeout early"),
    ("unban", "unban", "unban", "Разбанить пользователя по ID", "Unban a user by ID"),
    ("clear", "clear", "clear", "Удалить сообщения в текущем канале", "Delete messages in the current channel"),
    ("blackjack", "blackjack", "блэкджек", "Сыграть в блэкджек против дилера на ставку монет", "Play blackjack against the dealer for coins"),
    ("slots", "slots", "слоты", "Крутить слоты на ставку монет: 3 барабана, совпадения дают выигрыш", "Spin the slots for coins: 3 reels, matches pay out"),
    ("coinflip", "coinflip", "монетка", "Подбросить монетку на ставку: угадал сторону — выигрыш", "Flip a coin for a bet: guess the side to win"),
    ("casino_top", "casino-top", "казино-топ", "Таблица лидеров казино по победам и проигрышам", "Casino leaderboard by wins and losses"),
    ("daily", "daily", "daily", "Забрать ежедневный бонус монет — растёт со стриком дней подряд", "Claim daily coin bonus — grows with consecutive-day streak"),
    ("balance", "balance", "баланс", "Показать баланс монет (свой или другого участника)", "Show coin balance (yours or another member)"),
    ("grant_balance", "grant-balance", "выдать-баланс", "Начислить (или списать) монеты участнику", "Grant or deduct coins from a member"),
    ("transfer", "transfer", "перевести", "Перевести монеты другому участнику", "Transfer coins to another member"),
    ("coins_top", "coins-top", "монеты-топ", "Топ участников по количеству монет", "Top members by coin balance"),
    ("shop", "shop", "магазин", "Магазин ролей за монеты", "Role shop for coins"),
    ("cosmetics", "cosmetics", "косметика", "Выбрать рамку карточки ранга и титул из купленного в магазине", "Choose rank card frame and title from shop purchases"),
    ("warn_group", "warn", "warn", "Управление предупреждениями участников", "Manage member warnings"),
    ("warn_add", "add", "add", "Выдать предупреждение участнику", "Issue a warning to a member"),
    ("warn_list", "list", "list", "Показать предупреждения участника", "Show warnings for a member"),
    ("warn_remove", "remove", "remove", "Снять предупреждение по ID", "Remove a warning by ID"),
    ("feedback_panel_group", "feedback_panel", "feedback_panel", "Управление панелью обратной связи", "Manage the feedback panel"),
    ("feedback_panel_send", "send", "send", "Опубликовать панель обратной связи", "Post the feedback panel"),
    ("button_group", "button_create", "button_create", "Создать кнопку (форма или выдача ролей)", "Create a button (form or role grant)"),
    ("button_form", "form", "form", "Создать кнопку с формой", "Create a button with a form"),
    ("button_role", "role", "role", "Создать кнопку для выдачи ролей", "Create a button that grants roles"),
    ("giveaway_group", "giveaway", "giveaway", "Розыгрыши призов", "Prize giveaways"),
    ("giveaway_start", "start", "start", "Начать розыгрыш приза", "Start a prize giveaway"),
    ("giveaway_reroll", "reroll", "reroll", "Перевыбрать победителя(ей) завершённого розыгрыша", "Reroll winner(s) of a finished giveaway"),
    ("giveaway_end", "end", "end", "Досрочно завершить розыгрыш", "End a giveaway early"),
    ("event_group", "event", "event", "Система турниров и событий", "Tournaments and events system"),
    ("event_setup", "setup", "setup", "Запустить конструктор событий/опросов", "Open the event/poll builder"),
    ("event_manage", "manage", "manage", "Управление активными событиями", "Manage active events"),
]


def render(lang: str) -> str:
    lines = ["MESSAGES: dict[str, str] = {"]
    for key, en, ru, desc_ru, desc_en in ENTRIES:
        desc = desc_ru if lang == "ru" else desc_en
        lines.append(f'    "slash.{key}.en": "{en}",')
        lines.append(f'    "slash.{key}.ru": "{ru}",')
        lines.append(f'    "slash.{key}.desc": "{desc}",')
    lines.append("}")
    return "\n".join(lines) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    (root / "locales/ru/slash.py").write_text(render("ru"), encoding="utf-8")
    (root / "locales/en/slash.py").write_text(render("en"), encoding="utf-8")
    print(f"written {len(ENTRIES)} entries")


if __name__ == "__main__":
    main()
