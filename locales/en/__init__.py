from locales._merge import merge_messages
from locales.en.antiraid import MESSAGES as antiraid_messages
from locales.en.automod import MESSAGES as automod_messages
from locales.en.brackets import MESSAGES as brackets_messages
from locales.en.bunker import MESSAGES as bunker_messages
from locales.en.button import MESSAGES as button_messages
from locales.en.casino import MESSAGES as casino_messages
from locales.en.common import MESSAGES as common_messages
from locales.en.ctd import MESSAGES as ctd_messages
from locales.en.daily_topic import MESSAGES as daily_topic_messages
from locales.en.economy import MESSAGES as economy_messages
from locales.en.events import MESSAGES as events_messages
from locales.en.family import MESSAGES as family_messages
from locales.en.feedback import MESSAGES as feedback_messages
from locales.en.fun import MESSAGES as fun_messages
from locales.en.giveaways import MESSAGES as giveaways_messages
from locales.en.lockdown import MESSAGES as lockdown_messages
from locales.en.mafia import MESSAGES as mafia_messages
from locales.en.moderation import MESSAGES as moderation_messages
from locales.en.news import MESSAGES as news_messages
from locales.en.reaction_roles import MESSAGES as reaction_roles_messages
from locales.en.serverlog import MESSAGES as serverlog_messages
from locales.en.slash import MESSAGES as slash_messages
from locales.en.spam import MESSAGES as spam_messages
from locales.en.streams import MESSAGES as streams_messages
from locales.en.supply import MESSAGES as supply_messages
from locales.en.tempban import MESSAGES as tempban_messages
from locales.en.verification import MESSAGES as verification_messages
from locales.en.voice_rooms import MESSAGES as voice_rooms_messages
from locales.en.welcome import MESSAGES as welcome_messages
from locales.en.wordle import MESSAGES as wordle_messages
from locales.en.xp import MESSAGES as xp_messages

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
    daily_topic_messages,
    streams_messages,
    feedback_messages,
    button_messages,
    ctd_messages,
    news_messages,
    brackets_messages,
    reaction_roles_messages,
    events_messages,
    supply_messages,
    giveaways_messages,
    voice_rooms_messages,
    family_messages,
    slash_messages,
)
