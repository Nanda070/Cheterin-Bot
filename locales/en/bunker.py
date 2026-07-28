MESSAGES: dict[str, str] = {
    "bunker.lobby.title": "🚪 Bunker lobby",
    "bunker.lobby.description": "Press «Join» to participate.",
    "bunker.lobby.initiator": "Host",
    "bunker.lobby.players_needed": "Players needed",
    "bunker.lobby.timers": "Timers",
    "bunker.lobby.timers_value": "💬 {discussion}s · 🗳️ {vote}s",
    "bunker.lobby.capacity": "Bunker capacity",
    "bunker.lobby.cards": "Cards",
    "bunker.lobby.cards_unique": "No duplicates",
    "bunker.lobby.cards_repeat": "With duplicates",
    "bunker.lobby.participants": "Players [{count}/{max}]",
    "bunker.lobby.cancelled": "🚫 Lobby cancelled",
    "bunker.lobby.btn.join": "Join",
    "bunker.lobby.btn.leave": "Leave",
    "bunker.lobby.btn.force_start": "Start now",
    "bunker.lobby.btn.cancel": "Cancel",
    "bunker.lobby.unavailable": "Lobby unavailable.",
    "bunker.lobby.full": "Lobby is full.",
    "bunker.lobby.already_joined": "You are already in the lobby.",
    "bunker.lobby.not_in_lobby": "You are not in the lobby.",
    "bunker.lobby.no_access": "Access denied.",
    "bunker.lobby.min_players": "At least {min} players required (currently {count}).",
    "bunker.started.title": "🚪 Bunker game started!",
    "bunker.started.title_test": "🧪 [TEST] Bunker game started!",
    "bunker.started.description": (
        "Character cards were sent in DMs. Each player got a personal dashboard link — "
        "the full game is there: card, trait reveals, special abilities, and expulsion vote."
    ),
    "bunker.started.players": "Players",
    "bunker.started.capacity": "Bunker capacity",
    "bunker.started.voice_channel": "Voice channel",
    "bunker.started.catastrophe": "Catastrophe",
    "bunker.started.conditions": "Bunker conditions",
    "bunker.started.round_discussion": "Round {round} · 💬 Discussion — {seconds} sec",
    "bunker.vote.title": "🗳️ Expulsion vote",
    "bunker.vote.description": (
        "Voting happens on each player's personal link. "
        "Votes are public. Time: {seconds} sec."
    ),
    "bunker.vote.votes": "Votes",
    "bunker.vote.no_votes": "Nobody has voted yet.",
    "bunker.vote.skip": "Skip",
    "bunker.vote.alive_footer": "Alive players: {count}",
    "bunker.expulsion.title": "⚖️ Vote results",
    "bunker.expulsion.no_majority": "No majority — nobody left the bunker.",
    "bunker.expulsion.expelled": "<@{user_id}> leaves the bunker.",
    "bunker.result.stopped_title": "🚫 Game stopped",
    "bunker.result.stopped_desc": "The game was stopped early by a moderator.",
    "bunker.result.finished_title": "🏆 Bunker is full!",
    "bunker.result.finished_desc": "Voting is over — survivors have been decided.",
    "bunker.result.survivors": "✅ In bunker",
    "bunker.result.eliminated": "❌ Did not make it",
    "bunker.error.channel_busy": "This channel already has an active lobby/game.",
    "bunker.error.min_gt_max": "Minimum players cannot exceed maximum.",
    "bunker.error.capacity_too_high": "Bunker capacity must be less than max players.",
    "bunker.error.no_active_game": "No active game in this channel.",
    "bunker.error.guild_only": "This command can only be used on a server.",
    "bunker.stopped": "Stopped.",
    "bunker.voice_channel": "Bunker · Game #{game_id}",
    "bunker.voice_channel_test": "TEST · Bunker #{game_id}",
    "bunker.voice_delete_reason": "Bunker game finished",
    "bunker.test.ready": (
        "🧪 Test Bunker started with **{count}** players ({bots} bots).\n"
        "Your personal link: {link}\n"
        "Stop with `/bunker-stop` when done."
    ),
    "bunker.test.failed": "Test game failed to start (no token for your seat).",
    "bunker.dm.started": (
        "Bunker game started. Your personal character card (profession, health, backpack, "
        "special abilities, etc.) is on your personal link (valid for the whole game): "
        "{link}\nThere: trait reveals, special ability requests, and expulsion voting.{voice}"
    ),
    "bunker.dm.voice": " In <#{channel_id}>.",
    "bunker.event.game_started": "Players: {count}. Capacity: {capacity}.",
    "bunker.event.expelled": "Expelled: {user_id}",
    "bunker.event.no_expulsion": "Nobody expelled (no majority).",
    "bunker.event.game_ended_stopped": "Stopped",
    "bunker.event.game_ended_finished": "Bunker full",
    "bunker.ability.announce": (
        "🃏 Stop the game! Player **{player}** wants to use special ability "
        "«{card_name}».{target}{note}\nThe host applies the effect manually "
        "via the Bunker module panel in the dashboard."
    ),
    "bunker.ability.target": " Target: {target}.",
    "bunker.ability.note": " Note: {note}",
    "bunker.phase.vote_open": "🗳️ Expulsion vote is open — vote on your personal link.",
    "bunker.phase.discussion": (
        "💬 Round {round}: discussion and trait reveals — "
        "{seconds} sec. Links are already in hand."
    ),
    "bunker.log.finished": (
        "Bunker game #{game_id} in <#{channel_id}> finished. {outcome}"
    ),
    "bunker.log.stopped": "Stopped early.",
    "bunker.log.survivors": "Survivors: {survivors}/{total}.",
}
