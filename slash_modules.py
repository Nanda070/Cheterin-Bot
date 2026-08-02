"""Map slash root commands → modules; per-guild filtered sync when modules toggle."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

import discord

logger = logging.getLogger("chetbot.slash_modules")

if TYPE_CHECKING:
    from discord.ext import commands

# settings_db module name → English root slash name(s) to include when enabled.
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

# Modules whose settings.put should trigger a guild slash resync.
SYNC_ON_MODULE_PUT: frozenset[str] = frozenset(MODULE_ROOT_COMMANDS.keys())

_bot: commands.Bot | None = None
_resync_tasks: dict[int, asyncio.Task] = {}
_RESYNC_DELAY_SEC = 1.5


def bind_bot(bot: commands.Bot) -> None:
    global _bot
    _bot = bot


def _settings_enabled(module: str, guild_id: int) -> bool:
    """True = keep slash roots. Unconfigured modules stay visible."""
    try:
        import settings_db

        if not settings_db.has(guild_id, module):
            return True

        if module == "xp":
            import xp_core as core
        elif module == "economy":
            import economy_core as core
        elif module == "casino":
            import casino_core as core
        elif module == "relations":
            import relations_core as core
        elif module == "valchecker":
            import valchecker_core as core
        elif module == "fun":
            import fun_core as core
        elif module == "wordle":
            import wordle_core as core
        elif module == "mafia":
            import mafia_core as core
        elif module == "bunker":
            import bunker_core as core
        elif module == "family":
            import family_core as core
        elif module == "birthdays":
            import birthdays_core as core
        elif module == "automod":
            import automod_core as core
        elif module == "verification":
            import verification_core as core
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
    """Copy global commands to guild, drop disabled-module roots, sync."""
    guild_id = guild.id if isinstance(guild, discord.Guild) else int(guild.id)
    target = discord.Object(id=guild_id)

    bot.tree.clear_commands(guild=target)
    bot.tree.copy_global_to(guild=target)

    disabled = disabled_root_names(guild_id)
    if disabled:
        for cmd in list(bot.tree.get_commands(guild=target)):
            if cmd.name in disabled:
                bot.tree.remove_command(cmd.name, guild=target)

    await bot.tree.sync(guild=target)
    logger.info(
        "slash sync guild=%s removed=%s",
        guild_id,
        sorted(disabled) if disabled else [],
    )


def on_settings_put(guild_id: int, module: str, data: dict) -> None:
    """Called from settings_db.put — debounce resync when module enabled flag matters."""
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
