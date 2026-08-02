MESSAGES: dict[str, str] = {
    "relations.disabled": "The Relations module is disabled on this server.",
    "relations.self": "You can’t target yourself — pick another member.",
    "relations.bot_target": "Actions don’t work on bots.",
    "relations.action_disabled": "This action is disabled by admins.",
    "relations.daily_limit": "Daily action limit reached ({limit}). Try again tomorrow.",
    "relations.cooldown": "Wait {seconds}s before using this action with that member again.",
    "relations.action.hug": "hugged",
    "relations.action.kiss": "kissed",
    "relations.action.slap": "slapped",
    "relations.action.pat": "patted",
    "relations.action.highfive": "high-fived",
    "relations.action.cuddle": "cuddled",
    "relations.action.poke": "poked",
    "relations.action_title": "{emoji} {action}",
    "relations.action_body": (
        "{actor} → {target}\n"
        "+{hp} relationship HP · total **{total}** · level **{level}**\n"
        "{progress}"
    ),
    "relations.married_bonus_note": "💍 Spouse bonus +{pct}% HP",
    "relations.progress": "Progress to next level: {into}/{need}",
    "relations.progress_max": "Max relationship level!",
    "relations.card_need_other": "Pick another member to show the pair card.",
    "relations.card_empty": "No relationship HP with {user} yet — try an action!",
    "relations.card_title": "Relationship card",
    "relations.card_body": (
        "{a} × {b}\n"
        "Level **{level}** · **{hp}** HP\n"
        "{progress}"
    ),
    "relations.card_married": "💍 Married · **{days}** days together",
    "relations.top_empty": "No pairs yet — start with `/relations hug` or another action.",
    "relations.top_title": "Server relationship top",
    "relations.top_line": "**#{n}** {a} × {b} — lv. {level} · {hp} HP",
    "relations.announce.title": "Relationship level up!",
    "relations.announce.body": "{a} and {b} reached level **{level}** ({hp} HP).",
    "relations.role.add_reason": "Relationship level reward",
    "relations.role.remove_reason": "Relationship reward removed",
    # Romance
    "relations.marriage.disabled": "Romance (marriage) is disabled on this server.",
    "relations.marriage.already": "You’re already married to {user}.",
    "relations.marriage.you_taken": "You’re already married. Use /divorce first.",
    "relations.marriage.they_taken": "{user} is already married.",
    "relations.marriage.proposer_taken": "The proposer is already married.",
    "relations.marriage.target_taken": "You’re already married to someone else.",
    "relations.marriage.level_low": (
        "You need relationship level **{need}** to propose (currently **{level}**). "
        "Earn HP with actions!"
    ),
    "relations.marriage.wed_title": "💍 You’re married!",
    "relations.marriage.wed_body": "{a} and {b} are now spouses. Congrats!",
    "relations.marriage.announce_title": "Wedding!",
    "relations.marriage.announce_body": "💍 {a} and {b} just got married!",
    "relations.marriage.role_add": "Married role",
    "relations.marriage.role_remove": "Married role removed",
    "relations.propose.title": "Marriage proposal",
    "relations.propose.body": (
        "{proposer} proposes to {target}!\n"
        "They have **{seconds}**s to answer."
    ),
    "relations.propose.btn_accept": "Accept",
    "relations.propose.btn_decline": "Decline",
    "relations.propose.only_target": "Only the person who was proposed to can answer.",
    "relations.propose.only_parties": "Only the proposal parties can press this.",
    "relations.propose.declined_title": "Proposal declined",
    "relations.propose.declined_body": "{target} declined {proposer}’s proposal.",
    "relations.propose.expired": "That proposal has expired.",
    "relations.propose.already_out": "You already have an active proposal. Wait for a reply.",
    "relations.divorce.title": "Divorce",
    "relations.divorce.mutual_body": (
        "{initiator} wants to divorce {spouse}.\n"
        "The spouse must confirm or stay together."
    ),
    "relations.divorce.solo_body": "Confirm divorce from {spouse}.",
    "relations.divorce.btn_accept": "Agree to divorce",
    "relations.divorce.btn_stay": "Stay together",
    "relations.divorce.btn_confirm": "Divorce",
    "relations.divorce.btn_cancel": "Cancel",
    "relations.divorce.only_spouse": "Only your spouse can confirm.",
    "relations.divorce.only_initiator": "Only the initiator can confirm.",
    "relations.divorce.only_parties": "Only the spouses can press this.",
    "relations.divorce.cancelled_title": "Divorce cancelled",
    "relations.divorce.cancelled_body": "You’re staying together.",
    "relations.divorce.done_title": "Divorced",
    "relations.divorce.done_body": "{a} and {b} are no longer spouses.",
    "relations.divorce.announce_title": "Divorce",
    "relations.divorce.announce_body": "{a} and {b} got divorced.",
    "relations.divorce.not_married": "That marriage no longer exists.",
    "relations.divorce.not_married_you": "You’re not married.",
    "relations.divorce.not_with": "You’re not married to {user}.",
    "relations.divorce.pick_spouse": "Pick a spouse: `/relations divorce member:…`",
    "relations.spouse.title": "💍 {user}",
    "relations.spouse.none_self": "You’re not married yet. Propose with `/relations marry`.",
    "relations.spouse.none_other": "{user} is not married.",
    "relations.spouse.line": "♥ {spouse} · **{days}** days · lv. {level} · {hp} HP",
    "relations.marriages_top.empty": "No marriages on this server yet.",
    "relations.marriages_top.title": "Longest marriages",
    "relations.marriages_top.line": (
        "**#{n}** {a} × {b} — **{days}** days · lv. {level} · {hp} HP"
    ),
    "relations.ship.title": "Ship meter",
    "relations.ship.body": "{a} × {b}\n{bar}\n**{score}%** — {tier}",
    "relations.ship.same": "Pick two different members.",
    "relations.ship.tier.soulmates": "soulmates",
    "relations.ship.tier.hot": "on fire",
    "relations.ship.tier.spark": "there’s a spark",
    "relations.ship.tier.friendzone": "friendzone",
    "relations.ship.tier.awkward": "awkward…",
    "relations.date.need_spouse": "Dates are only with your spouse.",
    "relations.date.title": "🌹 Date",
    "relations.date.body": (
        "{a} and {b} went on a date!\n"
        "+{hp} HP · total **{total}** · level **{level}**\n"
        "{progress}"
    ),
}
