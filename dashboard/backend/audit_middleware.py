"""Аудит действий дашборда: каждое мутирующее действие модератора пишется в stats.db."""

import logging
import re
import time

from aiohttp import web

import stats_db

logger = logging.getLogger("dashboard.audit")

# Порядок важен: первое совпадение по (метод|*, префикс) даёт ключ i18n (audit.action.*).
# В БД пишется ключ; UI переводит по языку интерфейса. Никогда не пишем сырой "PUT /api/...".
ACTION_LABELS: list[tuple[str, str, str]] = [
    ("PUT", "/api/config", "audit.action.config"),
    ("PUT", "/api/language", "audit.action.language"),
    ("PUT", "/api/ctd", "audit.action.ctd"),
    ("POST", "/api/lockdown/activate", "audit.action.lockdown_on"),
    ("POST", "/api/lockdown/deactivate", "audit.action.lockdown_off"),
    ("PUT", "/api/spam-settings", "audit.action.spam_settings"),
    ("PUT", "/api/tempban-settings", "audit.action.tempban_settings"),
    ("PUT", "/api/antiraid", "audit.action.antiraid"),
    ("PUT", "/api/verification", "audit.action.verification"),
    ("POST", "/api/members/", "audit.action.member"),
    ("DELETE", "/api/members/", "audit.action.member_role_remove"),
    ("POST", "/api/roles/", "audit.action.mass_assign"),
    ("POST", "/api/mass-assign", "audit.action.mass_assign"),
    ("PUT", "/api/welcome-settings", "audit.action.welcome"),
    ("PUT", "/api/welcome", "audit.action.welcome"),
    ("PUT", "/api/auto-roles", "audit.action.auto_roles"),
    ("POST", "/api/reaction-roles", "audit.action.reaction_roles_create"),
    ("PUT", "/api/reaction-roles", "audit.action.reaction_roles_update"),
    ("DELETE", "/api/reaction-roles", "audit.action.reaction_roles_delete"),
    ("POST", "/api/embed-messages", "audit.action.embed"),
    ("PUT", "/api/embed-messages", "audit.action.embed"),
    ("POST", "/api/embed-templates", "audit.action.embed"),
    ("DELETE", "/api/embed-templates", "audit.action.embed"),
    ("POST", "/api/embed-builder", "audit.action.embed"),
    ("POST", "/api/message-templates", "audit.action.message_template"),
    ("PUT", "/api/message-templates", "audit.action.message_template"),
    ("DELETE", "/api/message-templates", "audit.action.message_template"),
    ("POST", "/api/feedback-cases", "audit.action.feedback"),
    ("POST", "/api/feedback-categories", "audit.action.feedback_update"),
    ("PUT", "/api/feedback-categories", "audit.action.feedback_update"),
    ("DELETE", "/api/feedback-categories", "audit.action.feedback_delete"),
    ("POST", "/api/feedback-panel", "audit.action.feedback"),
    ("PUT", "/api/feedback-panel-settings", "audit.action.feedback_update"),
    ("POST", "/api/feedback", "audit.action.feedback"),
    ("PUT", "/api/feedback", "audit.action.feedback_update"),
    ("DELETE", "/api/feedback", "audit.action.feedback_delete"),
    ("POST", "/api/events", "audit.action.events"),
    ("DELETE", "/api/events", "audit.action.events_delete"),
    ("POST", "/api/brackets", "audit.action.brackets"),
    ("DELETE", "/api/brackets", "audit.action.brackets_delete"),
    ("POST", "/api/supply", "audit.action.supply"),
    ("DELETE", "/api/voice/rooms", "audit.action.voice_room_delete"),
    ("POST", "/api/voice/panel", "audit.action.voice_panel"),
    ("PUT", "/api/voice", "audit.action.voice_settings"),
    ("PUT", "/api/news", "audit.action.news"),
    ("PUT", "/api/serverlog", "audit.action.serverlog"),
    ("PUT", "/api/xp/members", "audit.action.xp_member"),
    ("POST", "/api/xp/members", "audit.action.xp_member_reset"),
    ("POST", "/api/xp/reset-all", "audit.action.xp_reset_all"),
    ("POST", "/api/economy/reset-all", "audit.action.economy_reset_all"),
    ("POST", "/api/xp/card-bg", "audit.action.xp_card_bg"),
    ("DELETE", "/api/xp/card-bg", "audit.action.xp_card_bg_delete"),
    ("PUT", "/api/xp", "audit.action.xp_settings"),
    ("POST", "/api/streams", "audit.action.streams"),
    ("PATCH", "/api/streams", "audit.action.streams_update"),
    ("DELETE", "/api/streams", "audit.action.streams_delete"),
    ("PUT", "/api/family", "audit.action.family"),
    ("POST", "/api/family/tickets/", "audit.action.family_ticket"),
    ("POST", "/api/family/birthdays", "audit.action.family_birthday"),
    ("DELETE", "/api/family/birthdays", "audit.action.family_birthday_delete"),
    ("PUT", "/api/mafia", "audit.action.mafia"),
    ("PUT", "/api/bunker", "audit.action.bunker"),
    ("PATCH", "/api/bunker", "audit.action.bunker"),
    ("POST", "/api/bunker", "audit.action.bunker"),
    ("PUT", "/api/casino", "audit.action.casino"),
    ("PUT", "/api/economy/balance", "audit.action.economy_balance"),
    ("PUT", "/api/economy", "audit.action.economy"),
    ("PUT", "/api/fun", "audit.action.fun"),
    ("PUT", "/api/wordle", "audit.action.wordle"),
    ("POST", "/api/giveaways", "audit.action.giveaways"),
    ("PUT", "/api/daily-topic/settings", "audit.action.daily_topic"),
    ("POST", "/api/daily-topic/topics", "audit.action.daily_topic_add"),
    ("PATCH", "/api/daily-topic/topics", "audit.action.daily_topic_update"),
    ("DELETE", "/api/daily-topic/topics", "audit.action.daily_topic_delete"),
    ("POST", "/api/daily-topic/post-now", "audit.action.daily_topic_post"),
    ("PUT", "/api/automod/filters/", "audit.action.automod_filter"),
    ("PUT", "/api/automod/manual-warn-duration", "audit.action.automod_warn_duration"),
    ("POST", "/api/automod/escalation", "audit.action.automod_escalation_add"),
    ("PATCH", "/api/automod/escalation/", "audit.action.automod_escalation_update"),
    ("DELETE", "/api/automod/escalation/", "audit.action.automod_escalation_delete"),
    ("PUT", "/api/automod", "audit.action.automod"),
    ("DELETE", "/api/warns/", "audit.action.warn_remove"),
    ("PUT", "/api/bot-profile", "audit.action.bot_profile"),
    ("PUT", "/api/starboard", "audit.action.starboard"),
    ("PUT", "/api/valchecker", "audit.action.valchecker"),
    ("PUT", "/api/customs", "audit.action.customs"),
    ("POST", "/api/customs/lobbies", "audit.action.customs_lobby"),
    ("POST", "/api/customs/schedules", "audit.action.customs_schedule"),
    ("DELETE", "/api/customs/schedules", "audit.action.customs_schedule_delete"),
    ("POST", "/api/customs/lobbies/", "audit.action.customs_lobby"),
    ("PUT", "/api/auto-reactions", "audit.action.auto_reactions"),
    ("PUT", "/api/quote", "audit.action.quote"),
    ("POST", "/api/tempban-settings/publish-warning", "audit.action.tempban_publish"),
    ("PUT", "/api/banner-rotation", "audit.action.banner_rotation"),
    ("POST", "/api/banner-rotation/banners", "audit.action.banner_rotation"),
    ("DELETE", "/api/banner-rotation/banners/", "audit.action.banner_rotation"),
    ("POST", "/api/banner-rotation/icons", "audit.action.banner_rotation"),
    ("DELETE", "/api/banner-rotation/icons/", "audit.action.banner_rotation"),
    ("POST", "/api/banner-rotation/rotate-now", "audit.action.banner_rotation"),
    ("PUT", "/api/ideas", "audit.action.ideas"),
    ("POST", "/api/ideas", "audit.action.ideas"),
    ("PUT", "/api/polls", "audit.action.polls"),
    ("POST", "/api/polls", "audit.action.polls"),
    ("PUT", "/api/sticky-roles", "audit.action.sticky_roles"),
    ("PUT", "/api/sticky", "audit.action.sticky"),
    ("POST", "/api/sticky", "audit.action.sticky"),
    ("DELETE", "/api/sticky", "audit.action.sticky"),
    ("PUT", "/api/custom-commands", "audit.action.custom_commands"),
    ("POST", "/api/custom-commands", "audit.action.custom_commands"),
    ("PATCH", "/api/custom-commands", "audit.action.custom_commands"),
    ("DELETE", "/api/custom-commands", "audit.action.custom_commands"),
    ("PUT", "/api/scheduled-messages", "audit.action.scheduled_messages"),
    ("POST", "/api/scheduled-messages", "audit.action.scheduled_messages"),
    ("PATCH", "/api/scheduled-messages", "audit.action.scheduled_messages"),
    ("DELETE", "/api/scheduled-messages", "audit.action.scheduled_messages"),
    ("PUT", "/api/invites", "audit.action.invites"),
    ("PUT", "/api/owner-alerts", "audit.action.owner_alerts"),
    ("POST", "/api/owner-alerts", "audit.action.owner_alerts"),
    ("PUT", "/api/timezone", "audit.action.timezone"),
    ("POST", "/api/preview", "audit.action.preview"),
    ("PUT", "/api/relations", "audit.action.relations"),
    ("PUT", "/api/valorant", "audit.action.valorant"),
    ("POST", "/api/valorant", "audit.action.valorant"),
    ("DELETE", "/api/timed-roles", "audit.action.timed_roles"),
    ("PUT", "/api/lockdown/exempt", "audit.action.lockdown_exempt"),
]

