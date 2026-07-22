import discord
from discord.ext import commands
from discord import app_commands
import os
import logging

import bot_config
import i18n
import slash_registry

logger = logging.getLogger("chetbot.memobb")

# CTD — привилегия основного сервера (Фаза 2b): ког активен только на мейне.
# Разрешение id мейна единообразно с main.get_main_guild_id().
MAIN_GUILD_ID = int(os.getenv("GUILD_ID") or os.getenv("MAIN_GUILD_ID") or "1324239354154975252")


def _is_main_guild(interaction: discord.Interaction) -> bool:
    return interaction.guild is not None and interaction.guild.id == MAIN_GUILD_ID


class CTDCloseView(discord.ui.View):
    def __init__(self, lang: str | None = None):
        super().__init__(timeout=None)
        self.lang = lang or i18n.lang_for(MAIN_GUILD_ID)
        button = discord.ui.Button(
            label=i18n.t("ctd.btn_close", self.lang),
            style=discord.ButtonStyle.danger,
            custom_id="ctd_close_ticket",
        )
        button.callback = self.close_ticket
        self.add_item(button)

    async def close_ticket(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        if not _is_main_guild(interaction):
            await interaction.response.send_message(i18n.t("ctd.main_guild_only", lang), ephemeral=True)
            return
        raw_role_id = bot_config.get(interaction.guild.id, "CTD_ROLE_ID")
        if not raw_role_id:
            await interaction.response.send_message(i18n.t("ctd.role_id_missing", lang), ephemeral=True)
            return
        role_id = int(raw_role_id)
        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles:
            await interaction.response.send_message(i18n.t("ctd.no_close_permission", lang), ephemeral=True)
            return

        await interaction.response.defer()
        thread = interaction.channel
        new_name = thread.name.replace("new-ticket-", "closed-ticket-", 1)
        await thread.edit(name=new_name, archived=True, locked=True)

        embed = discord.Embed(
            title=i18n.t("ctd.ticket_closed_title", lang),
            description=i18n.t(
                "ctd.ticket_closed_body",
                lang,
                thread_name=thread.name,
                mention=interaction.user.mention,
            ),
            color=discord.Color.red(),
            timestamp=interaction.client.utcnow(),
        )
        await interaction.client.send_log(interaction.guild.id, embed)


class CTDView(discord.ui.View):
    def __init__(self, lang: str | None = None):
        super().__init__(timeout=None)
        self.lang = lang or i18n.lang_for(MAIN_GUILD_ID)
        button = discord.ui.Button(
            label=i18n.t("ctd.btn_create", self.lang),
            style=discord.ButtonStyle.primary,
            custom_id="ctd_create_ticket",
        )
        button.callback = self.create_ticket
        self.add_item(button)

    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        if not _is_main_guild(interaction):
            await interaction.response.send_message(i18n.t("ctd.main_guild_only", lang), ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        raw_role_id = bot_config.get(interaction.guild.id, "CTD_ROLE_ID")
        if not raw_role_id:
            await interaction.followup.send(i18n.t("ctd.role_id_missing", lang), ephemeral=True)
            return
        role_id = int(raw_role_id)

        # Проверка на существующий открытый тикет
        try:
            active_threads = await interaction.guild.active_threads()
        except Exception as e:
            logger.warning("Ошибка получения активных тредов: %s", e)
            active_threads = []

        for thread in active_threads:
            if thread.parent_id == channel.id and thread.name.startswith("new-ticket-") and thread.name.endswith(f"-{interaction.user.id}"):
                await interaction.followup.send(
                    i18n.t("ctd.open_ticket_exists", lang, thread_id=thread.id),
                    ephemeral=True,
                )
                return

        thread_name = f"new-ticket-{interaction.user.name}-{interaction.user.id}"
        thread = await channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        await thread.add_user(interaction.user)
        role = interaction.guild.get_role(role_id)
        if role:
            for member in role.members:
                if not member.bot:
                    try:
                        await thread.add_user(member)
                    except Exception:
                        pass

        msg = await thread.send(
            content=i18n.t("ctd.ticket_prompt", lang, mention=interaction.user.mention),
            view=CTDCloseView(lang),
        )
        await msg.pin()

        await interaction.followup.send(i18n.t("ctd.ticket_created_user", lang), ephemeral=True)

        embed = discord.Embed(
            title=i18n.t("ctd.ticket_created_log", lang),
            description=i18n.t(
                "ctd.ticket_created_log_body",
                lang,
                thread_id=thread.id,
                mention=interaction.user.mention,
            ),
            color=discord.Color.green(),
            timestamp=interaction.client.utcnow(),
        )
        await interaction.client.send_log(interaction.guild.id, embed)


class CTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._auto_close_tickets.start()

    def cog_unload(self):
        self._auto_close_tickets.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_ctd_views_loaded", False):
            lang = i18n.lang_for(MAIN_GUILD_ID)
            self.bot.add_view(CTDView(lang))
            self.bot.add_view(CTDCloseView(lang))
            self.bot._ctd_views_loaded = True

    from discord.ext import tasks
    @tasks.loop(hours=6)
    async def _auto_close_tickets(self):
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            guild = self.bot.get_guild(MAIN_GUILD_ID)
            if not guild: return
            lang = i18n.lang_for(MAIN_GUILD_ID)

            try:
                threads = await guild.active_threads()
            except Exception as e:
                logger.error("Auto-close error fetching threads: %s", e)
                return

            inactive_marker = i18n.t("ctd.inactive_warning", lang)[:20]
            for thread in threads:
                if thread.name.startswith("new-ticket-"):
                    if thread.last_message_id:
                        try:
                            msg = await thread.fetch_message(thread.last_message_id)
                            diff = discord.utils.utcnow() - msg.created_at
                            if diff.total_seconds() > 48 * 3600 and msg.author != self.bot.user:
                                await thread.send(i18n.t("ctd.inactive_warning", lang))
                            elif diff.total_seconds() > 24 * 3600 and msg.author == self.bot.user and inactive_marker in msg.content:
                                new_name = thread.name.replace("new-ticket-", "closed-ticket-", 1)
                                await thread.edit(name=new_name, archived=True, locked=True)
                                await thread.send(i18n.t("ctd.auto_closed", lang))
                        except discord.NotFound:
                            pass
                        except Exception as e:
                            logger.warning("Error processing thread %s for auto-close: %s", thread.id, e)
        except Exception:
            logger.exception("_auto_close_tickets: ошибка итерации — цикл продолжает работать")

    @_auto_close_tickets.error
    async def _auto_close_tickets_error(self, _error: BaseException):
        logger.exception("_auto_close_tickets: критическая ошибка — перезапуск цикла")
        self._auto_close_tickets.restart()

    @_auto_close_tickets.before_loop
    async def _before_auto_close(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="ctd_setup", description="Установить панель тикетов CTD")
    @app_commands.guilds(discord.Object(id=MAIN_GUILD_ID))
    @app_commands.default_permissions(manage_guild=True)
    async def ctd_setup(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        if not _is_main_guild(interaction):
            await interaction.response.send_message(i18n.t("ctd.main_guild_only", lang), ephemeral=True)
            return
        raw_channel_id = bot_config.get(interaction.guild.id, "CTD_CHANNEL_ID")
        if not raw_channel_id:
            await interaction.response.send_message(i18n.t("ctd.channel_id_missing", lang), ephemeral=True)
            return
        channel_id = int(raw_channel_id)
        if interaction.channel_id != channel_id:
            await interaction.response.send_message(
                i18n.t("ctd.wrong_channel", lang, channel_id=channel_id),
                ephemeral=True,
            )
            return

        view = CTDView(lang)
        content = i18n.t("ctd.panel_content", lang)
        # Сначала отвечаем на interaction, потом отправляем панель
        await interaction.response.send_message(i18n.t("ctd.panel_installed", lang), ephemeral=True)
        await interaction.channel.send(content=content, view=view)


async def setup(bot):
    cog = CTD(bot)
    slash_registry.register_ctd(cog)
    await bot.add_cog(cog)
