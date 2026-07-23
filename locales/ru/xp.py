MESSAGES: dict[str, str] = {
    "xp.default_announce_template": (
        "Поздравляю {{member}}! 🎉\n"
        "Вы достигли **{{level}}** уровня. Спасибо за вашу активность на сервере!"
    ),
    "xp.disabled": "Система уровней отключена.",
    "xp.rank.no_bot_rank": "У ботов нет ранга.",
    "xp.no_bot_xp": "У ботов нет опыта.",
    "xp.leaders.empty": "Пока никто не заработал опыт.",
    "xp.add.success": "✅ Опыт {mention}: {current} → **{new_xp}**.",
    "xp.set.success": "✅ Опыт {mention} установлен: **{amount}**.",
    "xp.clear.success": "✅ Опыт {mention} обнулён.",
    "xp.leaderboard.title": "Топ рейтинга участников",
    "xp.leaderboard.no_data": "Нет данных.",
    "xp.leaderboard.prefix_top": "\u2B50 #{rank}.",
    "xp.leaderboard.prefix": "#{rank}.",
    "xp.leaderboard.row": (
        "**{prefix} {mention} ({display})**\n"
        "Уровень: {level} | Опыт: {xp} | \U0001f5e3\ufe0f {voice}"
    ),
    "xp.leaderboard.sort_xp": "опыту \U0001f3c6",
    "xp.leaderboard.sort_voice": "голосу \U0001f5e3\ufe0f",
    "xp.leaderboard.footer": (
        "Отсортировано по {mode_label} \u2022 Страница {page} из {max_pages} \u2014 "
        "Всего участников: {total}"
    ),
    "xp.leaderboard.btn_xp": "\U0001f3c6 Опыт",
    "xp.leaderboard.btn_voice": "\U0001f5e3\ufe0f Голос",
    "xp.leaderboard.left_server": "Покинул сервер",
    "xp.level_up.description": (
        "Поздравляю {mention}\U0001f929!\n"
        "Вы достигли **{level}** уровня. "
        "Спасибо за вашу активность на сервере {guild_name}"
    ),
    "xp.reward.add_reason": "Награда за уровень/войс-активность",
    "xp.reward.remove_reason": "Награда снята: недостаточный уровень/время",
    "xp.card.level": "Уровень {level}",
    "xp.card.rank": "Ранг {rank} из {total}",
    "xp.card.voice": "\U0001f50a В войсе: {time}",
    "xp.voice_time.week": "{n} нед.",
    "xp.voice_time.day": "{n} д.",
    "xp.voice_time.hour": "{n} ч.",
    "xp.voice_time.min": "{n} мин.",
}
