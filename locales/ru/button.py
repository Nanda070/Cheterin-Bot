MESSAGES: dict[str, str] = {
    "button.question_fallback": "Вопрос {index}",
    "button.answer_placeholder": "Ваш ответ…",
    "button.default_question": "Ответ",
    "button.embed.title": "\U0001f4dd Ответ по кнопке: {name}",
    "button.embed.submitter": "Отправитель",
    "button.embed.question_fallback": "Вопрос",
    "button.embed.footer": "404 Helper · Button Form",
    "button.webhook_missing": "BUTTON_WEBHOOK_URL не задан в переменных окружения.",
    "button.webhook_error": "\u26a0\ufe0f Ошибка отправки в вебхук: {error}",
    "button.sent": "\u2705 Отправлено!",
    "button.log.form_submit": "\U0001f4cb Форма отправлена",
    "button.log.form_submit_body": "**Кнопка:** {name}\n**Пользователь:** {mention} (`{user_id}`)",
    "button.log.form_footer": "Button · Form Submit",
    "button.cooldown": "\u23f3 Подождите {seconds:.0f} сек. перед следующим нажатием.",
    "button.role_not_found": "Роль не найдена на сервере.",
    "button.role_removed": "\u274c Роль **{name}** снята.",
    "button.role_added": "\u2705 Роль **{name}** выдана.",
    "button.role_remove_forbidden": "У бота нет прав для снятия этой роли.",
    "button.role_add_forbidden": "У бота нет прав для выдачи этой роли.",
    "button.role_action_removed": "снята",
    "button.role_action_added": "выдана",
    "button.log.role_title": "\U0001f3f7\ufe0f Роль через кнопку",
    "button.log.role_body": (
        "**Роль:** {mention} (`{role_id}`)\n"
        "**Действие:** {action}\n"
        "**Пользователь:** {mention_user} (`{user_id}`)"
    ),
    "button.log.role_footer": "Button · Role Toggle",
    "button.form_not_found": "\u26a0\ufe0f Конфигурация формы не найдена.",
    "button.modal_title": "Форма: {name}",
    "button.no_permission": "\u274c У вас нет прав для использования этой команды.",
    "button.form_created": "\u2705 Кнопка-форма создана.",
    "button.log.create_form": "\U0001f195 Создана кнопка-форма",
    "button.log.create_form_body": (
        "**Название:** {name}\n"
        "**Канал:** {channel}\n"
        "**Создал:** {mention} (`{user_id}`)"
    ),
    "button.log.questions": "Вопросы",
    "button.log.create_form_footer": "Button · Create Form",
    "button.need_role": "Укажите хотя бы одну роль (r1 – r5).",
    "button.role_created": "\u2705 Кнопка-роль создана.",
    "button.log.create_role": "\U0001f195 Создана кнопка-роль",
    "button.log.create_role_body": (
        "**Название:** {name}\n"
        "**Канал:** {channel}\n"
        "**Создал:** {mention} (`{user_id}`)"
    ),
    "button.log.roles": "Роли",
    "button.log.create_role_footer": "Button · Create Role",
}
