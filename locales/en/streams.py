MESSAGES: dict[str, str] = {
    "streams.default_template_twitch": (
        "\U0001f534 **{{channel}}** went live: **{{stream}}**\n"
        "Playing {{game}} — join us! {{channel.url}}"
    ),
    "streams.default_template_youtube": (
        "\u25b6\ufe0f New video from **{{channel}}**: **{{stream}}**\n{{channel.url}}"
    ),
    "streams.embed.stream_title": "Stream",
    "streams.embed.game": "Game",
    "streams.embed.viewers": "Viewers",
    "streams.embed.author_twitch": "{name} — Twitch",
    "streams.embed.author_youtube": "{name} — YouTube",
    "streams.game_unknown": "—",
}
