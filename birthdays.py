"""Guild-wide birthday calendar cog."""

import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import birthdays_core
import birthdays_db
import i18n
import slash_registry

logger = logging.getLogger("birthdays")
MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")


class BirthdaysCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.announce_loop.start()

    def cog_unload(self):
        self.announce_loop.cancel()

    @app_commands.command(name="set-birthday", description="Set your birthday (MM-DD)")
    @app_commands.describe(date="Birthday as MM-DD, e.g. 07-23")
    async def set_birthday_command(self, interaction: discord.Interaction, date: str):
        lang = i18n.lang_for(interaction.guild_id)
        date = date.strip()
        if not birthdays_db.is_valid_mm_dd(date):
            return await interaction.response.send_message(
                i18n.t("birthdays.error.invalid_date", lang), ephemeral=True
            )
        birthdays_db.set_birthday(interaction.guild.id, interaction.user.id, date)
        await interaction.response.send_message(
            i18n.t("birthdays.set_ok", lang, date=date), ephemeral=True
        )

    @tasks.loop(minutes=5)
    async def announce_loop(self):
        try:
            today = datetime.now(MOSCOW_TZ)
            date_iso = today.strftime("%Y-%m-%d")
            mm_dd = today.strftime("%m-%d")
            for guild in self.bot.guilds:
                settings = birthdays_core.get_settings(guild.id)
                if not settings["enabled"] or not settings["channel_id"]:
                    continue
                if settings["last_announced_date"] == date_iso:
                    continue
                rows = birthdays_db.for_date(guild.id, mm_dd)
                if not rows:
                    birthdays_core.mark_announced(guild.id, date_iso)
                    continue
                channel = guild.get_channel(int(settings["channel_id"]))
                if not isinstance(channel, discord.TextChannel):
                    continue
                lang = i18n.lang_for(guild.id)
                mentions = []
                for row in rows:
                    member = guild.get_member(row["user_id"])
                    if member:
                        mentions.append(member.mention)
                if not mentions:
                    birthdays_core.mark_announced(guild.id, date_iso)
                    continue
                ping = ""
                if settings["ping_role_id"]:
                    ping = f"<@&{settings['ping_role_id']}> "
                text = ping + i18n.t(
                    "birthdays.announce",
                    lang,
                    members=", ".join(mentions),
                )
                try:
                    await channel.send(text)
                    birthdays_core.mark_announced(guild.id, date_iso)
                except discord.HTTPException:
                    logger.warning("birthday announce failed guild=%s", guild.id)
        except Exception:
            logger.exception("birthday announce_loop error")

    @announce_loop.before_loop
    async def before_announce(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    birthdays_db.init()
    cog = BirthdaysCog(bot)
    slash_registry.register_birthdays(cog)
    await bot.add_cog(cog)
