import discord
from discord.ext import commands
from discord import app_commands
import os
from typing import Optional
import logging

logger = logging.getLogger("chetbot.feedback")

_feedback_categories_cache = None

PANEL_BANNER_URL = "https://i.imgur.com/vLAcc7q.png"


def _env_int(key: str) -> int:
    """Безопасно читает переменную окружения и конвертирует в int."""
    val = os.getenv(key)
    if not val:
        raise RuntimeError(f"Переменная окружения {key} не задана.")
    return int(val)


def get_feedback_categories():
    global _feedback_categories_cache
    if _feedback_categories_cache is not None:
        return _feedback_categories_cache

    _feedback_categories_cache = {
        "players": {
            "title": "Жалоба на участника",
            "button_label": "            Жалоба на участника            ",
            "button_style": discord.ButtonStyle.secondary,
            "channel_id": _env_int("CHANNEL_COMPLAINT_PLAY"),
            "case_prefix": "PR",
            "case_title": "Жалоба на участника",
            "thread_name": "player-report",
            "review_role_ids": [_env_int("ROLE_PLAYERS")],
            "review_user_ids": [],
            "approved_text": "Участник наказан.",
            "denied_text": "Жалоба отклонена.",
            "modal_title": "Жалоба на участника",
            "fields": [
                {"key": "offender", "label": "Ник / ID участника", "style": discord.TextStyle.short, "required": True, "max_length": 120},
                {"key": "complaint", "label": "Суть жалобы", "style": discord.TextStyle.paragraph, "required": True, "max_length": 1000},
                {"key": "datetime", "label": "Дата и время ситуации", "style": discord.TextStyle.short, "required": False, "max_length": 120},
                {"key": "proof", "label": "Доказательства", "style": discord.TextStyle.paragraph, "required": False, "max_length": 1000},
            ],
            "mini_summary_key": "offender",
        },
    }
    return _feedback_categories_cache


