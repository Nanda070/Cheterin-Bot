"""Apply slash command localizations for every cog (Phase 3.2(3))."""

from __future__ import annotations

from typing import Any

import bot.core.slash_i18n as si

_c = si.localize_command
_g = si.localize_group

# Keys used by tests to verify locale coverage.
SLASH_KEYS: tuple[str, ...] = (
    "help",
    "levels_group",
    "rank",
    "profile",
    "xp",  # levels manage subcommand uses slash.xp keys
    "leaders",
    "wordle",
    "russian_roulette",
    "verify_setup",
    "ctd_setup",
    "family_applications",
    "roster",
    "birthday",
    "supply_run",
    "antispam",
    "bunker_start",
    "bunker_stop",
    "mafia_start",
    "mafia_stop",
    "ban",
    "kick",
    "mute",
    "unmute",
    "unban",
    "clear",
    "casino_group",
    "slots",
    "coinflip",
    "blackjack",
    "casino_top",
    "daily",
    "balance",
    "grant_balance",
    "transfer",
    "coins_top",
    "shop",
    "cosmetics",
    "economy_weekly",
    "timed_role",
    "birthday_set_self",
    "poll_create",
    "warn",
    "feedback_panel_group",
    "feedback_panel_send",
    "button_group",
    "button_form",
    "button_role",
    "giveaway",
    "event",
    "val_group",
    "val_setup",
    "val_profile",
    "val_match",
    "val_compare",
    "val_lb",
    "val_status",
    "relations_group",
    "relations_hug",
    "relations_kiss",
    "relations_slap",
    "relations_pat",
    "relations_highfive",
    "relations_cuddle",
    "relations_poke",
    "relations_card",
    "relations_top",
    "relations_marry",
    "relations_divorce",
    "relations_marriages_top",
    "relations_ship",
    "relations_date",
    "valorant_group",
    "valorant_agent",
    "valorant_buddy",
    "valorant_map",
    "valorant_skin",
    "valorant_weapon",
)


def _key(name: str) -> str:
    return f"slash.{name}"


def _cmd(command: Any, name: str) -> None:
    base = _key(name)
    _c(command, desc_key=f"{base}.desc", name_key=base)


def _grp(group: Any, name: str) -> None:
    base = _key(name)
    _g(group, desc_key=f"{base}.desc", name_key=base)


def register_help(cog) -> None:
    _cmd(cog.help_command, "help")


def register_xp(cog) -> None:
    _grp(cog.levels_group, "levels_group")
    _cmd(cog.rank_command, "rank")
    _cmd(cog.profile_command, "profile")
    _cmd(cog.xp_command, "xp")
    _cmd(cog.leaders_command, "leaders")


def register_wordle(cog) -> None:
    _cmd(cog.wordle_command, "wordle")


def register_fun(cog) -> None:
    _cmd(cog.russian_roulette, "russian_roulette")


def register_verification(cog) -> None:
    _cmd(cog.verify_setup, "verify_setup")


def register_ctd(cog) -> None:
    _cmd(cog.ctd_setup, "ctd_setup")


def register_family_tickets(cog) -> None:
    _cmd(cog.create_panel, "family_applications")


def register_family_roster(cog) -> None:
    _cmd(cog.roster_list, "roster")


def register_family_birthdays(cog) -> None:
    _cmd(cog.birthday_command, "birthday")


def register_supply(cog) -> None:
    _cmd(cog.supply_collect, "supply_run")


def register_lockdown(cog) -> None:
    _cmd(cog.antispam, "antispam")


def register_bunker(cog) -> None:
    _cmd(cog.start_lobby, "bunker_start")
    _cmd(cog.stop_game, "bunker_stop")


def register_mafia(cog) -> None:
    _cmd(cog.start_lobby, "mafia_start")
    _cmd(cog.stop_game, "mafia_stop")


def register_moderation(cog) -> None:
    _cmd(cog.ban_command, "ban")
    _cmd(cog.kick_command, "kick")
    _cmd(cog.mute_command, "mute")
    _cmd(cog.unmute_command, "unmute")
    _cmd(cog.unban_command, "unban")
    _cmd(cog.clear_command, "clear")


def register_blackjack(cog) -> None:
    # Blackjack is a subcommand of /casino — see register_casino.
    return


def register_casino(cog, casino_top_command=None) -> None:
    _grp(cog.casino_group, "casino_group")
    _cmd(cog.slots_command, "slots")
    _cmd(cog.coinflip_command, "coinflip")
    _cmd(cog.casino_blackjack, "blackjack")
    _cmd(cog.casino_top_command, "casino_top")


def register_economy(cog) -> None:
    _cmd(cog.daily_command, "daily")
    _cmd(cog.balance_command, "balance")
    _cmd(cog.grant_balance_command, "grant_balance")
    _cmd(cog.transfer_command, "transfer")
    _cmd(cog.top_command, "coins_top")
    _cmd(cog.shop_command, "shop")
    _cmd(cog.cosmetics_command, "cosmetics")
    _cmd(cog.weekly_command, "economy_weekly")


def register_timed_roles(cog) -> None:
    _cmd(cog.timed_role_command, "timed_role")


def register_birthdays(cog) -> None:
    _cmd(cog.set_birthday_command, "birthday_set_self")


def register_polls(cog) -> None:
    _cmd(cog.poll_command, "poll_create")


def register_automod(cog) -> None:
    _cmd(cog.warn_command, "warn")


def register_feedback(cog) -> None:
    _grp(cog.feedback_panel_group, "feedback_panel_group")
    _cmd(cog.feedback_panel_send, "feedback_panel_send")


def register_button(cog) -> None:
    _grp(cog.button_group, "button_group")
    _cmd(cog.button_create_form, "button_form")
    _cmd(cog.button_create_role, "button_role")


def register_giveaways(cog) -> None:
    _cmd(cog.giveaway_command, "giveaway")


def register_events(cog) -> None:
    _cmd(cog.event_command, "event")


def register_valchecker(cog) -> None:
    _grp(cog.val_group, "val_group")
    _cmd(cog.val_setup, "val_setup")
    _cmd(cog.val_profile, "val_profile")
    _cmd(cog.val_match, "val_match")
    _cmd(cog.val_compare, "val_compare")
    _cmd(cog.val_lb, "val_lb")
    _cmd(cog.val_status, "val_status")


def register_relations(cog) -> None:
    _grp(cog.relations_group, "relations_group")
    _cmd(cog.relations_hug, "relations_hug")
    _cmd(cog.relations_kiss, "relations_kiss")
    _cmd(cog.relations_slap, "relations_slap")
    _cmd(cog.relations_pat, "relations_pat")
    _cmd(cog.relations_highfive, "relations_highfive")
    _cmd(cog.relations_cuddle, "relations_cuddle")
    _cmd(cog.relations_poke, "relations_poke")
    _cmd(cog.relations_card, "relations_card")
    _cmd(cog.relations_top, "relations_top")
    _cmd(cog.relations_marry, "relations_marry")
    _cmd(cog.relations_divorce, "relations_divorce")
    _cmd(cog.relations_marriages_top, "relations_marriages_top")
    _cmd(cog.relations_ship, "relations_ship")
    _cmd(cog.relations_date, "relations_date")


def register_valorant_random(cog) -> None:
    _grp(cog.group, "valorant_group")
    _cmd(cog.agent, "valorant_agent")
    _cmd(cog.buddy, "valorant_buddy")
    _cmd(cog.map, "valorant_map")
    _cmd(cog.skin, "valorant_skin")
    _cmd(cog.weapon, "valorant_weapon")
