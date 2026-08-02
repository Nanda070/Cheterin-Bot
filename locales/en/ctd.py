MESSAGES: dict[str, str] = {
    "ctd.main_guild_only": "CTD is only available on the main server.",
    "ctd.role_id_missing": "CTD_ROLE_ID is not set in environment variables.",
    "ctd.channel_id_missing": "CTD_CHANNEL_ID is not set in environment variables.",
    "ctd.no_close_permission": "You do not have permission to close this ticket.",
    "ctd.btn_close": "Close ticket",
    "ctd.btn_create": "Create ticket",
    "ctd.ticket_closed_title": "\U0001f512 Ticket closed",
    "ctd.ticket_closed_body": "Thread: {thread_name}\nClosed by: {mention}",
    "ctd.open_ticket_exists": "\u274c You already have an open ticket: <#{thread_id}>",
    "ctd.ticket_prompt": (
        "{mention} Please describe your issue and wait for a response from the staff."
    ),
    "ctd.ticket_created_user": "Ticket created successfully.",
    "ctd.ticket_create_failed": "Could not create the ticket. Try again or contact staff.",
    "ctd.ticket_created_log": "\U0001f3ab New ticket created",
    "ctd.ticket_created_log_body": "Thread: <#{thread_id}>\nUser: {mention}",
    "ctd.wrong_channel": "Use this command in <#{channel_id}>",
    "ctd.panel_installed": "Panel installed.",
    "ctd.panel_content": (
        "**Use the feedback form to report a problem, suggest an improvement, or get help.**\n"
        "> Click the button below to open a case. A private thread will open "
        "where you can describe the situation in detail."
    ),
    "ctd.inactive_warning": (
        "\u23f3 This ticket has been inactive for over 48 hours and will be "
        "closed automatically in 24 hours."
    ),
    "ctd.auto_closed": "\U0001f512 Ticket automatically closed due to inactivity.",
}
