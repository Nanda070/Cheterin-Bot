MESSAGES: dict[str, str] = {
    "streams.default_template_twitch": (
        "\U0001f534 **{{channel}}** запустил трансляцию: **{{stream}}**\n"
        "Играем в {{game}} — заходите! {{channel.url}}"
    ),
    "streams.default_template_youtube": (
        "\u25b6\ufe0f Новое видео от **{{channel}}**: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.embed.stream_title": "Стрим",
    "streams.embed.game": "Игра",
    "streams.embed.viewers": "Зрителей",
    "streams.embed.author_twitch": "{name} — Twitch",
    "streams.embed.author_youtube": "{name} — YouTube",
    "streams.game_unknown": "—",
    "streams.test.sample_title": "[ТЕСТ] Пример названия стрима",
    "streams.test.sample_game": "Тестовая игра",
    "streams.test.footer": "Тестовое уведомление из дашборда",
}
