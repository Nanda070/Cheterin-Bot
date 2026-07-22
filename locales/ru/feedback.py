MESSAGES: dict[str, str] = {
    "feedback.need_text_channel": "Нужен обычный текстовый канал.",
    "feedback.panel_published": "Панель опубликована.",
    "feedback.create_failed": "Не удалось создать обращение.",
    "feedback.case_registered": (
        "Обращение зарегистрировано. Номер: **{case_id}**.\n"
        "Итог рассмотрения придёт вам в личные сообщения."
    ),
    "feedback.channel_not_found": "Целевой канал не найден или не является текстовым.",
    "feedback.category_deleted": (
        "\u274c Категория этого обращения была удалена. Обращение нельзя обработать."
    ),
    "feedback.case_not_found": "Обращение не найдено или уже закрыто.",
    "feedback.close_error": "\u274c Произошла ошибка при закрытии обращения. Администраторы уведомлены.",
    "feedback.no_mentions": "Без упоминаний",
    "feedback.btn_approve": "Принять",
    "feedback.btn_reject": "Отклонить",
    "feedback.field.submitter": "Отправитель",
    "feedback.field.status": "Статус",
    "feedback.field.summary": "Кратко",
    "feedback.field.public_message": "Публичное сообщение",
    "feedback.field.reviewer": "Рассмотрел",
    "feedback.field.footer_user_id": "ID пользователя: {user_id}",
    "feedback.field.footer_staff_only": "Доступно только для staff",
    "feedback.status.pending": "На рассмотрении",
    "feedback.status.awaiting_decision": "Ожидает решения",
    "feedback.status.approved": "Принято",
    "feedback.status.denied": "Отклонено",
    "feedback.status.reviewed": "Рассмотрено",
    "feedback.status.reviewed_with": "Рассмотрено · {status}",
    "feedback.case_title_public": "\U0001f4e8 {case_title} · {case_id}",
    "feedback.case_title_internal": "\U0001f512 Внутреннее обращение · {case_id}",
    "feedback.log.new_case": "\U0001f4e5 Создано новое обращение",
    "feedback.log.new_case_body": (
        "**Номер:** `{case_id}`\n"
        "**Отправитель:** {mention} (`{user_id}`)\n"
        "**Канал:** <#{channel_id}>\n"
        "**Ветка:** <#{thread_id}>\n"
        "**Пинги:** {mentions}"
    ),
    "feedback.error_create_title": "\u274c Ошибка при создании обращения",
    "feedback.error_create_body": (
        "**Категория:** {category}\n"
        "**Пользователь:** {mention} (`{user_id}`)\n"
        "**Ошибка:** `{error}`"
    ),
    "feedback.thread_reason": "Внутреннее обращение {case_id}",
    "feedback.dm.title": "Результат по обращению №{case_id}",
    "feedback.dm.description": "Ваше обращение было рассмотрено.",
    "feedback.dm.field.outcome": "Итог",
    "feedback.dm.footer": "Номер обращения: {case_id}",
    "feedback.log.decision": "\U0001f4cc Решение по обращению",
    "feedback.log.decision_body": (
        "**Номер:** `{case_id}`\n"
        "**Статус:** Рассмотрено\n"
        "**Решение:** {decision}\n"
        "**Рассмотрел:** {mention} (`{user_id}`)\n"
        "**DM:** {dm_status}"
    ),
    "feedback.log.dm_ok": "Успешно",
    "feedback.log.dm_fail": "Не удалось отправить",
    "feedback.thread.decision_title": "Решение по обращению {case_id}",
    "feedback.panel.description": (
        "### <:IconModeration:1356540597770518538>・Выберите тип связи со стаффом.\n\n"
        "```\n"
        "В создавшемся обращении, как можно точнее опишите его суть "
        "и по возможности прикрепите фото и/или видео для дальнейшего ознакомления.\n"
        "```"
    ),
    "feedback.log.panel_published": "\U0001f9e9 Панель feedback опубликована",
    "feedback.log.panel_published_body": (
        "**Кто:** {mention} (`{user_id}`)\n"
        "**Канал:** {channel_mention}\n"
        "**Сообщение:** [Открыть]({jump_url})"
    ),
    "feedback.link.open": "Открыть",
}
