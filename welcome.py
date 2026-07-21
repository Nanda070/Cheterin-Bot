import settings_db
import discord
from discord.ext import commands
from discord import app_commands

import bot_config


class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cached_invites: dict[int, list[discord.Invite]] = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.bot.guilds:
            try:
                self.cached_invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                self.cached_invites[guild.id] = []

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        self.cached_invites.setdefault(invite.guild.id, []).append(invite)

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        self.cached_invites[invite.guild.id] = [
            item for item in self.cached_invites.get(invite.guild.id, []) if item.code != invite.code
        ]

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        try:
            new_invites = await guild.invites()
        except discord.Forbidden:
            new_invites = []

        old_invites = self.cached_invites.get(guild.id, [])
        used = None
        for new_inv in new_invites:
            for old_inv in old_invites:
                if new_inv.code == old_inv.code and new_inv.uses > old_inv.uses:
                    used = new_inv
                    break
            if used:
                break
        self.cached_invites[guild.id] = new_invites

        if bot_config.get(guild.id, "WELCOME_CHANNEL_ENABLED", True):
            welcome_ch_id = bot_config.get(guild.id, "WELCOME_CHANNEL_ID")
            if welcome_ch_id:
                welcome_ch = self.bot.get_channel(int(welcome_ch_id))
                if welcome_ch:
                    await welcome_ch.send(f"Приветствую тебя {member.mention} на сервере **{guild.name}**! Теперь нас {guild.member_count}!")

        auto_role_ids = bot_config.get(guild.id, "AUTO_ROLE_IDS", [])
        if auto_role_ids:
            roles_to_add = [guild.get_role(int(rid)) for rid in auto_role_ids]
            roles_to_add = [r for r in roles_to_add if r is not None]
            if roles_to_add:
                try:
                    await member.add_roles(*roles_to_add, reason="Авто-роль при входе")
                except discord.Forbidden:
                    pass

        if used and used.inviter:
            inviter_id = str(used.inviter.id)
            invites_data = settings_db.get(member.guild.id, "invites_stats", {})
            stats = invites_data.setdefault("stats", {})
            invite_history = invites_data.setdefault("invite_history", {})
            
            stats.setdefault(inviter_id, {"joins": 0, "leaves": 0, "invites": 0})
            stats[inviter_id]["joins"] += 1
            stats[inviter_id]["invites"] += 1
            invite_history[str(member.id)] = inviter_id
            
            settings_db.put(member.guild.id, "invites_stats", invites_data)

            embed_inv = discord.Embed(
                title="📥 Invite Log",
                description=(
                    f"{used.inviter.mention} пригласил {member.mention}\n"
                    f"Код: `{used.code}` | Всего приглашено: **{stats[inviter_id]['invites']}**"
                ),
                color=discord.Color.blurple(),
                timestamp=self.bot.utcnow(),
            )
            inv_ch_id = bot_config.get(guild.id, "INVITE_LOG_CHANNEL_ID")
            if inv_ch_id:
                inv_ch = self.bot.get_channel(int(inv_ch_id))
                if inv_ch:
                    await inv_ch.send(embed=embed_inv)

        dm_embed = discord.Embed(
            title=f"Добро пожаловать на {guild.name}",
            description="Рады видеть тебя в нашем пространстве! Ниже — краткое руководство по ключевым ресурсам:",
            color=discord.Color.dark_blue(),
            timestamp=self.bot.utcnow(),
        )
        dm_embed.set_thumbnail(url="https://i.imgur.com/4ydti00.png")

        dm_embed.add_field(name="〘❗〙 Объявления", value=f"<#{bot_config.get(guild.id, 'ANNOUNCEMENTS_CHANNEL_ID') or '0'}> — все важные новости и анонсы", inline=False)
        dm_embed.add_field(name="〘📜〙 Правила", value=f"<#{bot_config.get(guild.id, 'RULES_CHANNEL_ID') or '0'}> — ознакомься перед общением", inline=False)
        dm_embed.add_field(name="〘❗〙 Роли", value=f"<#{bot_config.get(guild.id, 'ROLES_CHANNEL_ID') or '0'}> — получи доступ к привилегиям", inline=False)
        dm_embed.add_field(name="〘🔎〙 Поиск игроков", value=f"<#{bot_config.get(guild.id, 'SEARCH_PLAYERS_CHANNEL_ID') or '0'}> — найдёшь тиммейтов под свои задачи", inline=False)
        dm_embed.add_field(name="📈 Система уровней", value=("Наращивай активность в голосовых чатах и зарабатывай опыт — твоя роль и цвет ника будут расти вместе с тобой."), inline=False)
        dm_embed.add_field(name="💡 Советы по вливанию", value=("1. Представься в чате.\n2. Загляни в раздел «Правила» и ставь реакцию ✔️.\n3. Выбери роли, которые тебе интересны.\n4. Не стесняйся задавать вопросы — мы тут все на «ты» :)"), inline=False)
        dm_embed.set_footer(text="Для помощи — обращайся к Администрации. По вопросам ботов — пиши Nanda070.")

        dm_sent = False
        if bot_config.get(guild.id, "WELCOME_DM_ENABLED", True):
            try:
                await member.send(embed=dm_embed)
                dm_sent = True
            except discord.Forbidden:
                dm_sent = False

        dm_log = discord.Embed(
            title="📩 DM Log",
            color=discord.Color.green() if dm_sent else discord.Color.red(),
            timestamp=self.bot.utcnow(),
        )
        dm_log.add_field(name="Пользователь", value=member.mention, inline=False)
        dm_log.add_field(name="Статус", value="✅ Отправлено" if dm_sent else "❌ Отказано", inline=False)

        await self.bot.send_log(member.guild.id, dm_log)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        mid = str(member.id)
        invites_data = settings_db.get(member.guild.id, "invites_stats", {})
        stats = invites_data.setdefault("stats", {})
        invite_history = invites_data.setdefault("invite_history", {})
        
        if mid in invite_history:
            inv_id = invite_history.pop(mid)
            if inv_id in stats:
                stats[inv_id]["leaves"] += 1
                stats[inv_id]["invites"] = max(0, stats[inv_id].get("invites", 0) - 1)
            settings_db.put(member.guild.id, "invites_stats", invites_data)

    @app_commands.command(name="userinfo", description="Показать сводку по участнику сервера")
    @app_commands.describe(user="Пользователь")
    @app_commands.default_permissions(manage_messages=True)
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member):
        invites_data = settings_db.get(interaction.guild_id, "invites_stats", {})
        stats_dict = invites_data.setdefault("stats", {})
        stats = stats_dict.get(str(user.id), {"joins": 0, "leaves": 0, "invites": 0})
        
        cases = settings_db.get(interaction.guild_id, "feedback_cases", {})
        cases_count = sum(1 for c in cases.values() if c.get("submitter_id") == user.id)

        embed = discord.Embed(
            title=f"Сводка по {user.name}",
            color=user.color or discord.Color.blurple(),
            timestamp=self.bot.utcnow()
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="Вход на сервер", value=discord.utils.format_dt(user.joined_at, "D") if user.joined_at else "Неизвестно", inline=True)
        embed.add_field(name="Регистрация", value=discord.utils.format_dt(user.created_at, "D"), inline=True)
        
        roles = [r.mention for r in user.roles if r.name != "@everyone"]
        roles_text = " ".join(roles) if roles else "Нет ролей"
        if len(roles_text) > 1024:
            roles_text = f"{len(roles)} ролей"
        embed.add_field(name="Роли", value=roles_text, inline=False)
        
        embed.add_field(name="Приглашения", value=f"Актуально: {stats.get('invites', 0)} (Всего зашло: {stats.get('joins', 0)}, Ушло: {stats.get('leaves', 0)})", inline=False)
        embed.add_field(name="Создано обращений/жалоб", value=str(cases_count), inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