# Path-only fallbacks (any method) for older/unknown verb combinations.
PATH_LABELS: list[tuple[str, str]] = [
    ("/api/wordle", "audit.action.wordle"),
    ("/api/fun", "audit.action.fun"),
    ("/api/casino", "audit.action.casino"),
    ("/api/economy", "audit.action.economy"),
    ("/api/bunker", "audit.action.bunker"),
    ("/api/mafia", "audit.action.mafia"),
    ("/api/config", "audit.action.config"),
    ("/api/language", "audit.action.language"),
    ("/api/ctd", "audit.action.ctd"),
    ("/api/spam-settings", "audit.action.spam_settings"),
    ("/api/tempban-settings", "audit.action.tempban_settings"),
    ("/api/antiraid", "audit.action.antiraid"),
    ("/api/verification", "audit.action.verification"),
    ("/api/welcome", "audit.action.welcome"),
    ("/api/auto-roles", "audit.action.auto_roles"),
    ("/api/reaction-roles", "audit.action.reaction_roles_update"),
    ("/api/embed-", "audit.action.embed"),
    ("/api/feedback", "audit.action.feedback"),
    ("/api/events", "audit.action.events"),
    ("/api/brackets", "audit.action.brackets"),
    ("/api/supply", "audit.action.supply"),
    ("/api/voice", "audit.action.voice_settings"),
    ("/api/news", "audit.action.news"),
    ("/api/serverlog", "audit.action.serverlog"),
    ("/api/xp", "audit.action.xp_settings"),
    ("/api/streams", "audit.action.streams"),
    ("/api/family", "audit.action.family"),
    ("/api/giveaways", "audit.action.giveaways"),
    ("/api/daily-topic", "audit.action.daily_topic"),
    ("/api/automod", "audit.action.automod"),
    ("/api/warns", "audit.action.warn_remove"),
    ("/api/members", "audit.action.member"),
    ("/api/roles", "audit.action.mass_assign"),
    ("/api/lockdown/exempt", "audit.action.lockdown_exempt"),
    ("/api/lockdown", "audit.action.lockdown_on"),
    ("/api/bot-profile", "audit.action.bot_profile"),
    ("/api/banner-rotation", "audit.action.banner_rotation"),
    ("/api/starboard", "audit.action.starboard"),
    ("/api/valchecker", "audit.action.valchecker"),
    ("/api/customs", "audit.action.customs"),
    ("/api/auto-reactions", "audit.action.auto_reactions"),
    ("/api/ideas", "audit.action.ideas"),
    ("/api/polls", "audit.action.polls"),
    ("/api/sticky-roles", "audit.action.sticky_roles"),
    ("/api/sticky", "audit.action.sticky"),
    ("/api/custom-commands", "audit.action.custom_commands"),
    ("/api/scheduled-messages", "audit.action.scheduled_messages"),
    ("/api/invites", "audit.action.invites"),
    ("/api/owner-alerts", "audit.action.owner_alerts"),
    ("/api/timezone", "audit.action.timezone"),
    ("/api/preview", "audit.action.preview"),
    ("/api/relations", "audit.action.relations"),
    ("/api/valorant", "audit.action.valorant"),
    ("/api/timed-roles", "audit.action.timed_roles"),
]

