"""Дни рождения участников: хранение дат, live-список по месяцам, ежедневная рассылка.

Портировано из FamQ birthdays.py. Рассылка триггерится в 00:00 по MSK,
как в оригинале (ручная проверка часа/минуты вместо discord.ext.tasks time=,
чтобы не зависеть от таймзоны хоста).
"""

import logging
from datetime import datetime, timezone, timedelta

import discord
from discord import app_commands
from discord.ext import commands, tasks

import family_core
import family_db
import i18n
import slash_registry

logger = logging.getLogger("family.birthdays")

MOSCOW_TZ = timezone(timedelta(hours=3), name="MSK")


def build_birthday_embed(member: discord.abc.User, lang: str) -> discord.Embed:
    now_msk = datetime.now(MOSCOW_TZ)
    embed = discord.Embed(
        title=i18n.t("family.birthdays.embed.title", lang),
        description=i18n.t("family.birthdays.embed.description", lang, mention=member.mention),
        color=0xFEE75C,
        timestamp=datetime.now(timezone.utc),
    )
    embed.set_footer(text=i18n.t("family.birthdays.embed.footer", lang, date=now_msk.strftime('%d.%m.%Y')))
    return embed


async def send_birthday_log(bot: commands.Bot, guild_id: int, text: str):
    log_channel_id = family_core.get_settings(guild_id)["applications"]["log_channel_id"]
    if not log_channel_id:
        return
    channel = bot.get_channel(int(log_channel_id))
    if isinstance(channel, discord.TextChannel):
        try:
            await channel.send(text, allowed_mentions=discord.AllowedMentions.none())
        except discord.HTTPException:
            pass


class BirthdayCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_announcement_date: str | None = None
        self._recovered = False
        self.birthday_loop.start()

    def cog_unload(self):
        self.birthday_loop.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        for guild in self.bot.guilds:
            await self.update_birthday_message(guild)

    async def update_birthday_message(self, guild: discord.Guild):
        lang = i18n.lang_for(guild.id)
        settings = family_core.get_settings(guild.id)
        list_channel_id = settings["birthdays"]["list_channel_id"]
        if not list_channel_id:
            return
        channel = guild.get_channel(int(list_channel_id))
        if not isinstance(channel, discord.TextChannel):
            return

        all_rows = family_db.get_all_birthdays(guild.id)
        valid_rows = []
        for row in all_rows:
            user_id = row["user_id"]
            member = guild.get_member(user_id)
            if not member:
                try:
                    member = await guild.fetch_member(user_id)
                except discord.NotFound:
                    family_db.delete_birthday(guild.id, user_id)
                    continue
                except discord.HTTPException:
                    pass
            if member:
                valid_rows.append(row)

        content = family_core.build_birthday_text(valid_rows, guild, lang)
        data = family_db.get_birthday_message_data(guild.id)

        if data:
            old_channel = guild.get_channel(data["channel_id"])
            if isinstance(old_channel, discord.TextChannel):
                try:
                    message = await old_channel.fetch_message(data["message_id"])
                    await message.edit(content=content, allowed_mentions=discord.AllowedMentions.none())
                    return
                except discord.NotFound:
                    family_db.clear_birthday_message_data(guild.id)
                except discord.HTTPException:
                    return

        message = await channel.send(content=content, allowed_mentions=discord.AllowedMentions.none())
        family_db.save_birthday_message_data(guild.id, message.channel.id, message.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if not family_core.get_settings(member.guild.id)["enabled"]:
            return
        lang = i18n.lang_for(member.guild.id)
        deleted = family_db.delete_birthday(member.guild.id, member.id)
        if deleted:
            await self.update_birthday_message(member.guild)
            await send_birthday_log(
                self.bot, member.guild.id,
                i18n.t("family.birthdays.log.member_left", lang, mention=member.mention, name=member.name),
            )

    async def send_today_birthdays(self, guild: discord.Guild):
        lang = i18n.lang_for(guild.id)
        settings = family_core.get_settings(guild.id)
        channel_id = settings["birthdays"]["channel_id"]
        if not channel_id:
            return

        now_msk = datetime.now(MOSCOW_TZ)
        rows = family_db.get_birthdays_for_date(guild.id, now_msk.day, now_msk.month)
        if not rows:
            return

        channel = guild.get_channel(int(channel_id))
        if not isinstance(channel, discord.TextChannel):
            return

        notify_role_id = settings["applications"]["notify_role_id"]
        content = f"<@&{notify_role_id}>" if notify_role_id else None

        for row in rows:
            member = guild.get_member(row["user_id"])
            if not member:
                try:
                    member = await guild.fetch_member(row["user_id"])
                except discord.HTTPException:
                    continue

            await channel.send(content=content, embed=build_birthday_embed(member, lang))
            await send_birthday_log(self.bot, guild.id, i18n.t("family.birthdays.log.sent", lang, mention=member.mention))

    @tasks.loop(minutes=1)
    async def birthday_loop(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            now_msk = datetime.now(MOSCOW_TZ)
            today = now_msk.strftime("%Y-%m-%d")
            if now_msk.hour != 0 or now_msk.minute != 0 or self.last_announcement_date == today:
                return

            for guild in self.bot.guilds:
                if not family_core.get_settings(guild.id)["enabled"]:
                    continue
                try:
                    await self.send_today_birthdays(guild)
                except Exception:
                    logger.exception("send_today_birthdays failed for guild %s", guild.id)
            self.last_announcement_date = today
        except Exception:
            logger.exception("birthday_loop: ошибка итерации — цикл продолжает работать")

    @birthday_loop.error
    async def birthday_loop_error(self, _error: BaseException):
        logger.exception("birthday_loop: критическая ошибка — перезапуск цикла")
        self.birthday_loop.restart()

    @birthday_loop.before_loop
    async def before_birthday_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="добавить-др", description="Добавить свой день рождения")
    @app_commands.describe(дата="Дата рождения (дд.мм, дд.мм.гггг или «1 января»)")
    async def add_birthday(self, interaction: discord.Interaction, дата: str):
        lang = i18n.lang_for(interaction.guild_id)
        if not interaction.guild:
            return await interaction.response.send_message(i18n.t("family.guild_only", lang), ephemeral=True)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)

        try:
            day, month, display = family_core.parse_birthday_date(дата, lang)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        family_db.save_birthday(interaction.user.id, interaction.guild.id, day, month, display)
        await self.update_birthday_message(interaction.guild)
        await send_birthday_log(
            self.bot, interaction.guild.id,
            i18n.t("family.birthdays.log.added", lang, mention=interaction.user.mention, date=display),
        )
        await interaction.followup.send(i18n.t("family.birthdays.added", lang))

    @app_commands.command(name="установить-др", description="Установить день рождения участнику")
    @app_commands.describe(участник="Участник", дата="Дата рождения")
    async def set_birthday(self, interaction: discord.Interaction, участник: discord.Member, дата: str):
        lang = i18n.lang_for(interaction.guild_id)
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(i18n.t("family.guild_only", lang), ephemeral=True)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)
        if not family_core.has_staff_access(interaction.user):
            return await interaction.response.send_message(i18n.t("family.no_access", lang), ephemeral=True)

        try:
            day, month, display = family_core.parse_birthday_date(дата, lang)
        except ValueError as exc:
            return await interaction.response.send_message(str(exc), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        family_db.save_birthday(участник.id, interaction.guild.id, day, month, display)
        await self.update_birthday_message(interaction.guild)
        await send_birthday_log(
            self.bot, interaction.guild.id,
            i18n.t(
                "family.birthdays.log.set", lang,
                mention=interaction.user.mention, date=display, target=участник.mention,
            ),
        )
        await interaction.followup.send(i18n.t("family.birthdays.set", lang))

    @app_commands.command(name="удалить-др", description="Удалить день рождения")
    @app_commands.describe(участник="Участник (по умолчанию — вы сами)")
    async def delete_birthday(self, interaction: discord.Interaction, участник: discord.Member | None = None):
        lang = i18n.lang_for(interaction.guild_id)
        if not interaction.guild or not isinstance(interaction.user, discord.Member):
            return await interaction.response.send_message(i18n.t("family.guild_only", lang), ephemeral=True)
        if not family_core.get_settings(interaction.guild.id)["enabled"]:
            return await interaction.response.send_message(i18n.module_disabled(lang, "family"), ephemeral=True)

        target = участник or interaction.user
        if target.id != interaction.user.id and not family_core.has_staff_access(interaction.user):
            return await interaction.response.send_message(i18n.t("family.no_access", lang), ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        deleted = family_db.delete_birthday(interaction.guild.id, target.id)
        await self.update_birthday_message(interaction.guild)
        if deleted:
            await send_birthday_log(
                self.bot, interaction.guild.id,
                i18n.t(
                    "family.birthdays.log.deleted", lang,
                    mention=interaction.user.mention, target=target.mention,
                ),
            )
            await interaction.followup.send(i18n.t("family.birthdays.deleted", lang))
        else:
            await interaction.followup.send(i18n.t("family.birthdays.not_found", lang))


async def setup(bot: commands.Bot):
    family_db.init()
    cog = BirthdayCog(bot)
    slash_registry.register_family_birthdays(cog)
    await bot.add_cog(cog)
