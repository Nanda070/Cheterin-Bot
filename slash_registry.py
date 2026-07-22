"""Apply slash command localizations for every cog (Phase 3.2(3))."""

from __future__ import annotations

from typing import Any

import slash_i18n as si

_c = si.localize_command
_g = si.localize_group

# Keys used by tests to verify locale coverage.
SLASH_KEYS: tuple[str, ...] = (
    "userinfo",
    "rank",
    "leaders",
    "xp_group",
    "xp_add",
    "xp_set",
    "xp_clear",
    "wordle",
    "wordle_training",
    "wordle_stats",
    "wordle_top",
    "russian_roulette",
    "emoji_roulette",
    "verify_setup",
    "ctd_setup",
    "family_applications",
    "roster",
    "birthday_add",
    "birthday_set",
    "birthday_remove",
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
    "blackjack",
    "slots",
    "coinflip",
    "casino_top",
    "daily",
    "balance",
    "grant_balance",
    "transfer",
    "coins_top",
    "shop",
    "cosmetics",
    "warn_group",
    "warn_add",
    "warn_list",
    "warn_remove",
    "feedback_panel_group",
    "feedback_panel_send",
    "button_group",
    "button_form",
    "button_role",
    "giveaway_group",
    "giveaway_start",
    "giveaway_reroll",
    "giveaway_end",
    "event_group",
    "event_setup",
    "event_manage",
)


def _key(name: str) -> str:
    return f"slash.{name}"


def _cmd(command: Any, name: str) -> None:
    base = _key(name)
    _c(command, desc_key=f"{base}.desc", name_key=base)


def _grp(group: Any, name: str) -> None:
    base = _key(name)
    _g(group, desc_key=f"{base}.desc", name_key=base)


def register_welcome(cog) -> None:
    _cmd(cog.userinfo, "userinfo")


def register_xp(cog) -> None:
    _grp(cog.xp_group, "xp_group")
    _cmd(cog.xp_add, "xp_add")
    _cmd(cog.xp_set, "xp_set")
    _cmd(cog.xp_clear, "xp_clear")
    _cmd(cog.rank_command, "rank")
    _cmd(cog.leaders_command, "leaders")


def register_wordle(cog) -> None:
    _cmd(cog.wordle_command, "wordle")
    _cmd(cog.training_command, "wordle_training")
    _cmd(cog.stats_command, "wordle_stats")
    _cmd(cog.top_command, "wordle_top")


def register_fun(cog) -> None:
    _cmd(cog.russian_roulette, "russian_roulette")
    _cmd(cog.emoji_roulette, "emoji_roulette")


def register_verification(cog) -> None:
    _cmd(cog.verify_setup, "verify_setup")


def register_ctd(cog) -> None:
    _cmd(cog.ctd_setup, "ctd_setup")


def register_family_tickets(cog) -> None:
    _cmd(cog.create_panel, "family_applications")


def register_family_roster(cog) -> None:
    _cmd(cog.roster_list, "roster")


def register_family_birthdays(cog) -> None:
    _cmd(cog.add_birthday, "birthday_add")
    _cmd(cog.set_birthday, "birthday_set")
    _cmd(cog.delete_birthday, "birthday_remove")


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
    _cmd(cog.blackjack_command, "blackjack")


def register_casino(cog, casino_top_command) -> None:
    _cmd(cog.slots_command, "slots")
    _cmd(cog.coinflip_command, "coinflip")
    _cmd(casino_top_command, "casino_top")


def register_economy(cog) -> None:
    _cmd(cog.daily_command, "daily")
    _cmd(cog.balance_command, "balance")
    _cmd(cog.grant_balance_command, "grant_balance")
    _cmd(cog.transfer_command, "transfer")
    _cmd(cog.top_command, "coins_top")
    _cmd(cog.shop_command, "shop")
    _cmd(cog.cosmetics_command, "cosmetics")


def register_automod(cog) -> None:
    _grp(cog.warn_group, "warn_group")
    _cmd(cog.warn_add, "warn_add")
    _cmd(cog.warn_list, "warn_list")
    _cmd(cog.warn_remove, "warn_remove")


def register_feedback(cog) -> None:
    _grp(cog.feedback_panel_group, "feedback_panel_group")
    _cmd(cog.feedback_panel_send, "feedback_panel_send")


def register_button(cog) -> None:
    _grp(cog.button_group, "button_group")
    _cmd(cog.button_create_form, "button_form")
    _cmd(cog.button_create_role, "button_role")


def register_giveaways(cog) -> None:
    _grp(cog.giveaway_group, "giveaway_group")
    _cmd(cog.giveaway_start, "giveaway_start")
    _cmd(cog.giveaway_reroll, "giveaway_reroll")
    _cmd(cog.giveaway_end, "giveaway_end")


def register_events(cog) -> None:
    _grp(cog.event_group, "event_group")
    _cmd(cog.event_setup, "event_setup")
    _cmd(cog.event_manage, "event_manage")
