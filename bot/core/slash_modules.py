"""Map slash root commands → modules; per-guild sync (optional hide when modules off)."""

from __future__ import annotations

import asyncio
import logging
import os
from typing import TYPE_CHECKING

import discord

logger = logging.getLogger("chetbot.slash_modules")

if TYPE_CHECKING:
    from discord.ext import commands

# settings_db module name → English root slash name(s).
# Roots not listed here are always synced (help, moderation, …).
MODULE_ROOT_COMMANDS: dict[str, tuple[str, ...]] = {
    "xp": ("levels",),
    "economy": (
        "daily",
        "balance",
        "grant-balance",
        "transfer",
        "coins-top",
        "shop",
        "cosmetics",
        "economy-weekly",
    ),
    "casino": ("casino",),
    "relations": ("relations",),
    "valchecker": ("val",),
    "fun": ("russian-roulette",),
    "wordle": ("wordle",),
    "mafia": ("mafia-start", "mafia-stop"),
    "bunker": ("bunker-start", "bunker-stop"),
    "family": ("family-applications", "roster", "birthday"),
    "birthdays": ("set-birthday",),
    "automod": ("warn",),
    "verification": ("verify_setup",),
}

# Modules whose settings.put should trigger a guild slash resync (only when hiding).
SYNC_ON_MODULE_PUT: frozenset[str] = frozenset(MODULE_ROOT_COMMANDS.keys())

_bot: commands.Bot | None = None
_resync_tasks: dict[int, asyncio.Task] = {}
_RESYNC_DELAY_SEC = 1.5


def bind_bot(bot: commands.Bot) -> None:
    global _bot
    _bot = bot


def hide_disabled_module_commands() -> bool:
    """When True, guild sync omits slash roots for disabled modules.

    Default is False: always sync the full tree so commands like /levels stay
    visible; runtime still refuses when the module is off. Opt in with
    COMMAND_SYNC_HIDE_DISABLED=1.
    """
    return os.getenv("COMMAND_SYNC_HIDE_DISABLED", "").strip().lower() in ("1", "true", "yes")


def _settings_enabled(module: str, guild_id: int) -> bool:
    """True = keep slash roots. Unconfigured modules stay visible."""
    try:
        import bot.core.settings_db as settings_db

        if not settings_db.has(guild_id, module):
            return True

        if module == "xp":
            import bot.modules.levels.xp_core as core
        elif module == "economy":
            import bot.modules.games.economy_core as core
        elif module == "casino":
            import bot.modules.games.casino_core as core
        elif module == "relations":
            import bot.modules.games.relations_core as core
        elif module == "valchecker":
            import bot.modules.valorant.valchecker_core as core
        elif module == "fun":
            import bot.modules.games.fun_core as core
        elif module == "wordle":
            import bot.modules.games.wordle_core as core
        elif module == "mafia":
            import bot.modules.games.mafia_core as core
        elif module == "bunker":
            import bot.modules.games.bunker_core as core
        elif module == "family":
            import bot.modules.games.family_core as core
        elif module == "birthdays":
            import bot.modules.community.birthdays_core as core
        elif module == "automod":
            import bot.modules.moderation.automod_core as core
        elif module == "verification":
            import bot.modules.moderation.verification_core as core
        else:
            return True
        return bool(core.get_settings(guild_id).get("enabled", True))
    except Exception:
        logger.exception("slash_modules: enabled check failed module=%s", module)
        return True


def allowed_root_names(guild_id: int) -> set[str] | None:
    """Unused helper kept for clarity — prefer disabled_root_names()."""
    disabled = disabled_root_names(guild_id)
    return None if not disabled else disabled


def disabled_root_names(guild_id: int) -> set[str]:
    out: set[str] = set()
    for module, roots in MODULE_ROOT_COMMANDS.items():
        if not _settings_enabled(module, guild_id):
            out.update(roots)
    return out


async def sync_guild_commands(bot: commands.Bot, guild: discord.Guild | discord.Object) -> None:
    """Copy global commands to guild and sync. Optionally drop disabled-module roots."""
    guild_id = guild.id if isinstance(guild, discord.Guild) else int(guild.id)
    target = discord.Object(id=guild_id)

    bot.tree.clear_commands(guild=target)
    bot.tree.copy_global_to(guild=target)

    disabled: set[str] = set()
    if hide_disabled_module_commands():
        disabled = disabled_root_names(guild_id)
        if disabled:
            for cmd in list(bot.tree.get_commands(guild=target)):
                if cmd.name in disabled:
                    bot.tree.remove_command(cmd.name, guild=target)

    synced = await bot.tree.sync(guild=target)
    names = sorted(c.name for c in synced)
    logger.info(
        "slash sync guild=%s roots=%d names=%s removed=%s",
        guild_id,
        len(names),
        names,
        sorted(disabled) if disabled else [],
    )
    if "levels" not in names:
        logger.warning("slash sync guild=%s missing root /levels", guild_id)


def on_settings_put(guild_id: int, module: str, data: dict) -> None:
    """Called from settings_db.put — debounce resync when hide-disabled is on."""
    if not hide_disabled_module_commands():
        return
    if module not in SYNC_ON_MODULE_PUT:
        return
    if _bot is None:
        return
    if "enabled" not in data:
        return
    schedule_guild_resync(guild_id)


def schedule_guild_resync(guild_id: int) -> None:
    bot = _bot
    if bot is None:
        return
    loop = getattr(bot, "loop", None)
    if loop is None or not loop.is_running():
        return

    prev = _resync_tasks.get(guild_id)
    if prev is not None and not prev.done():
        prev.cancel()

    async def _run() -> None:
        try:
            await asyncio.sleep(_RESYNC_DELAY_SEC)
            guild = bot.get_guild(guild_id)
            target = guild or discord.Object(id=guild_id)
            await sync_guild_commands(bot, target)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("slash resync failed guild=%s", guild_id)
        finally:
            _resync_tasks.pop(guild_id, None)

    _resync_tasks[guild_id] = loop.create_task(_run())
