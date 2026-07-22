MESSAGES: dict[str, str] = {
    "button.question_fallback": "Question {index}",
    "button.answer_placeholder": "Your answer…",
    "button.default_question": "Answer",
    "button.embed.title": "\U0001f4dd Button form response: {name}",
    "button.embed.submitter": "Submitter",
    "button.embed.question_fallback": "Question",
    "button.embed.footer": "404 Helper · Button Form",
    "button.webhook_missing": "BUTTON_WEBHOOK_URL is not set in environment variables.",
    "button.webhook_error": "\u26a0\ufe0f Webhook send error: {error}",
    "button.sent": "\u2705 Sent!",
    "button.log.form_submit": "\U0001f4cb Form submitted",
    "button.log.form_submit_body": "**Button:** {name}\n**User:** {mention} (`{user_id}`)",
    "button.log.form_footer": "Button · Form Submit",
    "button.cooldown": "\u23f3 Wait {seconds:.0f} sec. before clicking again.",
    "button.role_not_found": "Role not found on this server.",
    "button.role_removed": "\u274c Role **{name}** removed.",
    "button.role_added": "\u2705 Role **{name}** assigned.",
    "button.role_remove_forbidden": "The bot lacks permission to remove this role.",
    "button.role_add_forbidden": "The bot lacks permission to assign this role.",
    "button.role_action_removed": "removed",
    "button.role_action_added": "assigned",
    "button.log.role_title": "\U0001f3f7\ufe0f Role via button",
    "button.log.role_body": (
        "**Role:** {mention} (`{role_id}`)\n"
        "**Action:** {action}\n"
        "**User:** {mention_user} (`{user_id}`)"
    ),
    "button.log.role_footer": "Button · Role Toggle",
    "button.form_not_found": "\u26a0\ufe0f Form configuration not found.",
    "button.modal_title": "Form: {name}",
    "button.no_permission": "\u274c You do not have permission to use this command.",
    "button.form_created": "\u2705 Form button created.",
    "button.log.create_form": "\U0001f195 Form button created",
    "button.log.create_form_body": (
        "**Name:** {name}\n"
        "**Channel:** {channel}\n"
        "**Created by:** {mention} (`{user_id}`)"
    ),
    "button.log.questions": "Questions",
    "button.log.create_form_footer": "Button · Create Form",
    "button.need_role": "Specify at least one role (r1 – r5).",
    "button.role_created": "\u2705 Role button created.",
    "button.log.create_role": "\U0001f195 Role button created",
    "button.log.create_role_body": (
        "**Name:** {name}\n"
        "**Channel:** {channel}\n"
        "**Created by:** {mention} (`{user_id}`)"
    ),
    "button.log.roles": "Roles",
    "button.log.create_role_footer": "Button · Create Role",
}
