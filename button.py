import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import time
import aiohttp

import bot_config
import i18n
import slash_registry
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
    def __init__(self, bot, title: str, questions: list[str], button_name: str, lang: str):
        super().__init__(title=title, timeout=None)
        self.bot = bot
        self.questions = questions
        self.button_name = button_name
        self.lang = lang
        self.inputs: list[discord.ui.TextInput] = []

        for idx, q in enumerate(self.questions, start=1):
            inp = discord.ui.TextInput(
                label=q[:45] if q else i18n.t("button.question_fallback", lang, index=idx),
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=1000,
                placeholder=i18n.t("button.answer_placeholder", lang),
            )
            self.add_item(inp)
            self.inputs.append(inp)

    async def on_submit(self, interaction: discord.Interaction):
        lang = self.lang
        answers = []
        for i, (q, inp) in enumerate(zip(self.questions, self.inputs), start=1):
            val = (inp.value or "").strip()
            answers.append(
                (
                    q or i18n.t("button.question_fallback", lang, index=i),
                    val if val else "—",
                )
            )

        embed = discord.Embed(
            title=i18n.t("button.embed.title", lang, name=self.button_name),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        embed.add_field(
            name=i18n.t("button.embed.submitter", lang),
            value=f"{interaction.user.mention}",
            inline=False,
        )
        for q, a in answers:
            embed.add_field(
                name=q[:256] if q else i18n.t("button.embed.question_fallback", lang),
                value=a[:1024] if a else "—",
                inline=False,
            )
        embed.set_footer(text=i18n.t("button.embed.footer", lang))

        webhook_url = bot_config.get(interaction.guild.id, "BUTTON_WEBHOOK_URL")
        if not webhook_url:
            await interaction.response.send_message(i18n.t("button.webhook_missing", lang), ephemeral=True)
            return

        try:
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(webhook_url, session=session)
                username = (bot_config.get(interaction.guild.id, "BUTTON_WEBHOOK_USERNAME") or "").strip()
                if not username:
                    username = "404 Button Collector"
                avatar_url = (bot_config.get(interaction.guild.id, "BUTTON_WEBHOOK_AVATAR_URL") or "").strip()
                send_kwargs: dict = {"embed": embed, "username": username}
                if avatar_url:
                    send_kwargs["avatar_url"] = avatar_url
                await webhook.send(**send_kwargs)
        except Exception as exc:
            await interaction.response.send_message(
                i18n.t("button.webhook_error", lang, error=exc), ephemeral=True
            )
            return

        await interaction.response.send_message(i18n.t("button.sent", lang), ephemeral=True)

        log_embed = discord.Embed(
            title=i18n.t("button.log.form_submit", lang),
            description=i18n.t(
                "button.log.form_submit_body",
                lang,
                name=self.button_name,
                mention=interaction.user.mention,
                user_id=interaction.user.id,
            ),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.set_footer(text=i18n.t("button.log.form_footer", lang))
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
        lang = i18n.lang_for(interaction.guild_id)
        # Cooldown
        remaining = self._check_cooldown(interaction.user.id)
        if remaining is not None:
            await interaction.response.send_message(
                i18n.t("button.cooldown", lang, seconds=remaining),
                ephemeral=True,
            )
            return

        # custom_id = "btn_role_{role_id}"
        try:
            role_id = int(custom_id.removeprefix("btn_role_"))
        except ValueError:
            return

        role = interaction.guild.get_role(role_id)
        if not role:
            await interaction.response.send_message(i18n.t("button.role_not_found", lang), ephemeral=True)
            return

        member = interaction.user
        role_added = False
        if role in member.roles:
            try:
                await member.remove_roles(role, reason="Role-button toggle")
                await interaction.response.send_message(
                    i18n.t("button.role_removed", lang, name=role.name), ephemeral=True
                )
                action = i18n.t("button.role_action_removed", lang)
            except discord.Forbidden:
                await interaction.response.send_message(
                    i18n.t("button.role_remove_forbidden", lang), ephemeral=True
                )
                return
        else:
            try:
                await member.add_roles(role, reason="Role-button toggle")
                await interaction.response.send_message(
                    i18n.t("button.role_added", lang, name=role.name), ephemeral=True
                )
                action = i18n.t("button.role_action_added", lang)
                role_added = True
            except discord.Forbidden:
                await interaction.response.send_message(
                    i18n.t("button.role_add_forbidden", lang), ephemeral=True
                )
                return

        log_embed = discord.Embed(
            title=i18n.t("button.log.role_title", lang),
            description=i18n.t(
                "button.log.role_body",
                lang,
                mention=role.mention,
                role_id=role.id,
                action=action,
                mention_user=member.mention,
                user_id=member.id,
            ),
            color=discord.Color.green() if role_added else discord.Color.orange(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.set_footer(text=i18n.t("button.log.role_footer", lang))
        await self.bot.send_log(interaction.guild.id, log_embed)

    async def _handle_form_click(self, interaction: discord.Interaction, custom_id: str):
        lang = i18n.lang_for(interaction.guild_id)
        remaining = self._check_cooldown(interaction.user.id)
        if remaining is not None:
            await interaction.response.send_message(
                i18n.t("button.cooldown", lang, seconds=remaining),
                ephemeral=True,
            )
            return

        form_id = custom_id.removeprefix("btn_form_")
        form_data = _load_buttons_config(interaction.guild_id).get("forms", {}).get(form_id)
        if not form_data:
            await interaction.response.send_message(i18n.t("button.form_not_found", lang), ephemeral=True)
            return

        button_name = form_data["button_name"]
        questions = form_data["questions"]

        modal = DynamicQuestionsModal(
            self.bot,
            title=i18n.t("button.modal_title", lang, name=button_name),
            questions=questions,
            button_name=button_name,
            lang=lang,
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
        lang = i18n.lang_for(interaction.guild_id)
        if not self._has_permission(interaction.user):
            await interaction.response.send_message(i18n.t("button.no_permission", lang), ephemeral=True)
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
        lang = i18n.lang_for(interaction.guild_id)
        if not self._has_permission(interaction.user):
            await interaction.response.send_message(i18n.t("button.no_permission", lang), ephemeral=True)
            return

        await self._create_role(interaction, name, [r1, r2, r3, r4, r5])

    # ---------- internal ----------

    async def _create_form(self, interaction: discord.Interaction, name: str, raw_questions: list):
        lang = i18n.lang_for(interaction.guild_id)
        default_q = i18n.t("button.default_question", lang)
        questions = [q for q in raw_questions if q] or [default_q]

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
        await interaction.response.send_message(i18n.t("button.form_created", lang), ephemeral=True)
        await interaction.channel.send(view=view)

        log_embed = discord.Embed(
            title=i18n.t("button.log.create_form", lang),
            description=i18n.t(
                "button.log.create_form_body",
                lang,
                name=name,
                channel=interaction.channel.mention,
                mention=interaction.user.mention,
                user_id=interaction.user.id,
            ),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        if questions and questions != [default_q]:
            log_embed.add_field(
                name=i18n.t("button.log.questions", lang),
                value="\n".join(f"• {q}" for q in questions),
                inline=False,
            )
        log_embed.set_footer(text=i18n.t("button.log.create_form_footer", lang))
        await self.bot.send_log(interaction.guild.id, log_embed)

    async def _create_role(self, interaction: discord.Interaction, name: str, raw_roles: list):
        lang = i18n.lang_for(interaction.guild_id)
        roles = [r for r in raw_roles if r is not None]
        if not roles:
            await interaction.response.send_message(i18n.t("button.need_role", lang), ephemeral=True)
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
        await interaction.response.send_message(i18n.t("button.role_created", lang), ephemeral=True)
        await interaction.channel.send(view=view)

        role_list = "\n".join(f"• {r.mention} (`{r.id}`)" for r in roles)
        log_embed = discord.Embed(
            title=i18n.t("button.log.create_role", lang),
            description=i18n.t(
                "button.log.create_role_body",
                lang,
                name=name,
                channel=interaction.channel.mention,
                mention=interaction.user.mention,
                user_id=interaction.user.id,
            ),
            color=discord.Color.green(),
            timestamp=self.bot.utcnow(),
        )
        log_embed.add_field(name=i18n.t("button.log.roles", lang), value=role_list, inline=False)
        log_embed.set_footer(text=i18n.t("button.log.create_role_footer", lang))
        await self.bot.send_log(interaction.guild.id, log_embed)


async def setup(bot):
    cog = ButtonCreate(bot)
    slash_registry.register_button(cog)
    await bot.add_cog(cog)
