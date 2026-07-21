import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import time
import aiohttp

import bot_config
import settings_db

logger = logging.getLogger("chetbot.button")

MODULE_NAME = "buttons"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP
COOLDOWN_SECONDS = 5


def _load_buttons_config(guild_id: int) -> dict:
    data = settings_db.get(guild_id, MODULE_NAME)
    data.setdefault("forms", {})
    data.setdefault("next_form_id", 1)
    return data


def _save_buttons_config(guild_id: int, data: dict):
    settings_db.put(guild_id, MODULE_NAME, data)


def _get_allowed_role_ids(guild_id: int) -> set[int]:
    raw = bot_config.get(guild_id, "BUTTON_CREATE_ALLOWED_ROLES", [])
    return {int(x) for x in raw}


# ─────────────────────────────────────────────
#  Модалка формы
# ─────────────────────────────────────────────

class DynamicQuestionsModal(discord.ui.Modal):
    def __init__(self, bot, title: str, questions: list[str], button_name: str):
        super().__init__(title=title, timeout=None)
        self.bot = bot
        self.questions = questions
        self.button_name = button_name
        self.inputs: list[discord.ui.TextInput] = []

        for idx, q in enumerate(self.questions, start=1):
            inp = discord.ui.TextInput(
                label=q[:45] if q else f"Вопрос {idx}",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000,
                placeholder="Ваш ответ…",
            )
            self.add_item(inp)
            self.inputs.append(inp)

    async def on_submit(self, interaction: discord.Interaction):
        answers = []
        for i, (q, inp) in enumerate(zip(self.questions, self.inputs), start=1):
            val = (inp.value or "").strip()
            answers.append((q or f"Вопрос {i}", val if val else "—"))

        embed = discord.Embed(
            title=f"📝 Ответ по кнопке: {self.button_name}",
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(name="Отправитель", value=f"{interaction.user.mention}", inline=False)
        for q, a in answers:
            embed.add_field(name=q[:256] if q else "Вопрос", value=a[:1024] if a else "—", inline=False)
        embed.set_footer(text="404 Helper · Button Form")

        webhook_url = bot_config.get(interaction.guild.id, "BUTTON_WEBHOOK_URL")
        if not webhook_url:
            await interaction.response.send_message("BUTTON_WEBHOOK_URL не задан в переменных окружения.", ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                await webhook.send(embed=embed, username="404 Button Collector", avatar_url="https://i.imgur.com/4ydti00.png")
        except Exception as exc:
            await interaction.response.send_message(f"⚠️ Ошибка отправки в вебхук: {exc}", ephemeral=True)
            return

        await interaction.response.send_message("✅ Отправлено!", ephemeral=True)

        # --- лог ---
        log_embed = discord.Embed(
            title="📋 Форма отправлена",
            description=(
                f"**Кнопка:** {self.button_name}\n"
                f"**Пользователь:** {interaction.user.mention} (`{interaction.user.id}`)"
            ),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.set_footer(text="Button · Form Submit")
        await self.bot.send_log(interaction.guild.id, log_embed)


# ─────────────────────────────────────────────
#  Cog
# ─────────────────────────────────────────────

class ButtonCreate(commands.Cog):
    button_group = app_commands.Group(
        name="button_create",
        description="Создать кнопку (форма или выдача ролей)",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot):
        self.bot = bot
        self._cooldowns: dict[int, float] = {}
        self._cleanup_cooldowns.start()

    async def _save_and_cache(self, guild_id: int, config: dict):
        _save_buttons_config(guild_id, config)

    def cog_unload(self):
        self._cleanup_cooldowns.cancel()

    # ---------- periodic cleanup ----------

    @tasks.loop(minutes=10)
    async def _cleanup_cooldowns(self):
        """Удаляет устаревшие записи кулдаунов."""
        # Всё тело под try/except: необработанное исключение навсегда остановило бы tasks.loop.
        try:
            now = time.time()
            expired = [uid for uid, ts in self._cooldowns.items() if now - ts > COOLDOWN_SECONDS * 2]
            for uid in expired:
                del self._cooldowns[uid]
        except Exception:
            logger.exception("_cleanup_cooldowns: ошибка итерации — цикл продолжает работать")

    @_cleanup_cooldowns.error
    async def _cleanup_cooldowns_error(self, _error: BaseException):
        logger.exception("_cleanup_cooldowns: критическая ошибка — перезапуск цикла")
        self._cleanup_cooldowns.restart()

    @_cleanup_cooldowns.before_loop
    async def _before_cleanup(self):
        await self.bot.wait_until_ready()

    # ---------- helpers ----------

    def _check_cooldown(self, user_id: int) -> float | None:
        """Возвращает оставшиеся секунды если кулдаун активен, иначе None."""
        now = time.time()
        last = self._cooldowns.get(user_id, 0)
        remaining = COOLDOWN_SECONDS - (now - last)
        if remaining > 0:
            return remaining
        self._cooldowns[user_id] = now
        return None

    def _has_permission(self, member: discord.Member) -> bool:
        """Проверяет, есть ли у участника права на создание кнопок."""
        if member.guild_permissions.administrator:
            return True
        allowed = _get_allowed_role_ids(member.guild.id)
        return any(role.id in allowed for role in member.roles)

    # ---------- persistent handler ----------

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        """Обработка всех нажатий на кнопки — работает и после перезагрузки бота."""
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id.startswith("btn_role_"):
            await self._handle_role_click(interaction, custom_id)
        elif custom_id.startswith("btn_form_"):
            await self._handle_form_click(interaction, custom_id)

    async def _handle_role_click(self, interaction: discord.Interaction, custom_id: str):
        # Cooldown
        remaining = self._check_cooldown(interaction.user.id)
        if remaining is not None:
            await interaction.response.send_message(
                f"⏳ Подождите {remaining:.0f} сек. перед следующим нажатием.", ephemeral=True,
            )
            return

        # custom_id = "btn_role_{role_id}"
        try:
            role_id = int(custom_id.removeprefix("btn_role_"))
        except ValueError:
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message("Роль не найдена на сервере.", ephemeral=True)
            return

        member = interaction.user
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Role-button toggle")
                await interaction.response.send_message(f"❌ Роль **{role.name}** снята.", ephemeral=True)
                action = "снята"
            except discord.Forbidden:
                await interaction.response.send_message("У бота нет прав для снятия этой роли.", ephemeral=True)
                return
        else:
            try:
                await member.add_roles(role, reason="Role-button toggle")
                await interaction.response.send_message(f"✅ Роль **{role.name}** выдана.", ephemeral=True)
                action = "выдана"
            except discord.Forbidden:
                await interaction.response.send_message("У бота нет прав для выдачи этой роли.", ephemeral=True)
                return

        # --- лог ---
        log_embed = discord.Embed(
            title="🏷️ Роль через кнопку",
            description=(
                f"**Роль:** {role.mention} (`{role.id}`)\n"
                f"**Действие:** {action}\n"
                f"**Пользователь:** {member.mention} (`{member.id}`)"
            ),
            color=discord.Color.green() if action == "выдана" else discord.Color.orange(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.set_footer(text="Button · Role Toggle")
        await self.bot.send_log(interaction.guild.id, log_embed)

    async def _handle_form_click(self, interaction: discord.Interaction, custom_id: str):
        # Cooldown
        remaining = self._check_cooldown(interaction.user.id)
        if remaining is not None:
            await interaction.response.send_message(
                f"⏳ Подождите {remaining:.0f} сек. перед следующим нажатием.", ephemeral=True,
            )
            return

        # custom_id = "btn_form_{form_id}"
        form_id = custom_id.removeprefix("btn_form_")
        form_data = _load_buttons_config(interaction.guild_id).get("forms", {}).get(form_id)
        if not form_data:
            await interaction.response.send_message("⚠️ Конфигурация формы не найдена.", ephemeral=True)
            return

        button_name = form_data["button_name"]
        questions = form_data["questions"]

        modal = DynamicQuestionsModal(
            self.bot,
            title=f"Форма: {button_name}",
            questions=questions,
            button_name=button_name,
        )
        await interaction.response.send_modal(modal)

    # ---------- subcommands ----------

    @button_group.command(name="form", description="Создать кнопку с формой")
    @app_commands.describe(
        name="Текст на кнопке",
        q1="Вопрос 1",
        q2="Вопрос 2",
        q3="Вопрос 3",
        q4="Вопрос 4",
        q5="Вопрос 5",
    )
    async def button_create_form(
        self,
        interaction: discord.Interaction,
        name: str,
        q1: str | None = None,
        q2: str | None = None,
        q3: str | None = None,
        q4: str | None = None,
        q5: str | None = None,
    ):
        if not self._has_permission(interaction.user):
            await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
            return

        await self._create_form(interaction, name, [q1, q2, q3, q4, q5])

    @button_group.command(name="role", description="Создать кнопку для выдачи ролей")
    @app_commands.describe(
        name="Заголовок панели",
        r1="Роль 1",
        r2="Роль 2",
        r3="Роль 3",
        r4="Роль 4",
        r5="Роль 5",
    )
    async def button_create_role(
        self,
        interaction: discord.Interaction,
        name: str,
        r1: discord.Role | None = None,
        r2: discord.Role | None = None,
        r3: discord.Role | None = None,
        r4: discord.Role | None = None,
        r5: discord.Role | None = None,
    ):
        if not self._has_permission(interaction.user):
            await interaction.response.send_message("❌ У вас нет прав для использования этой команды.", ephemeral=True)
            return

        await self._create_role(interaction, name, [r1, r2, r3, r4, r5])

    # ---------- internal ----------

    async def _create_form(self, interaction: discord.Interaction, name: str, raw_questions: list):
        questions = [q for q in raw_questions if q] or ["Ответ"]

        # Сохраняем конфиг формы
        config = _load_buttons_config(interaction.guild_id)
        form_id = str(config.get("next_form_id", 1))
        config["forms"][form_id] = {
            "button_name": name,
            "questions": questions,
        }
        config["next_form_id"] = int(form_id) + 1
        await self._save_and_cache(interaction.guild_id, config)

        # Собираем View
        view = discord.ui.View(timeout=None)
        btn = discord.ui.Button(
            label=name[:80],
            style=discord.ButtonStyle.primary,
            custom_id=f"btn_form_{form_id}",
        )
        view.add_item(btn)

        # Сначала отвечаем на interaction, потом отправляем кнопку
        await interaction.response.send_message("✅ Кнопка-форма создана.", ephemeral=True)
        await interaction.channel.send(view=view)

        # --- лог ---
        log_embed = discord.Embed(
            title="🆕 Создана кнопка-форма",
            description=(
                f"**Название:** {name}\n"
                f"**Канал:** {interaction.channel.mention}\n"
                f"**Создал:** {interaction.user.mention} (`{interaction.user.id}`)"
            ),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        if questions and questions != ["Ответ"]:
            log_embed.add_field(name="Вопросы", value="\n".join(f"• {q}" for q in questions), inline=False)
        log_embed.set_footer(text="Button · Create Form")
        await self.bot.send_log(interaction.guild.id, log_embed)

    async def _create_role(self, interaction: discord.Interaction, name: str, raw_roles: list):
        roles = [r for r in raw_roles if r is not None]
        if not roles:
            await interaction.response.send_message("Укажите хотя бы одну роль (r1 – r5).", ephemeral=True)
            return

        # Собираем View
        view = discord.ui.View(timeout=None)
        for role in roles:
            btn = discord.ui.Button(
                label=role.name[:80],
                style=discord.ButtonStyle.secondary,
                custom_id=f"btn_role_{role.id}",
            )
            view.add_item(btn)

        # Сначала отвечаем на interaction, потом отправляем кнопку
        await interaction.response.send_message("✅ Кнопка-роль создана.", ephemeral=True)
        await interaction.channel.send(view=view)

        # --- лог ---
        role_list = "\n".join(f"• {r.mention} (`{r.id}`)" for r in roles)
        log_embed = discord.Embed(
            title="🆕 Создана кнопка-роль",
            description=(
                f"**Название:** {name}\n"
                f"**Канал:** {interaction.channel.mention}\n"
                f"**Создал:** {interaction.user.mention} (`{interaction.user.id}`)"
            ),
            color=discord.Color.green(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.add_field(name="Роли", value=role_list, inline=False)
        log_embed.set_footer(text="Button · Create Role")
        await self.bot.send_log(interaction.guild.id, log_embed)


async def setup(bot):
    await bot.add_cog(ButtonCreate(bot))
