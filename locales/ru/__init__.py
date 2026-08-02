from locales._merge import merge_messages
from locales.ru.antiraid import MESSAGES as antiraid_messages
from locales.ru.automod import MESSAGES as automod_messages
from locales.ru.brackets import MESSAGES as brackets_messages
from locales.ru.bunker import MESSAGES as bunker_messages
from locales.ru.button import MESSAGES as button_messages
from locales.ru.casino import MESSAGES as casino_messages
from locales.ru.common import MESSAGES as common_messages
from locales.ru.ctd import MESSAGES as ctd_messages
from locales.ru.daily_topic import MESSAGES as daily_topic_messages
from locales.ru.economy import MESSAGES as economy_messages
from locales.ru.events import MESSAGES as events_messages
from locales.ru.family import MESSAGES as family_messages
from locales.ru.feedback import MESSAGES as feedback_messages
from locales.ru.fun import MESSAGES as fun_messages
from locales.ru.giveaways import MESSAGES as giveaways_messages
from locales.ru.help import MESSAGES as help_messages
from locales.ru.lockdown import MESSAGES as lockdown_messages
from locales.ru.mafia import MESSAGES as mafia_messages
from locales.ru.moderation import MESSAGES as moderation_messages
from locales.ru.news import MESSAGES as news_messages
from locales.ru.new_modules import MESSAGES as new_modules_messages
from locales.ru.reaction_roles import MESSAGES as reaction_roles_messages
from locales.ru.serverlog import MESSAGES as serverlog_messages
from locales.ru.slash import MESSAGES as slash_messages
from locales.ru.spam import MESSAGES as spam_messages
from locales.ru.streams import MESSAGES as streams_messages
from locales.ru.supply import MESSAGES as supply_messages
from locales.ru.quote import MESSAGES as quote_messages
from locales.ru.relations import MESSAGES as relations_messages
from locales.ru.valchecker import MESSAGES as valchecker_messages
from locales.ru.tempban import MESSAGES as tempban_messages
from locales.ru.verification import MESSAGES as verification_messages
from locales.ru.voice_rooms import MESSAGES as voice_rooms_messages
from locales.ru.welcome import MESSAGES as welcome_messages
from locales.ru.wordle import MESSAGES as wordle_messages
from locales.ru.xp import MESSAGES as xp_messages

MESSAGES = merge_messages(
    common_messages,
    verification_messages,
    welcome_messages,
    fun_messages,
    economy_messages,
    events_messages,
    casino_messages,
    xp_messages,
    wordle_messages,
    mafia_messages,
    bunker_messages,
    moderation_messages,
    serverlog_messages,
    automod_messages,
    lockdown_messages,
    antiraid_messages,
    spam_messages,
    tempban_messages,
    quote_messages,
    relations_messages,
    valchecker_messages,
    daily_topic_messages,
    streams_messages,
    feedback_messages,
    button_messages,
    ctd_messages,
    news_messages,
    new_modules_messages,
    brackets_messages,
    reaction_roles_messages,
    events_messages,
    supply_messages,
    giveaways_messages,
    help_messages,
    voice_rooms_messages,
    family_messages,
    slash_messages,
)
