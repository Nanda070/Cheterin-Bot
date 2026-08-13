MESSAGES: dict[str, str] = {
    "streams.default_template_twitch": (
        "\U0001f534 **{{channel}}** went live: **{{stream}}**\n"
        "Playing {{game}} — join us! {{channel.url}}"
    ),
    "streams.default_template_youtube": (
        "\u25b6\ufe0f New video from **{{channel}}**: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.default_template_tiktok": (
        "\U0001f3b5 **{{channel}}** posted a new TikTok: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.embed.stream_title": "Stream",
    "streams.embed.game": "Game",
    "streams.embed.viewers": "Viewers",
    "streams.embed.author_twitch": "{name} — Twitch",
    "streams.embed.author_youtube": "{name} — YouTube",
    "streams.embed.author_tiktok": "{name} — TikTok",
    "streams.game_unknown": "—",
    "streams.test.sample_title": "[TEST] Sample stream title",
    "streams.test.sample_game": "Test Game",
    "streams.test.footer": "Test notification from dashboard",
}