class FeedbackMenu(commands.Cog):
    feedback_panel_group = app_commands.Group(
        name="feedback_panel",
        description="Управление панелью обратной связи",
        guild_only=True,
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if not getattr(self.bot, "_feedback_views_loaded", False):
            self.bot.add_view(FeedbackView(self.bot))
            await self.restore_feedback_views()
            self.bot._feedback_views_loaded = True

    async def restore_feedback_views(self):
        for case_id, case_data in self.bot.feedback_cases.items():
            if case_data.get("status") != "pending":
                continue
            message_id = case_data.get("decision_message_id")
            submitter_id = case_data.get("submitter_id")
            category_key = case_data.get("category_key")
            if not message_id or not submitter_id or not category_key:
                continue
            self.bot.add_view(
                FeedbackDecisionView(self.bot, case_id, submitter_id, category_key),
                message_id=message_id,
            )

    @feedback_panel_group.command(name="send", description="Опубликовать панель обратной связи")
    @app_commands.describe(channel="Канал для публикации панели")
    async def feedback_panel_send(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
    ):
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message("Нужен обычный текстовый канал.", ephemeral=True)
            return

        embed = discord.Embed(
            description=(
                "### <:IconModeration:1356540597770518538>・Выберите тип связи со стаффом.\n\n"
                "```\n"
                "В создавшемся обращении, как можно точнее опишите его суть "
                "и по возможности прикрепите фото и/или видео для дальнейшего ознакомления.\n"
                "```"
            ),
            color=discord.Color.from_rgb(44, 47, 51),
        )
        embed.set_image(url=PANEL_BANNER_URL)

        # Сначала отвечаем на interaction, потом отправляем панель
        await interaction.response.send_message("Панель опубликована.", ephemeral=True)
        message = await target_channel.send(embed=embed, view=FeedbackView(self.bot))

        log_embed = discord.Embed(
            title="🧩 Панель feedback опубликована",
            description=(
                f"**Кто:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**Канал:** {target_channel.mention}\n"
                f"**Сообщение:** [Открыть]({message.jump_url})"
            ),
            color=discord.Color.blurple(),
            timestamp=self.bot.utcnow(),
        )
        await self.bot.send_log(log_embed)


class FeedbackView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        categories = get_feedback_categories()

        for category_key, config in categories.items():
            button = discord.ui.Button(
                label=config["button_label"],
                style=config["button_style"],
                custom_id=f"feedback_open:{category_key}",
                row=0,
            )

            async def callback(interaction: discord.Interaction, ck=category_key):
                await interaction.response.send_modal(FeedbackModal(self.bot, ck))

            button.callback = callback
            self.add_item(button)


class FeedbackModal(discord.ui.Modal):
    def __init__(self, bot, category_key: str):
        self.bot = bot
        self.category_key = category_key
        config = get_feedback_categories()[category_key]
        super().__init__(title=config["modal_title"], timeout=None)

        self.field_keys = []
        for field in config["fields"]:
            input_item = discord.ui.TextInput(
                label=field["label"],
                style=field["style"],
                required=field["required"],
                max_length=field["max_length"],
            )
            self.add_item(input_item)
            self.field_keys.append(field["key"])

    async def on_submit(self, interaction: discord.Interaction):
        answers = {}
        for key, child in zip(self.field_keys, self.children):
            if isinstance(child, discord.ui.TextInput):
                answers[key] = (child.value or "").strip() or "—"

        try:
            await create_feedback_case(interaction, self.bot, self.category_key, answers)
        except Exception as exc:
            logger.error("Ошибка при создании обращения: %s", exc, exc_info=True)
            embed = discord.Embed(
                title="❌ Ошибка при создании обращения",
                description=(
                    f"**Категория:** {get_feedback_categories()[self.category_key]['title']}\n"
                    f"**Пользователь:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                    f"**Ошибка:** `{exc}`"
                ),
                color=discord.Color.red(),
                timestamp=self.bot.utcnow(),
            )
            await self.bot.send_log(embed)
            if interaction.response.is_done():
                await interaction.followup.send("Не удалось создать обращение.", ephemeral=True)
            else:
                await interaction.response.send_message("Не удалось создать обращение.", ephemeral=True)


class FeedbackDecisionView(discord.ui.View):
    def __init__(self, bot, case_id: str, submitter_id: int, category_key: str, disabled: bool = False):
        super().__init__(timeout=None)
        self.bot = bot
        self.case_id = case_id
        self.submitter_id = submitter_id
        self.category_key = category_key

        approve_btn = discord.ui.Button(
            label="Принять",
            style=discord.ButtonStyle.success,
            custom_id=f"feedback_accept:{case_id}",
            disabled=disabled,
        )
        reject_btn = discord.ui.Button(
            label="Отклонить",
            style=discord.ButtonStyle.danger,
            custom_id=f"feedback_reject:{case_id}",
            disabled=disabled,
        )

        approve_btn.callback = self.approve_callback
        reject_btn.callback = self.reject_callback

        self.add_item(approve_btn)
        self.add_item(reject_btn)

    async def approve_callback(self, interaction: discord.Interaction):
        await close_case(interaction, self.bot, self.case_id, approved=True)

    async def reject_callback(self, interaction: discord.Interaction):
        await close_case(interaction, self.bot, self.case_id, approved=False)


# --- Хелперы для обращений ---

async def get_next_case_id(bot, prefix: str) -> str:
    current = int(bot.feedback_counters.get(prefix, 0)) + 1
    bot.feedback_counters[prefix] = current
    await bot.update_file()
    return f"{prefix}-{current:04d}"


def build_mentions(config: dict) -> str:
    parts = [f"<@&{r_id}>" for r_id in config["review_role_ids"]]
    parts.extend(f"<@{u_id}>" for u_id in config["review_user_ids"])
    return " ".join(parts).strip() or "Без упоминаний"


def upsert_embed_field(embed: discord.Embed, field_name: str, value: str, inline: bool = False):
    for index, field in enumerate(embed.fields):
        if field.name == field_name:
            embed.set_field_at(index, name=field_name, value=value, inline=inline)
            return
    embed.add_field(name=field_name, value=value, inline=inline)


async def add_reviewers(thread: discord.Thread, guild: discord.Guild, config: dict):
    added_ids = set()
    for role_id in config["review_role_ids"]:
        role = guild.get_role(role_id)
        if not role:
            continue
        for member in role.members:
            if not member.bot and member.id not in added_ids:
                try:
                    await thread.add_user(member)
                    added_ids.add(member.id)
                except Exception as e:
                    logger.debug("Не удалось добавить %s в тред: %s", member.id, e)

    for user_id in config["review_user_ids"]:
        member = guild.get_member(user_id)
        if member and not member.bot and member.id not in added_ids:
            try:
                await thread.add_user(member)
                added_ids.add(member.id)
            except Exception as e:
                logger.debug("Не удалось добавить %s в тред: %s", member.id, e)


async def create_feedback_case(interaction: discord.Interaction, bot, category_key: str, answers: dict):
    config = get_feedback_categories()[category_key]
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    parent_channel = bot.get_channel(config["channel_id"])
    if not isinstance(parent_channel, discord.TextChannel):
        await interaction.followup.send("Целевой канал не найден или не является текстовым.", ephemeral=True)
        return

    case_id = await get_next_case_id(bot, config["case_prefix"])
    summary_val = answers.get(config["mini_summary_key"], "—")

    mini_embed = discord.Embed(
        title=f"📨 {config['case_title']} · {case_id}",
        color=discord.Color.blurple(),
        timestamp=bot.utcnow(),
    )
    mini_embed.add_field(name="Отправитель", value=interaction.user.mention, inline=True)
    mini_embed.add_field(name="Статус", value="На рассмотрении", inline=True)
    mini_embed.add_field(name="Кратко", value=summary_val[:1024], inline=False)
    mini_embed.set_footer(text=f"ID пользователя: {interaction.user.id}")

    public_message = await parent_channel.send(embed=mini_embed)

    thread = await parent_channel.create_thread(
        name=f"{config['thread_name']}-{case_id.lower()}",
        type=discord.ChannelType.private_thread,
        invitable=False,
        auto_archive_duration=1440,
        reason=f"Внутреннее обращение {case_id}",
    )
    await add_reviewers(thread, interaction.guild, config)

    mentions = build_mentions(config)
    try:
        await thread.send(
            content=mentions,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )
    except Exception as e:
        logger.warning("Не удалось отправить упоминания в тред %s: %s", thread.id, e)

    full_embed = discord.Embed(
        title=f"🔒 Внутреннее обращение · {case_id}",
        color=discord.Color.orange(),
        timestamp=bot.utcnow(),
    )
    full_embed.add_field(name="Отправитель", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
    full_embed.add_field(name="Публичное сообщение", value=f"[Открыть]({public_message.jump_url})", inline=False)
    for field in config["fields"]:
        val = answers.get(field["key"], "—")
        full_embed.add_field(name=field["label"], value=val[:1024] if val else "—", inline=False)
    full_embed.add_field(name="Статус", value="Ожидает решения", inline=False)
    full_embed.set_footer(text="Доступно только для staff")

    decision_view = FeedbackDecisionView(bot, case_id, interaction.user.id, category_key)
    decision_message = await thread.send(embed=full_embed, view=decision_view)

    bot.feedback_cases[case_id] = {
        "case_id": case_id,
        "category_key": category_key,
        "submitter_id": interaction.user.id,
        "public_channel_id": parent_channel.id,
        "public_message_id": public_message.id,
        "thread_id": thread.id,
        "decision_message_id": decision_message.id,
        "status": "pending",
        "created_at": bot.utcnow().isoformat(),
    }
    await bot.update_file()

    log_embed = discord.Embed(
        title="📥 Создано новое обращение",
        description=(
            f"**Номер:** `{case_id}`\n"
            f"**Отправитель:** {interaction.user.mention} (`{interaction.user.id}`)\n"
            f"**Канал:** <#{parent_channel.id}>\n"
            f"**Ветка:** <#{thread.id}>\n"
            f"**Пинги:** {mentions}"
        ),
        color=discord.Color.blurple(),
        timestamp=bot.utcnow(),
    )
    await bot.send_log(log_embed)

    await interaction.followup.send(
        f"Обращение зарегистрировано. Номер: **{case_id}**.\nИтог рассмотрения придёт вам в личные сообщения.",
        ephemeral=True,
    )


async def close_case(interaction: discord.Interaction, bot, case_id: str, approved: bool):
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    try:
        case_data = bot.feedback_cases.get(case_id)
        if not case_data or case_data.get("status") != "pending":
            await interaction.followup.send("Обращение не найдено или уже закрыто.", ephemeral=True)
            return

        category_key = case_data["category_key"]
        config = get_feedback_categories()[category_key]
        status_text = "Принято" if approved else "Отклонено"
        reviewed_status = f"Рассмотрено · {status_text}"

        case_data["status"] = "approved" if approved else "denied"
        case_data["status_label"] = reviewed_status
        case_data["reviewed_by"] = interaction.user.id
        case_data["reviewed_at"] = bot.utcnow().isoformat()
        await bot.update_file()

        color = discord.Color.green() if approved else discord.Color.red()

        public_channel = bot.get_channel(case_data.get("public_channel_id"))
        if isinstance(public_channel, discord.TextChannel):
            try:
                public_message = await public_channel.fetch_message(case_data["public_message_id"])
                if public_message.embeds:
                    emb = public_message.embeds[0].copy()
                    emb.color = color
                    upsert_embed_field(emb, "Статус", reviewed_status, inline=True)
                    upsert_embed_field(emb, "Рассмотрел", f"{interaction.user.mention}", inline=False)
                    await public_message.edit(embed=emb)
            except Exception as e:
                logger.warning("Не удалось обновить публичное сообщение для %s: %s", case_id, e)

        thread = bot.get_channel(case_data.get("thread_id"))
        if isinstance(thread, discord.Thread):
            try:
                decision_message = await thread.fetch_message(case_data["decision_message_id"])
                if decision_message.embeds:
                    emb = decision_message.embeds[0].copy()
                    emb.color = color
                    upsert_embed_field(emb, "Статус", reviewed_status, inline=False)
                    upsert_embed_field(emb, "Рассмотрел", f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
                    await decision_message.edit(
                        embed=emb,
                        view=FeedbackDecisionView(bot, case_id, case_data["submitter_id"], category_key, disabled=True),
                    )
            except Exception as e:
                logger.warning("Не удалось обновить сообщение решения для %s: %s", case_id, e)

        user = interaction.guild.get_member(case_data["submitter_id"]) if interaction.guild else None
        if user is None:
            try:
                user = await bot.fetch_user(case_data["submitter_id"])
            except Exception as e:
                logger.debug("Не удалось получить пользователя %s: %s", case_data["submitter_id"], e)

        dm_ok = False
        if user:
            dm_emb = discord.Embed(
                title=f"Результат по обращению №{case_id}",
                description="Ваше обращение было рассмотрено.",
                color=color,
                timestamp=bot.utcnow(),
            )
            dm_emb.add_field(name="Статус", value="Рассмотрено", inline=False)
            dm_emb.add_field(name="Итог", value=config["approved_text"] if approved else config["denied_text"], inline=False)
            dm_emb.add_field(name="Рассмотрел", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            dm_emb.set_footer(text=f"Номер обращения: {case_id}")
            try:
                await user.send(embed=dm_emb)
                dm_ok = True
            except Exception as e:
                logger.debug("Не удалось отправить DM пользователю %s: %s", user.id, e)

        log_emb = discord.Embed(
            title="📌 Решение по обращению",
            description=(
                f"**Номер:** `{case_id}`\n"
                f"**Статус:** Рассмотрено\n"
                f"**Решение:** {status_text}\n"
                f"**Рассмотрел:** {interaction.user.mention} (`{interaction.user.id}`)\n"
                f"**DM:** {'Успешно' if dm_ok else 'Не удалось отправить'}"
            ),
            color=color,
            timestamp=bot.utcnow(),
        )
        await bot.send_log(log_emb)

        if isinstance(interaction.channel, discord.Thread):
            dec_emb = discord.Embed(
                title=f"Решение по обращению {case_id}",
                color=color,
                timestamp=bot.utcnow(),
            )
            dec_emb.add_field(name="Статус", value=status_text, inline=False)
            dec_emb.add_field(name="Рассмотрел", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)
            try:
                await interaction.channel.send(embed=dec_emb)
                await interaction.channel.edit(archived=True, locked=True)
            except Exception as e:
                logger.warning("Не удалось закрыть тред %s: %s", interaction.channel.id, e)
    except Exception as e:
        logger.error("Ошибка при закрытии обращения %s: %s", case_id, e)
        await interaction.followup.send("❌ Произошла ошибка при закрытии обращения. Администраторы уведомлены.", ephemeral=True)


async def setup(bot):
    await bot.add_cog(FeedbackMenu(bot))
