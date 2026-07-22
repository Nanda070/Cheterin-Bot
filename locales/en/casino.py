MESSAGES: dict[str, str] = {
    "casino.bet_min": "Minimum bet is {min}.",
    "casino.bet_max": "Maximum bet is {max}.",
    "casino.bet_insufficient": "Insufficient funds: balance is {balance}.",
    "casino.bj_active_first": "Finish your current blackjack game first.",
    "casino.cooldown": "Casino is resting — try again in {seconds} sec.",
    "casino.loss_role_reason": "Casino loss threshold reached",
    "casino.slots.miss": "🎰 {reels}\n{mention} — no luck. Balance: {balance}.",
    "casino.slots.win": (
        "🎰 {reels}\n{mention} — {kind}! Winnings: **{payout}** (balance: {balance})."
    ),
    "casino.slots.kind.jackpot": "Jackpot",
    "casino.slots.kind.match": "Match",
    "casino.coinflip.heads": "Heads",
    "casino.coinflip.tails": "Tails",
    "casino.coinflip.loss": (
        "{emoji} Result: **{label}**.\n{mention} guessed wrong. Balance: {balance}."
    ),
    "casino.coinflip.win": (
        "{emoji} Result: **{label}**.\n{mention} guessed right! Winnings: "
        "**{payout}** (balance: {balance})."
    ),
    "casino.top.btn.wins": "🏆 Wins",
    "casino.top.btn.losses": "❌ Losses",
    "casino.top.btn.mode_slots": "🎰 Slots/Coinflip",
    "casino.top.btn.mode_bj": "🎴 Blackjack",
    "casino.top.btn.mode_total": "📊 Overall",
    "casino.top.stat.wins": "wins",
    "casino.top.stat.losses": "losses",
    "casino.top.title": "Casino — Top by {stat} ({mode})",
    "casino.top.empty": "Leaderboard is empty.",
    "casino.top.footer": "Page {page} of {total}",
    "casino.top.mode.slots": "Slots/Coinflip",
    "casino.top.mode.bj": "Blackjack",
    "casino.top.mode.total": "Overall",
    "casino.top.not_your_menu": "This isn't your menu.",
    "casino.top.line.total.wins": (
        "{icon} **#{rank}.** {mention} — Total: {total} 🏆 (🎰 {slots} | 🎴 {bj})"
    ),
    "casino.top.line.total.losses": (
        "{icon} **#{rank}.** {mention} — Total: {total} ❌ (🎰 {slots} | 🎴 {bj})"
    ),
    "casino.top.line.slots": "{icon} **#{rank}.** {mention} — 🎰 {val} {emoji}",
    "casino.top.line.bj": "{icon} **#{rank}.** {mention} — 🎴 {val} {emoji}",
    "casino.bj.result.blackjack": "🃏 Blackjack!",
    "casino.bj.result.win": "✅ Win!",
    "casino.bj.result.push": "🤝 Push",
    "casino.bj.result.lose": "❌ Loss",
    "casino.bj.title": "🎴 Blackjack",
    "casino.bj.title_result": "🎴 Blackjack — {result}",
    "casino.bj.dealer": "Dealer — {value}",
    "casino.bj.player": "You — {value}",
    "casino.bj.bet": "Bet",
    "casino.bj.bet_doubled": " (doubled)",
    "casino.bj.prize": "Winnings",
    "casino.bj.prize_none": "—",
    "casino.bj.balance_footer": "Balance: {balance}",
    "casino.bj.btn_hit": "Hit",
    "casino.bj.btn_stand": "Stand",
    "casino.bj.btn_double": "Double",
    "casino.bj.timeout_footer": "⏰ Time's up — bet lost.",
    "casino.bj.double_insufficient": "Insufficient funds to double down.",
    "casino.bj.active_game": "You already have a blackjack game — finish it first.",
    "casino.bj.already_active": "You already have a blackjack game — finish it first.",
    "casino.bj.not_your_game": "This isn't your game.",
}
