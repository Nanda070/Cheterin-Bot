"""Owner alerts: DM/channel notify on missing perms, mass bans, module errors."""

import logging

import discord
from discord.ext import commands, tasks

import i18n
import owner_alerts_core

logger = logging.getLogger("owner_alerts")


class OwnerAlertsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.perms_loop.start()

    def cog_unload(self):
        self.perms_loop.cancel()

    async def send_alert(self, guild: discord.Guild, kind: str, detail: str) -> None:
        settings = owner_alerts_core.get_settings(guild.id)
        if not settings["enabled"]:
            return
        lang = i18n.lang_for(guild.id)
        text = owner_alerts_core.format_alert(kind, detail, lang)
        if settings["channel_id"]:
            channel = guild.get_channel(int(settings["channel_id"]))
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(text)
                except discord.HTTPException:
                    pass
        if settings["notify_dm"] and guild.owner:
            try:
                await guild.owner.send(f"**{guild.name}**\n{text}")
            except discord.HTTPException:
                pass

    @tasks.loop(minutes=30)
    async def perms_loop(self):
        try:
            for guild in self.bot.guilds:
                settings = owner_alerts_core.get_settings(guild.id)
                if not settings["enabled"] or not settings["alert_missing_perms"]:
                    continue
                me = guild.me
                if me is None:
                    continue
                missing = owner_alerts_core.critical_perms_missing(me.guild_permissions)
                if missing:
                    await self.send_alert(
                        guild,
                        "missing_perms",
                        ", ".join(missing),
                    )
        except Exception:
            logger.exception("owner_alerts perms_loop error")

    @perms_loop.before_loop
    async def before_perms(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, _user: discord.User | discord.Member):
        settings = owner_alerts_core.get_settings(guild.id)
        if owner_alerts_core.register_ban(guild.id, settings):
            await self.send_alert(
                guild,
                "mass_ban",
                i18n.t(
                    "owner_alerts.mass_ban_detail",
                    i18n.lang_for(guild.id),
                    threshold=settings["mass_ban_threshold"],
                    window=settings["mass_ban_window_sec"],
                ),
            )

    def report_module_error(self, guild_id: int, module: str, error: str) -> None:
        """Callable from other modules when they hit repeated failures."""
        settings = owner_alerts_core.get_settings(guild_id)
        if owner_alerts_core.register_module_error(guild_id, settings):
            guild = self.bot.get_guild(guild_id)
            if guild:
                self.bot.loop.create_task(
                    self.send_alert(guild, "module_error", f"{module}: {error}")
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(OwnerAlertsCog(bot))
