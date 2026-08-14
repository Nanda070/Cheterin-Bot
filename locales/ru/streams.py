MESSAGES: dict[str, str] = {
    "streams.default_template_twitch": (
        "\U0001f534 **{{channel}}** запустил трансляцию: **{{stream}}**\n"
        "Играем в {{game}} — заходите! {{channel.url}}"
    ),
    "streams.default_template_youtube": (
        "\u25b6\ufe0f Новое видео от **{{channel}}**: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.default_template_tiktok": (
        "\U0001f3b5 **{{channel}}** вышло новое видео в TikTok: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.default_template_tiktok_live": (
        "**{{channel}}** запустил стрим, залетай!"
    ),
    "streams.embed.stream_title": "Стрим",
    "streams.embed.game": "Игра",
    "streams.embed.viewers": "Зрителей",
    "streams.embed.author_twitch": "{name} — Twitch",
    "streams.embed.author_youtube": "{name} — YouTube",
    "streams.embed.author_tiktok": "{name} — TikTok",
    "streams.embed.author_tiktok_live": "{name} — TikTok LIVE",
    "streams.embed.live_title": "В эфире",
    "streams.embed.live_description": "**{name}** сейчас в эфире на TikTok!",
    "streams.btn.watch_live": "Смотреть стрим",
    "streams.btn.watch_video": "Смотреть видео",
    "streams.btn.tiktok": "TikTok",
    "streams.game_unknown": "—",
    "streams.test.sample_title": "[ТЕСТ] Пример названия стрима",
    "streams.test.sample_game": "Тестовая игра",
    "streams.test.footer": "Тестовое уведомление из дашборда",
}
