MESSAGES: dict[str, str] = {
    "ctd.main_guild_only": "CTD доступен только на основном сервере.",
    "ctd.role_id_missing": "CTD_ROLE_ID не задан в переменных окружения.",
    "ctd.channel_id_missing": "CTD_CHANNEL_ID не задан в переменных окружения.",
    "ctd.no_close_permission": "У вас нет прав для закрытия тикета.",
    "ctd.btn_close": "Закрыть Тикет",
    "ctd.btn_create": "Создать Тикет",
    "ctd.ticket_closed_title": "\U0001f512 Тикет закрыт",
    "ctd.ticket_closed_body": "Ветка: {thread_name}\nЗакрыл: {mention}",
    "ctd.open_ticket_exists": "\u274c У вас уже есть открытый тикет: <#{thread_id}>",
    "ctd.ticket_prompt": (
        "{mention} Пожалуйста, опишите ваше обращение и ожидайте ответа администрации."
    ),
    "ctd.ticket_created_user": "Тикет успешно создан.",
    "ctd.ticket_created_log": "\U0001f3ab Создан новый тикет",
    "ctd.ticket_created_log_body": "Ветка: <#{thread_id}>\nПользователь: {mention}",
    "ctd.wrong_channel": "Команду нужно использовать в канале <#{channel_id}>",
    "ctd.panel_installed": "Панель установлена.",
    "ctd.panel_content": (
        "**Используйте форму обратной связи, чтобы сообщить о проблеме, предложить улучшение или получить помощь.**\n"
        "> Нажмите кнопку ниже, чтобы создать обращение. После нажатия автоматически откроется "
        "отдельная ветка, где можно подробно описать ситуацию."
    ),
    "ctd.inactive_warning": (
        "\u23f3 Тикет неактивен более 48 часов и будет автоматически закрыт через 24 часа."
    ),
    "ctd.auto_closed": "\U0001f512 Тикет автоматически закрыт по неактивности.",
}
