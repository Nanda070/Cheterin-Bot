MESSAGES: dict[str, str] = {
    "casino.bet_min": "Минимальная ставка — {min}.",
    "casino.bet_max": "Максимальная ставка — {max}.",
    "casino.bet_insufficient": "Недостаточно средств: на балансе {balance}.",
    "casino.bj_active_first": "Сначала доиграй текущую партию в блэкджек.",
    "casino.cooldown": "Казино отдыхает — попробуй через {seconds} сек.",
    "casino.loss_role_reason": "Достигнут порог проигрышей в казино",
    "casino.slots.miss": "🎰 {reels}\n{mention} — мимо. Баланс: {balance}.",
    "casino.slots.win": (
        "🎰 {reels}\n{mention} — {kind}! Выигрыш: **{payout}** (баланс: {balance})."
    ),
    "casino.slots.kind.jackpot": "Джекпот",
    "casino.slots.kind.match": "Совпадение",
    "casino.coinflip.heads": "Орёл",
    "casino.coinflip.tails": "Решка",
    "casino.coinflip.loss": (
        "{emoji} Выпало: **{label}**.\n{mention} не угадал(а). Баланс: {balance}."
    ),
    "casino.coinflip.win": (
        "{emoji} Выпало: **{label}**.\n{mention} угадал(а)! Выигрыш: "
        "**{payout}** (баланс: {balance})."
    ),
    "casino.top.btn.wins": "🏆 Победы",
    "casino.top.btn.losses": "❌ Проигрыши",
    "casino.top.btn.mode_slots": "🎰 Слоты/Монетка",
    "casino.top.btn.mode_bj": "🎴 Блэкджек",
    "casino.top.btn.mode_total": "📊 Общий",
    "casino.top.stat.wins": "победам",
    "casino.top.stat.losses": "проигрышам",
    "casino.top.title": "Казино — Топ по {stat} ({mode})",
    "casino.top.empty": "Таблица пуста.",
    "casino.top.footer": "Страница {page} из {total}",
    "casino.top.mode.slots": "Слоты/Монетка",
    "casino.top.mode.bj": "Блэкджек",
    "casino.top.mode.total": "Общий",
    "casino.top.not_your_menu": "Это не ваше меню.",
    "casino.top.line.total.wins": (
        "{icon} **#{rank}.** {mention} — Всего: {total} 🏆 (🎰 {slots} | 🎴 {bj})"
    ),
    "casino.top.line.total.losses": (
        "{icon} **#{rank}.** {mention} — Всего: {total} ❌ (🎰 {slots} | 🎴 {bj})"
    ),
    "casino.top.line.slots": "{icon} **#{rank}.** {mention} — 🎰 {val} {emoji}",
    "casino.top.line.bj": "{icon} **#{rank}.** {mention} — 🎴 {val} {emoji}",
    "casino.bj.result.blackjack": "🃏 Блэкджек!",
    "casino.bj.result.win": "✅ Победа!",
    "casino.bj.result.push": "🤝 Ничья",
    "casino.bj.result.lose": "❌ Проигрыш",
    "casino.bj.title": "🎴 Блэкджек",
    "casino.bj.title_result": "🎴 Блэкджек — {result}",
    "casino.bj.dealer": "Дилер — {value}",
    "casino.bj.player": "Вы — {value}",
    "casino.bj.bet": "Ставка",
    "casino.bj.bet_doubled": " (удвоено)",
    "casino.bj.prize": "Выигрыш",
    "casino.bj.prize_none": "—",
    "casino.bj.balance_footer": "Баланс: {balance}",
    "casino.bj.btn_hit": "Ещё карту",
    "casino.bj.btn_stand": "Стоп",
    "casino.bj.btn_double": "Удвоить",
    "casino.bj.timeout_footer": "⏰ Время вышло — ставка потеряна.",
    "casino.bj.double_insufficient": "Недостаточно средств для удвоения.",
    "casino.bj.active_game": "У тебя уже идёт партия в блэкджек — сначала доиграй её.",
    "casino.bj.already_active": "У тебя уже идёт партия в блэкджек — сначала доиграй её.",
        "casino.bj.need_bet": "Укажите сумму ставки.",
    "casino.bj.not_your_game": "Это не твоя партия.",
}
