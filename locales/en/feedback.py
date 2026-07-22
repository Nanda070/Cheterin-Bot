MESSAGES: dict[str, str] = {
    "feedback.need_text_channel": "A regular text channel is required.",
    "feedback.panel_published": "Panel published.",
    "feedback.create_failed": "Could not create a case.",
    "feedback.case_registered": (
        "Your case has been registered. Reference: **{case_id}**.\n"
        "You will receive the outcome in a direct message."
    ),
    "feedback.channel_not_found": "Target channel not found or is not a text channel.",
    "feedback.category_deleted": (
        "\u274c The category for this case was deleted. The case cannot be processed."
    ),
    "feedback.case_not_found": "Case not found or already closed.",
    "feedback.close_error": "\u274c An error occurred while closing the case. Administrators have been notified.",
    "feedback.no_mentions": "No mentions",
    "feedback.btn_approve": "Approve",
    "feedback.btn_reject": "Reject",
    "feedback.field.submitter": "Submitter",
    "feedback.field.status": "Status",
    "feedback.field.summary": "Summary",
    "feedback.field.public_message": "Public message",
    "feedback.field.reviewer": "Reviewed by",
    "feedback.field.footer_user_id": "User ID: {user_id}",
    "feedback.field.footer_staff_only": "Staff only",
    "feedback.status.pending": "Under review",
    "feedback.status.awaiting_decision": "Awaiting decision",
    "feedback.status.approved": "Approved",
    "feedback.status.denied": "Denied",
    "feedback.status.reviewed": "Reviewed",
    "feedback.status.reviewed_with": "Reviewed · {status}",
    "feedback.case_title_public": "\U0001f4e8 {case_title} · {case_id}",
    "feedback.case_title_internal": "\U0001f512 Internal case · {case_id}",
    "feedback.log.new_case": "\U0001f4e5 New case created",
    "feedback.log.new_case_body": (
        "**Reference:** `{case_id}`\n"
        "**Submitter:** {mention} (`{user_id}`)\n"
        "**Channel:** <#{channel_id}>\n"
        "**Thread:** <#{thread_id}>\n"
        "**Mentions:** {mentions}"
    ),
    "feedback.error_create_title": "\u274c Error creating case",
    "feedback.error_create_body": (
        "**Category:** {category}\n"
        "**User:** {mention} (`{user_id}`)\n"
        "**Error:** `{error}`"
    ),
    "feedback.thread_reason": "Internal case {case_id}",
    "feedback.dm.title": "Outcome for case #{case_id}",
    "feedback.dm.description": "Your case has been reviewed.",
    "feedback.dm.field.outcome": "Outcome",
    "feedback.dm.footer": "Case reference: {case_id}",
    "feedback.log.decision": "\U0001f4cc Case decision",
    "feedback.log.decision_body": (
        "**Reference:** `{case_id}`\n"
        "**Status:** Reviewed\n"
        "**Decision:** {decision}\n"
        "**Reviewed by:** {mention} (`{user_id}`)\n"
        "**DM:** {dm_status}"
    ),
    "feedback.log.dm_ok": "Sent",
    "feedback.log.dm_fail": "Could not send",
    "feedback.thread.decision_title": "Decision for case {case_id}",
    "feedback.panel.description": (
        "### <:IconModeration:1356540597770518538>・Choose how to contact staff.\n\n"
        "```\n"
        "In your case, describe the issue as precisely as possible "
        "and attach photos and/or videos when you can.\n"
        "```"
    ),
    "feedback.log.panel_published": "\U0001f9e9 Feedback panel published",
    "feedback.log.panel_published_body": (
        "**By:** {mention} (`{user_id}`)\n"
        "**Channel:** {channel_mention}\n"
        "**Message:** [Open]({jump_url})"
    ),
    "feedback.link.open": "Open",
}
