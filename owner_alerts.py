"""Owner alerts: DM/channel notify on missing perms, mass bans, module errors,
plus an optional weekly settings/activity digest posted to the alerts channel."""

import logging

import discord
from discord.ext import commands, tasks

import embed_style
import i18n
import owner_alerts_core
import stats_db

logger = logging.getLogger("owner_alerts")


class OwnerAlertsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.perms_loop.start()
        self.weekly_digest_loop.start()

    def cog_unload(self):
        self.perms_loop.cancel()
        self.weekly_digest_loop.cancel()

    async def send_alert(self, guild: discord.Guild, kind: str, detail: str, *, force: bool = False) -> bool:
        """Send an owner alert. Returns True if at least one delivery succeeded."""
        settings = owner_alerts_core.get_settings(guild.id)
        if not force and not settings["enabled"]:
            return False
        lang = i18n.lang_for(guild.id)
        text = owner_alerts_core.format_alert(kind, detail, lang)
        delivered = False
        if settings["channel_id"]:
            channel = guild.get_channel(int(settings["channel_id"]))
            if isinstance(channel, discord.TextChannel):
                try:
                    await channel.send(text)
                    delivered = True
                except discord.HTTPException:
                    pass
        if settings["notify_dm"] and guild.owner:
            try:
                await guild.owner.send(f"**{guild.name}**\n{text}")
                delivered = True
            except discord.HTTPException:
                pass
        return delivered

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

    def build_weekly_digest_embed(self, guild: discord.Guild, days: int, lang: str) -> discord.Embed:
        import time as time_module

        since_ts = int(time_module.time()) - days * 86400
        rows = stats_db.audit_list_since(guild.id, since_ts)
        summary = owner_alerts_core.summarize_audit_actions([dict(row) for row in rows])
        embed = discord.Embed(
            title=i18n.t("owner_alerts.digest.title", lang, days=days),
            color=embed_style.INFO,
            timestamp=discord.utils.utcnow(),
        )
        if not summary:
            embed.description = i18n.t("owner_alerts.digest.empty", lang)
            return embed
        lines = [
            i18n.t("owner_alerts.digest.line", lang, label=row["label"], count=row["count"])
            for row in summary
        ]
        embed.description = "\n".join(lines)
        embed.set_footer(text=i18n.t("owner_alerts.digest.footer", lang, total=len(rows)))
        return embed

    async def post_weekly_digest(self, guild_id: int) -> bool:
        settings = owner_alerts_core.get_settings(guild_id)
        channel_id = owner_alerts_core.weekly_digest_channel_id(settings)
        if not channel_id:
            return False
        channel = self.bot.get_channel(int(channel_id))
        if channel is None:
            return False
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            return False
        lang = i18n.lang_for(guild_id)
        try:
            await channel.send(embed=self.build_weekly_digest_embed(guild, 7, lang))
        except discord.HTTPException:
            logger.warning("Failed to post weekly settings digest guild=%s", guild_id)
            return False

        import timezone_core

        week_key = timezone_core.now_local(guild_id).strftime("%G-W%V")
        owner_alerts_core.mark_weekly_digest_posted(guild_id, week_key)
        return True

    @tasks.loop(minutes=15)
    async def weekly_digest_loop(self):
        try:
            for guild in self.bot.guilds:
                try:
                    if owner_alerts_core.should_post_weekly_digest(guild.id):
                        await self.post_weekly_digest(guild.id)
                except Exception as exc:
                    logger.exception("weekly_digest_loop guild=%s", guild.id)
                    cog = self.bot.get_cog("OwnerAlertsCog")
                    if cog:
                        cog.report_module_error(guild.id, "owner_alerts", str(exc))
        except Exception:
            logger.exception("weekly_digest_loop error")

    @weekly_digest_loop.before_loop
    async def before_weekly_digest(self):
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
