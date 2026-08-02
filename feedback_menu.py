import settings_db
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

import embed_style
import feedback_categories
import feedback_core
import feedback_panel_core
import i18n
import slash_registry

logger = logging.getLogger("chetbot.feedback")


def get_feedback_categories(guild_id: int):
    # Фаза 2.4: категории обращений — per-guild. Панель строится под сервер, где
    # она публикуется, а обработка нажатий резолвит категории по серверу интеракции.
    return feedback_categories.load_categories(guild_id)


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
            # Регистрируем панель-View для каждого сервера с настроенными категориями
            # (custom_id вида feedback_open:<key>); коллбэк резолвит категорию по
            # серверу интеракции, поэтому пересечение ключей между серверами безопасно.
            for guild in self.bot.guilds:
                if get_feedback_categories(guild.id):
                    self.bot.add_view(FeedbackView(self.bot, guild.id))
            await self.restore_feedback_views()
            self.bot._feedback_views_loaded = True

    async def restore_feedback_views(self):
        for guild in self.bot.guilds:
            cases = settings_db.get(guild.id, "feedback_cases", {})
            for case_id, case_data in cases.items():
                if case_data.get("status") != "pending":
                    continue
                message_id = case_data.get("decision_message_id")
                submitter_id = case_data.get("submitter_id")
                category_key = case_data.get("category_key")
                if not message_id or not submitter_id or not category_key:
                    continue
                self.bot.add_view(
                    FeedbackDecisionView(
                        self.bot, case_id, submitter_id, category_key, guild.id
                    ),
                    message_id=message_id,
                )

    @feedback_panel_group.command(name="send", description="Опубликовать панель обратной связи")
    @app_commands.describe(channel="Канал для публикации панели")
    async def feedback_panel_send(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel] = None,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        target_channel = channel or interaction.channel
        if not isinstance(target_channel, discord.TextChannel):
            await interaction.response.send_message(
                i18n.t("feedback.need_text_channel", lang), ephemeral=True
            )
            return

        await interaction.response.send_message(i18n.t("feedback.panel_published", lang), ephemeral=True)
        await feedback_core.publish_feedback_panel(
            self.bot,
            target_channel,
            published_by_id=interaction.user.id,
            published_by_mention=interaction.user.mention,
        )


class FeedbackView(discord.ui.View):
    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        categories = get_feedback_categories(guild_id)

        for category_key, config in categories.items():
            button = discord.ui.Button(
                label=config["button_label"],
                style=discord.ButtonStyle.secondary,
                custom_id=f"feedback_open:{category_key}",
                row=0,
            )

            async def callback(interaction: discord.Interaction, ck=category_key):
                # Категорию берём по серверу интеракции, а не по серверу публикации:
                # один и тот же процесс обслуживает много серверов.
                await interaction.response.send_modal(FeedbackModal(self.bot, interaction.guild_id, ck))

            button.callback = callback
            self.add_item(button)


class FeedbackModal(discord.ui.Modal):
    def __init__(self, bot, guild_id: int, category_key: str):
        self.bot = bot
        self.guild_id = guild_id
        self.category_key = category_key
        config = get_feedback_categories(guild_id)[category_key]
        super().__init__(title=config["modal_title"], timeout=None)

        self.field_keys = []
        for field in config["fields"]:
            style = discord.TextStyle.short if field["style"] == "short" else discord.TextStyle.paragraph
            input_item = discord.ui.TextInput(
                label=field["label"],
                style=style,
                required=field["required"],
                max_length=field["max_length"],
            )
            self.add_item(input_item)
            self.field_keys.append(field["key"])

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(self.guild_id)
        answers = {}
        for key, child in zip(self.field_keys, self.children):
            if isinstance(child, discord.ui.TextInput):
                answers[key] = (child.value or "").strip() or "—"

        try:
            await create_feedback_case(interaction, self.bot, self.category_key, answers)
        except Exception as exc:
            logger.error("Ошибка при создании обращения: %s", exc, exc_info=True)
            embed = discord.Embed(
                title=i18n.t("feedback.error_create_title", lang),
                description=i18n.t(
                    "feedback.error_create_body",
                    lang,
                    category=get_feedback_categories(self.guild_id)[self.category_key]["title"],
                    mention=interaction.user.mention,
                    user_id=interaction.user.id,
                    error=exc,
                ),
                color=embed_style.DANGER,
                timestamp=self.bot.utcnow(),
            )
            await self.bot.send_log(interaction.guild.id, embed)
            if interaction.response.is_done():
                await interaction.followup.send(i18n.t("feedback.create_failed", lang), ephemeral=True)
            else:
                await interaction.response.send_message(i18n.t("feedback.create_failed", lang), ephemeral=True)


