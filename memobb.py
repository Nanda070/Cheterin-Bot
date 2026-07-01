import discord
from discord.ext import commands
from discord import app_commands
import os
import logging

logger = logging.getLogger("chetbot.memobb")


class CTDCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть Тикет", style=discord.ButtonStyle.danger, custom_id="ctd_close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        raw_role_id = os.getenv("CTD_ROLE_ID")
        if not raw_role_id:
            await interaction.response.send_message("CTD_ROLE_ID не задан в переменных окружения.", ephemeral=True)
            return
        role_id = int(raw_role_id)
        role = interaction.guild.get_role(role_id)
        if role not in interaction.user.roles:
            await interaction.response.send_message("У вас нет прав для закрытия тикета.", ephemeral=True)
            return

        await interaction.response.defer()
        thread = interaction.channel
        new_name = thread.name.replace("new-ticket-", "closed-ticket-", 1)
        await thread.edit(name=new_name, archived=True, locked=True)

        embed = discord.Embed(
            title="🔒 Тикет закрыт",
            description=f"Ветка: {thread.name}\nЗакрыл: {interaction.user.mention}",
            color=discord.Color.red(),
            timestamp=interaction.client.utcnow()
        )
        await interaction.client.send_log(embed)


class CTDView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать Тикет", style=discord.ButtonStyle.primary, custom_id="ctd_create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        channel = interaction.channel
        raw_role_id = os.getenv("CTD_ROLE_ID")
        if not raw_role_id:
            await interaction.followup.send("CTD_ROLE_ID не задан в переменных окружения.", ephemeral=True)
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
                    f"❌ У вас уже есть открытый тикет: <#{thread.id}>", ephemeral=True
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
            content=f"{interaction.user.mention} Пожалуйста, опишите ваше обращение и ожидайте ответа администрации.",
            view=CTDCloseView()
        )
        await msg.pin()

        await interaction.followup.send("Тикет успешно создан.", ephemeral=True)

        embed = discord.Embed(
            title="🎫 Создан новый тикет",
            description=f"Ветка: <#{thread.id}>\nПользователь: {interaction.user.mention}",
            color=discord.Color.green(),
            timestamp=interaction.client.utcnow()
        )
        await interaction.client.send_log(embed)


class CTD(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._auto_close_tickets.start()

    def cog_unload(self):
        self._auto_close_tickets.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_ctd_views_loaded", False):
            self.bot.add_view(CTDView())
            self.bot.add_view(CTDCloseView())
            self.bot._ctd_views_loaded = True

    from discord.ext import tasks
    @tasks.loop(hours=6)
    async def _auto_close_tickets(self):
        guild_id_raw = os.getenv("GUILD_ID")
        if not guild_id_raw: return
        guild = self.bot.get_guild(int(guild_id_raw))
        if not guild: return
        
        try:
            threads = await guild.active_threads()
        except Exception as e:
            logger.error("Auto-close error fetching threads: %s", e)
            return

        for thread in threads:
            if thread.name.startswith("new-ticket-"):
                if thread.last_message_id:
                    try:
                        msg = await thread.fetch_message(thread.last_message_id)
                        diff = discord.utils.utcnow() - msg.created_at
                        if diff.total_seconds() > 48 * 3600 and msg.author != self.bot.user:
                            await thread.send("⏳ Тикет неактивен более 48 часов и будет автоматически закрыт через 24 часа.")
                        elif diff.total_seconds() > 24 * 3600 and msg.author == self.bot.user and "неактивен" in msg.content:
                            new_name = thread.name.replace("new-ticket-", "closed-ticket-", 1)
                            await thread.edit(name=new_name, archived=True, locked=True)
                            await thread.send("🔒 Тикет автоматически закрыт по неактивности.")
                    except discord.NotFound:
                        pass
                    except Exception as e:
                        logger.warning("Error processing thread %s for auto-close: %s", thread.id, e)

    @_auto_close_tickets.before_loop
    async def _before_auto_close(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="ctd_setup", description="Установить панель тикетов CTD")
    @app_commands.default_permissions(manage_guild=True)
    async def ctd_setup(self, interaction: discord.Interaction):
        raw_channel_id = os.getenv("CTD_CHANNEL_ID")
        if not raw_channel_id:
            await interaction.response.send_message("CTD_CHANNEL_ID не задан в переменных окружения.", ephemeral=True)
            return
        channel_id = int(raw_channel_id)
        if interaction.channel_id != channel_id:
            await interaction.response.send_message(f"Команду нужно использовать в канале <#{channel_id}>", ephemeral=True)
            return

        view = CTDView()
        content = (
            "**Используйте форму обратной связи, чтобы сообщить о проблеме, предложить улучшение или получить помощь.**\n"
            "> Нажмите кнопку ниже, чтобы создать обращение. После нажатия автоматически откроется отдельная ветка, где можно подробно описать ситуацию."
        )
        # Сначала отвечаем на interaction, потом отправляем панель
        await interaction.response.send_message("Панель установлена.", ephemeral=True)
        await interaction.channel.send(content=content, view=view)


async def setup(bot):
    await bot.add_cog(CTD(bot))