_RAW_ACTION_RE = re.compile(r"^(GET|POST|PUT|PATCH|DELETE)\s+(/api/\S+)$", re.I)

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def describe_action(method: str, path: str) -> str:
    for label_method, prefix, label in ACTION_LABELS:
        if method == label_method and path.startswith(prefix):
            return label
    for prefix, label in PATH_LABELS:
        if path.startswith(prefix):
            return label
    return "audit.action.other"


def normalize_stored_action(action: str) -> str:
    """Map legacy 'PUT /api/wordle' (and similar) rows to i18n keys."""
    if action.startswith("audit.action."):
        return action
    match = _RAW_ACTION_RE.match(action.strip())
    if match:
        return describe_action(match.group(1).upper(), match.group(2))
    return action


@web.middleware
async def audit_middleware(request: web.Request, handler):
    response = await handler(request)
    try:
        if (
            request.method in MUTATING_METHODS
            and request.path.startswith("/api/")
            and not request.path.startswith("/api/auth")
            and not request.path.startswith("/api/public/")
        ):
            moderator = request.get("moderator")
            status = getattr(response, "status", 0)
            if moderator is not None and 200 <= status < 300:
                stats_db.audit_add(
                    request.get("guild_id", request.app.get("guild_id")),
                    ts=int(time.time()),
                    moderator_id=moderator.id,
                    moderator_name=getattr(moderator, "display_name", str(moderator.id)),
                    method=request.method,
                    path=request.path,
                    action=describe_action(request.method, request.path),
                    status=status,
                    details=str(request.get("audit_details", "")),
                )
    except Exception:
        logger.exception("Не удалось записать аудит для %s %s", request.method, request.path)
    return response