class FeedbackDecisionView(discord.ui.View):
    def __init__(
        self,
        bot,
        case_id: str,
        submitter_id: int,
        category_key: str,
        guild_id: int,
        disabled: bool = False,
    ):
        super().__init__(timeout=None)
        self.bot = bot
        self.case_id = case_id
        self.submitter_id = submitter_id
        self.category_key = category_key
        self.guild_id = guild_id
        lang = i18n.lang_for(guild_id)

        approve_btn = discord.ui.Button(
            label=i18n.t("feedback.btn_approve", lang),
            style=discord.ButtonStyle.success,
            custom_id=f"feedback_accept:{case_id}",
            disabled=disabled,
        )
        reject_btn = discord.ui.Button(
            label=i18n.t("feedback.btn_reject", lang),
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

async def get_next_case_id(bot, guild_id: int, prefix: str) -> str:
    counters = settings_db.get(guild_id, "feedback_counters", {})
    current = int(counters.get(prefix, 0)) + 1
    counters[prefix] = current
    settings_db.put(guild_id, "feedback_counters", counters)
    return f"{prefix}-{current:04d}"


def build_mentions(config: dict, lang: str) -> str:
    parts = [f"<@&{r_id}>" for r_id in config["review_role_ids"]]
    parts.extend(f"<@{u_id}>" for u_id in config.get("review_user_ids", []))
    return " ".join(parts).strip() or i18n.t("feedback.no_mentions", lang)


async def add_reviewers(thread: discord.Thread, guild: discord.Guild, config: dict):
    added_ids = set()
    for role_id in config["review_role_ids"]:
        role = guild.get_role(int(role_id))
        if not role:
            continue
        for member in role.members:
            if not member.bot and member.id not in added_ids:
                try:
                    await thread.add_user(member)
                    added_ids.add(member.id)
                except Exception as e:
                    logger.debug("Не удалось добавить %s в тред: %s", member.id, e)

    for user_id in config.get("review_user_ids", []):
        member = guild.get_member(int(user_id))
        if member and not member.bot and member.id not in added_ids:
            try:
                await thread.add_user(member)
                added_ids.add(member.id)
            except Exception as e:
                logger.debug("Не удалось добавить %s в тред: %s", member.id, e)


async def create_feedback_case(interaction: discord.Interaction, bot, category_key: str, answers: dict):
    lang = i18n.lang_for(interaction.guild.id)
    config = get_feedback_categories(interaction.guild.id)[category_key]
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    parent_channel = bot.get_channel(int(config["channel_id"]))
    if not isinstance(parent_channel, discord.TextChannel):
        await interaction.followup.send(i18n.t("feedback.channel_not_found", lang), ephemeral=True)
        return

    case_id = await get_next_case_id(bot, interaction.guild.id, config["case_prefix"])
    summary_val = answers.get(config["mini_summary_key"], "—")

    mini_embed = discord.Embed(
        title=i18n.t(
            "feedback.case_title_public",
            lang,
            case_title=config["case_title"],
            case_id=case_id,
        ),
        color=embed_style.INFO,
        timestamp=bot.utcnow(),
    )
    mini_embed.add_field(
        name=i18n.t("feedback.field.submitter", lang),
        value=interaction.user.mention,
        inline=True,
    )
    mini_embed.add_field(
        name=i18n.t("feedback.field.status", lang),
        value=i18n.t("feedback.status.pending", lang),
        inline=True,
    )
    mini_embed.add_field(
        name=i18n.t("feedback.field.summary", lang),
        value=summary_val[:1024],
        inline=False,
    )
    mini_embed.set_footer(
        text=i18n.t("feedback.field.footer_user_id", lang, user_id=interaction.user.id)
    )

    public_message = await parent_channel.send(embed=mini_embed)

    thread = await parent_channel.create_thread(
        name=f"{config['thread_name']}-{case_id.lower()}",
        type=discord.ChannelType.private_thread,
        invitable=False,
        auto_archive_duration=1440,
        reason=i18n.t("feedback.thread_reason", lang, case_id=case_id),
    )
    await add_reviewers(thread, interaction.guild, config)

    mentions = build_mentions(config, lang)
    try:
        await thread.send(
            content=mentions,
            allowed_mentions=discord.AllowedMentions(roles=True, users=True, everyone=False),
        )
    except Exception as e:
        logger.warning("Не удалось отправить упоминания в тред %s: %s", thread.id, e)

    full_embed = discord.Embed(
        title=i18n.t("feedback.case_title_internal", lang, case_id=case_id),
        color=embed_style.WARN,
        timestamp=bot.utcnow(),
    )
    full_embed.add_field(
        name=i18n.t("feedback.field.submitter", lang),
        value=f"{interaction.user.mention} (`{interaction.user.id}`)",
        inline=False,
    )
    full_embed.add_field(
        name=i18n.t("feedback.field.public_message", lang),
        value=f"[{i18n.t('feedback.link.open', lang)}]({public_message.jump_url})",
        inline=False,
    )
    for field in config["fields"]:
        val = answers.get(field["key"], "—")
        full_embed.add_field(name=field["label"], value=val[:1024] if val else "—", inline=False)
    full_embed.add_field(
        name=i18n.t("feedback.field.status", lang),
        value=i18n.t("feedback.status.awaiting_decision", lang),
        inline=False,
    )
    full_embed.set_footer(text=i18n.t("feedback.field.footer_staff_only", lang))

    decision_view = FeedbackDecisionView(
        bot, case_id, interaction.user.id, category_key, interaction.guild.id
    )
    decision_message = await thread.send(embed=full_embed, view=decision_view)

    cases = settings_db.get(interaction.guild.id, "feedback_cases", {})
    cases[case_id] = {
        "case_id": case_id,
        "category_key": category_key,
        "submitter_id": interaction.user.id,
        "public_channel_id": parent_channel.id,
        "public_message_id": public_message.id,
        "thread_id": thread.id,
        "decision_message_id": decision_message.id,
        "status": "pending",
        "created_at": bot.utcnow().isoformat(),
        "answers": answers,
    }
    settings_db.put(interaction.guild.id, "feedback_cases", cases)

    log_embed = discord.Embed(
        title=i18n.t("feedback.log.new_case", lang),
        description=i18n.t(
            "feedback.log.new_case_body",
            lang,
            case_id=case_id,
            mention=interaction.user.mention,
            user_id=interaction.user.id,
            channel_id=parent_channel.id,
            thread_id=thread.id,
            mentions=mentions,
        ),
        color=embed_style.INFO,
        timestamp=bot.utcnow(),
    )
    await bot.send_log(interaction.guild.id, log_embed)

    await interaction.followup.send(
        i18n.t("feedback.case_registered", lang, case_id=case_id),
        ephemeral=True,
    )


async def close_case(interaction: discord.Interaction, bot, case_id: str, approved: bool):
    lang = i18n.lang_for(interaction.guild_id)
    if not interaction.response.is_done():
        await interaction.response.defer(ephemeral=True)

    try:
        result = await feedback_core.decide_case(
            bot,
            interaction.guild,
            case_id,
            approved,
            decided_by_id=interaction.user.id,
            decided_by_mention=interaction.user.mention,
        )
        if not result["ok"]:
            if result["error"] == "category_deleted":
                await interaction.followup.send(i18n.t("feedback.category_deleted", lang), ephemeral=True)
            else:
                await interaction.followup.send(i18n.t("feedback.case_not_found", lang), ephemeral=True)
    except Exception as e:
        logger.error("Ошибка при закрытии обращения %s: %s", case_id, e)
        await interaction.followup.send(i18n.t("feedback.close_error", lang), ephemeral=True)


async def setup(bot):
    cog = FeedbackMenu(bot)
    slash_registry.register_feedback(cog)
    await bot.add_cog(cog)
