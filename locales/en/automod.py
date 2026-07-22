MESSAGES: dict[str, str] = {
    "automod.default_notify_template": (
        "Hello {{member}}! You received a warning for breaking server rules: {{reason}}."
    ),
    "automod.reason": "Automod: {filter}",
    "automod.escalation_reason": "Automatic escalation: {count} active warning(s)",
    "automod.unban_reason": "Automod: temporary punishment expired",
    "automod.punishment_extra": "Punishment: {punishment}",
    "automod.escalation_extra": "Action: {action}",
    "automod.guild_only": "This command can only be used on a server.",
    "automod.warn.add_success": "⚠️ {mention} received a warning. Active warnings: **{count}**.",
    "automod.warn.no_warns": "{mention} has no warnings.",
    "automod.warn.list_title": "Warnings: {name}",
    "automod.warn.status_active": "🟢 active",
    "automod.warn.status_removed": "❌ removed",
    "automod.warn.status_expired": "⏱️ expired",
    "automod.warn.list_entry": "`#{id}` {status} — {reason}",
    "automod.warn.list_footer": "Active: {count}",
    "automod.warn.remove_not_found": "Warning not found or already removed.",
    "automod.warn.remove_success": "✅ Warning `#{id}` removed.",
}
