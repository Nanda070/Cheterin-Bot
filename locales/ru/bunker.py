MESSAGES: dict[str, str] = {
    "bunker.lobby.title": "🚪 Лобби «Бункер»",
    "bunker.lobby.description": "Нажмите «Присоединиться», чтобы принять участие.",
    "bunker.lobby.initiator": "Инициатор",
    "bunker.lobby.players_needed": "Игроков нужно",
    "bunker.lobby.timers": "Таймеры",
    "bunker.lobby.timers_value": "💬 {discussion}с · 🗳️ {vote}с",
    "bunker.lobby.capacity": "Вместимость бункера",
    "bunker.lobby.cards": "Карточки",
    "bunker.lobby.cards_unique": "Без повторов",
    "bunker.lobby.cards_repeat": "С повторами",
    "bunker.lobby.participants": "Участники [{count}/{max}]",
    "bunker.lobby.cancelled": "🚫 Лобби отменено",
    "bunker.lobby.btn.join": "Присоединиться",
    "bunker.lobby.btn.leave": "Покинуть",
    "bunker.lobby.btn.force_start": "Начать сейчас",
    "bunker.lobby.btn.cancel": "Отменить",
    "bunker.lobby.unavailable": "Лобби недоступно.",
    "bunker.lobby.full": "Лобби заполнено.",
    "bunker.lobby.already_joined": "Ты уже в лобби.",
    "bunker.lobby.not_in_lobby": "Тебя нет в лобби.",
    "bunker.lobby.no_access": "Нет доступа.",
    "bunker.lobby.min_players": "Нужно минимум {min} игроков (сейчас {count}).",
    "bunker.started.title": "🚪 Игра «Бункер» началась!",
    "bunker.started.title_test": "🧪 [ТЕСТ] Игра «Бункер» началась!",
    "bunker.started.description": (
        "Карточки персонажей розданы в личные сообщения. Каждый игрок получил персональную ссылку "
        "на дашборд — там вся игра: карточка, раскрытие характеристик, спец. возможности и "
        "голосование за исключение."
    ),
    "bunker.started.players": "Игроков",
    "bunker.started.capacity": "Вместимость бункера",
    "bunker.started.voice_channel": "Голосовой канал",
    "bunker.started.catastrophe": "Катаклизм",
    "bunker.started.conditions": "Условия бункера",
    "bunker.started.round_discussion": "Раунд {round} · 💬 Обсуждение — {seconds} сек",
    "bunker.vote.title": "🗳️ Голосование за исключение",
    "bunker.vote.description": (
        "Голосование проходит на персональной ссылке каждого игрока. "
        "Голосование открытое. Время: {seconds} сек."
    ),
    "bunker.vote.votes": "Голоса",
    "bunker.vote.no_votes": "Пока никто не проголосовал.",
    "bunker.vote.skip": "Пропустить",
    "bunker.vote.alive_footer": "Живых игроков: {count}",
    "bunker.expulsion.title": "⚖️ Итоги голосования",
    "bunker.expulsion.no_majority": "Большинства не набралось — никто не покинул бункер.",
    "bunker.expulsion.expelled": "Бункер покидает <@{user_id}>.",
    "bunker.result.stopped_title": "🚫 Игра остановлена",
    "bunker.result.stopped_desc": "Игра остановлена модератором досрочно.",
    "bunker.result.finished_title": "🏆 Бункер укомплектован!",
    "bunker.result.finished_desc": "Голосования завершены — состав выживших определён.",
    "bunker.result.survivors": "✅ В бункере",
    "bunker.result.eliminated": "❌ Не прошли",
    "bunker.error.channel_busy": "В этом канале уже есть активное лобби/игра.",
    "bunker.error.min_gt_max": "Минимум игроков не может быть больше максимума.",
    "bunker.error.capacity_too_high": "Вместимость бункера должна быть меньше максимума игроков.",
    "bunker.error.no_active_game": "В этом канале нет активной игры.",
    "bunker.error.guild_only": "Команда доступна только на сервере.",
    "bunker.stopped": "Остановлено.",
    "bunker.voice_channel": "Бункер • Игра #{game_id}",
    "bunker.voice_channel_test": "ТЕСТ • Бункер #{game_id}",
    "bunker.voice_delete_reason": "Игра «Бункер» завершена",
    "bunker.test.ready": (
        "🧪 Тестовый «Бункер» запущен: **{count}** игроков ({bots} ботов).\n"
        "Ваша персональная ссылка: {link}\n"
        "Остановить: `/бункер-стоп`."
    ),
    "bunker.test.failed": "Не удалось запустить тестовую игру (нет токена для вашего места).",
    "bunker.dm.started": (
        "Игра «Бункер» началась. Твоя личная карточка персонажа (профессия, здоровье, рюкзак, "
        "спец. возможности и т.д.) — на персональной ссылке (действует всю игру): "
        "{link}\nТам же: раскрытие характеристик, заявка на спец. возможность и голосование "
        "за исключение.{voice}"
    ),
    "bunker.dm.voice": " В <#{channel_id}>.",
    "bunker.event.game_started": "Игроков: {count}. Вместимость: {capacity}.",
    "bunker.event.expelled": "Исключён: {user_id}",
    "bunker.event.no_expulsion": "Никто не исключён (нет большинства).",
    "bunker.event.game_ended_stopped": "Остановлено",
    "bunker.event.game_ended_finished": "Бункер укомплектован",
    "bunker.ability.announce": (
        "🃏 Стоп игра! Игрок **{player}** хочет использовать спец. возможность "
        "«{card_name}».{target}{note}\nВедущий применяет эффект вручную "
        "через панель модуля «Бункер» в дашборде."
    ),
    "bunker.ability.target": " Цель: {target}.",
    "bunker.ability.note": " Комментарий: {note}",
    "bunker.phase.vote_open": "🗳️ Голосование за исключение открыто — голосуйте на своей персональной ссылке.",
    "bunker.phase.discussion": (
        "💬 Раунд {round}: обсуждение и раскрытие характеристик — "
        "{seconds} сек. Ссылки уже на руках."
    ),
    "bunker.log.finished": (
        "Игра «Бункер» #{game_id} в <#{channel_id}> завершена. {outcome}"
    ),
    "bunker.log.stopped": "Остановлено досрочно.",
    "bunker.log.survivors": "Выжило: {survivors}/{total}.",
}
