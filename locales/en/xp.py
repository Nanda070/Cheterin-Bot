MESSAGES: dict[str, str] = {
    "xp.default_announce_template": (
        "Congratulations {{member}}! 🎉\n"
        "You reached **{{level}}** level. Thank you for your activity on the server!"
    ),
    "xp.disabled": "Level system is disabled.",
    "xp.rank.no_bot_rank": "Bots don't have a rank.",
    "xp.no_bot_xp": "Bots don't have XP.",
    "xp.leaders.empty": "Nobody has earned XP yet.",
    "xp.add.success": "✅ XP for {mention}: {current} → **{new_xp}**.",
    "xp.set.success": "✅ XP for {mention} set to: **{amount}**.",
    "xp.clear.success": "✅ XP for {mention} cleared.",
    "xp.leaderboard.title": "Member leaderboard",
    "xp.leaderboard.no_data": "No data.",
    "xp.leaderboard.prefix_top": "\u2B50 #{rank}.",
    "xp.leaderboard.prefix": "#{rank}.",
    "xp.leaderboard.row": (
        "**{prefix} {mention} ({display})**\n"
        "Level: {level} | XP: {xp} | \U0001f5e3\ufe0f {voice}"
    ),
    "xp.leaderboard.sort_xp": "XP \U0001f3c6",
    "xp.leaderboard.sort_voice": "voice \U0001f5e3\ufe0f",
    "xp.leaderboard.footer": (
        "Sorted by {mode_label} \u2022 Page {page} of {max_pages} \u2014 Total members: {total}"
    ),
    "xp.leaderboard.btn_xp": "\U0001f3c6 XP",
    "xp.leaderboard.btn_voice": "\U0001f5e3\ufe0f Voice",
    "xp.level_up.description": (
        "Congratulations {mention}\U0001f929!\n"
        "You reached level **{level}**. "
        "Thank you for your activity on server {guild_name}"
    ),
    "xp.reward.add_reason": "Level/voice activity reward",
    "xp.reward.remove_reason": "Reward removed: insufficient level/time",
    "xp.card.level": "Level {level}",
    "xp.card.rank": "Rank {rank} of {total}",
    "xp.card.voice": "\U0001f50a In voice: {time}",
    "xp.voice_time.week": "{n} wk",
    "xp.voice_time.day": "{n} d",
    "xp.voice_time.hour": "{n} h",
    "xp.voice_time.min": "{n} min",
}
