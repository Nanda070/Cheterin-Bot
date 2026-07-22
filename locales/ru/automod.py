MESSAGES: dict[str, str] = {
    "automod.default_notify_template": (
        "Привет {{member}}! Вы получили предупреждение за нарушение правил сервера: {{reason}}."
    ),
    "automod.reason": "Автомодерация: {filter}",
    "automod.escalation_reason": "Автоматическая эскалация: {count} активных предупреждений",
    "automod.unban_reason": "Автомодерация: истёк срок временного наказания",
    "automod.punishment_extra": "Наказание: {punishment}",
    "automod.escalation_extra": "Действие: {action}",
    "automod.guild_only": "Команда доступна только на сервере.",
    "automod.warn.add_success": "⚠️ {mention} получил предупреждение. Активных предупреждений: **{count}**.",
    "automod.warn.no_warns": "У {mention} нет предупреждений.",
    "automod.warn.list_title": "Предупреждения: {name}",
    "automod.warn.status_active": "🟢 активно",
    "automod.warn.status_removed": "❌ снято",
    "automod.warn.status_expired": "⏱️ истекло",
    "automod.warn.list_entry": "`#{id}` {status} — {reason}",
    "automod.warn.list_footer": "Активных: {count}",
    "automod.warn.remove_not_found": "Предупреждение не найдено или уже снято.",
    "automod.warn.remove_success": "✅ Предупреждение `#{id}` снято.",
}
