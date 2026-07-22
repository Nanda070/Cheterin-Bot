"""Ког «Сборы на поставку» (портировано из ChetSupply, функционал расширен).

Слэш-команда /реаки-поставка создаёт сбор с кнопками участия. Сборы хранятся
per-guild в settings_db и восстанавливаются после перезапуска бота: таймеры
пересоздаются, кнопки продолжают работать (persistent view).
"""

import asyncio
import logging
import os

import discord
from discord import app_commands
from discord.ext import commands

import bot_config
import i18n
import slash_registry
import supply_core

logger = logging.getLogger("supply")


def _main_guild_id() -> int:
    return int(os.getenv("GUILD_ID", "0") or 0)


def _config_int(key: str) -> int:
    raw = bot_config.get(_main_guild_id(), key)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def get_reminder_minutes() -> int:
    raw = bot_config.get(_main_guild_id(), "SUPPLY_REMINDER_MINUTES")
    try:
        value = int(raw)
        return value if value > 0 else 0
    except (TypeError, ValueError):
        return 10


async def send_dev_log(
    bot: commands.Bot,
    title: str,
    description: str,
    color: discord.Color,
):
    channel_id = _config_int("SUPPLY_LOG_CHANNEL_ID") or _config_int("LOG_CHANNEL_ID")
    channel = bot.get_channel(channel_id)
    if channel:
        now = supply_core.now_msk().strftime('%Y-%m-%d %H:%M:%S')
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text=now)
        try:
            await channel.send(embed=embed, silent=True)
        except discord.HTTPException:
            pass


def generate_embed(supply: dict, lang: str) -> discord.Embed:
    unix_time = supply["target_ts"]
    is_closed = supply["status"] != "active"

    if supply["status"] == "cancelled":
        color = 0x2B2D31
        title = i18n.t("supply.embed.cancelled_title", lang)
        timer_text = i18n.t("supply.embed.cancelled_timer", lang)
    elif is_closed:
        color = 0x2B2D31
        title = i18n.t("supply.embed.closed_title", lang)
        timer_text = i18n.t("supply.embed.expired_timer", lang)
    else:
        color = 0x5865F2
        title = i18n.t("supply.embed.active_title", lang)
        timer_text = f"<t:{unix_time}:R>"

    embed = discord.Embed(title=title, color=color)
    embed.add_field(
        name=i18n.t("supply.embed.initiator", lang),
        value=f"<@{supply['initiator_id']}>",
        inline=True,
    )
    embed.add_field(
        name=i18n.t("supply.embed.opponent", lang),
        value=f"**{supply['opponent']}**",
        inline=True,
    )
    embed.add_field(
        name=i18n.t("supply.embed.start_time", lang),
        value=i18n.t(
            "supply.embed.start_time_value",
            lang,
            time=supply["time_str"],
            timer=timer_text,
        ),
        inline=False,
    )

    voice_channel_id = _config_int("SUPPLY_VOICE_CHANNEL_ID")
    if voice_channel_id:
        embed.add_field(
            name=i18n.t("supply.embed.voice_channel", lang),
            value=f"<#{voice_channel_id}>",
            inline=False,
        )

    participants = supply["participants"]
    if participants:
        users_list = "\n".join([f"`{i+1}.` <@{uid}>" for i, uid in enumerate(participants)])
    else:
        users_list = i18n.t("supply.embed.empty_list", lang)

    if is_closed:
        users_list = f"~~{users_list.replace('~~', '')}~~"

    embed.add_field(
        name=i18n.t(
            "supply.embed.participants",
            lang,
            current=len(participants),
            limit=supply["limit"],
        ),
        value=users_list,
        inline=False,
    )

    reserve = supply.get("reserve", [])
    if reserve:
        reserve_list = "\n".join([f"`{i+1}.` <@{uid}>" for i, uid in enumerate(reserve)])
        if is_closed:
            reserve_list = f"~~{reserve_list.replace('~~', '')}~~"
        embed.add_field(
            name=i18n.t("supply.embed.reserve", lang, count=len(reserve)),
            value=reserve_list,
            inline=False,
        )

    reminder = get_reminder_minutes()
    if not is_closed and reminder:
        embed.set_footer(text=i18n.t("supply.embed.reminder_footer", lang, minutes=reminder))
    return embed


class SupplyView(discord.ui.View):
    """Persistent view: кнопки работают и после перезапуска бота."""

    def __init__(self, cog: "SupplyCog", lang: str | None = None):
        super().__init__(timeout=None)
        self.cog = cog
        self.lang = lang or i18n.DEFAULT_LANGUAGE
        self._set_button_labels()

    def _set_button_labels(self, lang: str | None = None) -> None:
        lang = lang or self.lang
        self.lang = lang
        for child in self.children:
            if not isinstance(child, discord.ui.Button):
                continue
            if child.custom_id == "supply:join":
                child.label = i18n.t("supply.button.join", lang)
            elif child.custom_id == "supply:leave":
                child.label = i18n.t("supply.button.leave", lang)
            elif child.custom_id == "supply:close":
                child.label = i18n.t("supply.button.close", lang)

    def _get_supply(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None or interaction.guild_id is None:
            return None
        return supply_core.get_supply_by_message(interaction.guild_id, interaction.message.id)

    @discord.ui.button(label="Join", style=discord.ButtonStyle.green, custom_id="supply:join")
    async def join_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        self._set_button_labels(lang)
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message(
                i18n.t("supply.not_found", lang), ephemeral=True,
            )

        result = supply_core.join_supply(interaction.guild_id, supply["id"], interaction.user.id)
        if result == "already":
            return await interaction.response.send_message(
                i18n.t("supply.already_joined", lang), ephemeral=True,
            )
        if result == "closed":
            return await interaction.response.send_message(
                i18n.t("supply.closed", lang), ephemeral=True,
            )
        if result == "not_found":
            return await interaction.response.send_message(
                i18n.t("supply.not_found", lang), ephemeral=True,
            )

        supply = supply_core.get_supply(interaction.guild_id, supply["id"])
        await interaction.response.edit_message(embed=generate_embed(supply, lang), view=self)

        if result == "reserve":
            await interaction.followup.send(
                i18n.t("supply.reserve_joined", lang), ephemeral=True,
            )
            await send_dev_log(
                self.cog.bot,
                i18n.t("supply.log.reserve", lang),
                i18n.t(
                    "supply.log.reserve_body",
                    lang,
                    user=interaction.user.id,
                    initiator=supply["initiator_id"],
                    count=len(supply["reserve"]),
                ),
                discord.Color.gold(),
            )
        else:
            await send_dev_log(
                self.cog.bot,
                i18n.t("supply.log.join", lang),
                i18n.t(
                    "supply.log.join_body",
                    lang,
                    user=interaction.user.id,
                    initiator=supply["initiator_id"],
                    current=len(supply["participants"]),
                    limit=supply["limit"],
                ),
                discord.Color.green(),
            )

    @discord.ui.button(label="Withdraw", style=discord.ButtonStyle.red, custom_id="supply:leave")
    async def leave_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        self._set_button_labels(lang)
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message(
                i18n.t("supply.not_found", lang), ephemeral=True,
            )

        result, promoted = supply_core.leave_supply(interaction.guild_id, supply["id"], interaction.user.id)
        if result == "not_in_list":
            return await interaction.response.send_message(
                i18n.t("supply.not_in_list", lang), ephemeral=True,
            )
        if result in ("closed", "not_found"):
            return await interaction.response.send_message(
                i18n.t("supply.closed", lang), ephemeral=True,
            )

        supply = supply_core.get_supply(interaction.guild_id, supply["id"])
        await interaction.response.edit_message(embed=generate_embed(supply, lang), view=self)
        await send_dev_log(
            self.cog.bot,
            i18n.t("supply.log.leave", lang),
            i18n.t(
                "supply.log.leave_body",
                lang,
                user=interaction.user.id,
                initiator=supply["initiator_id"],
                current=len(supply["participants"]),
                limit=supply["limit"],
            ),
            discord.Color.red(),
        )

        if promoted:
            guild = interaction.guild
            member = guild.get_member(int(promoted)) if guild else None
            if member:
                try:
                    await member.send(i18n.t(
                        "supply.promoted_dm",
                        lang,
                        opponent=supply["opponent"],
                        time=supply["time_str"],
                    ))
                except discord.Forbidden:
                    pass
            await send_dev_log(
                self.cog.bot,
                i18n.t("supply.log.promoted", lang),
                i18n.t(
                    "supply.log.promoted_body",
                    lang,
                    user=promoted,
                    initiator=supply["initiator_id"],
                ),
                discord.Color.green(),
            )

    @discord.ui.button(label="Close signup", style=discord.ButtonStyle.grey, custom_id="supply:close")
    async def close_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        lang = i18n.lang_for(interaction.guild_id)
        self._set_button_labels(lang)
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message(
                i18n.t("supply.not_found", lang), ephemeral=True,
            )

        is_initiator = str(interaction.user.id) == supply["initiator_id"]
        is_moderator = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_guild
        if not (is_initiator or is_moderator):
            return await interaction.response.send_message(
                i18n.t("supply.close_forbidden", lang), ephemeral=True,
            )

        await interaction.response.defer()
        await self.cog.finalize_supply(
            interaction.guild_id,
            supply["id"],
            reason=i18n.t("supply.finalize.manual", lang),
            lang=lang,
        )


class SupplyCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._timers: dict[str, asyncio.Task] = {}
        self._recovered = False
        self.view = SupplyView(self)

    async def cog_load(self):
        self.bot.add_view(self.view)

    def cog_unload(self):
        for task in self._timers.values():
            task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        await self.recover_supplies()

    async def recover_supplies(self):
        recovered = 0
        for guild in self.bot.guilds:
            lang = i18n.lang_for(guild.id)
            for supply in supply_core.list_active(guild.id):
                self.schedule_supply(supply)
                await self._refresh_supply_message_labels(guild.id, supply, lang)
                recovered += 1
        if recovered:
            lang = i18n.lang_for(self.bot.guilds[0].id if self.bot.guilds else None)
            await send_dev_log(
                self.bot,
                i18n.t("supply.log.recovery", lang),
                i18n.t("supply.log.recovery_body", lang, count=recovered),
                discord.Color.blue(),
            )

    async def _refresh_supply_message_labels(self, guild_id: int, supply: dict, lang: str) -> None:
        if not supply.get("message_id") or not supply.get("channel_id"):
            return
        channel = self.bot.get_channel(int(supply["channel_id"]))
        if channel is None:
            return
        try:
            message = await channel.fetch_message(int(supply["message_id"]))
        except discord.HTTPException:
            return
        self.view._set_button_labels(lang)
        try:
            await message.edit(embed=generate_embed(supply, lang), view=self.view)
        except discord.HTTPException:
            pass

    def schedule_supply(self, supply: dict):
        guild_id = int(supply["guild_id"])
        key = (guild_id, supply["id"])
        old = self._timers.pop(key, None)
        if old:
            old.cancel()
        self._timers[key] = self.bot.loop.create_task(self._run_supply_timer(guild_id, supply["id"]))

    async def _run_supply_timer(self, guild_id: int, supply_id: str):
        try:
            supply = supply_core.get_supply(guild_id, supply_id)
            if supply is None or supply["status"] != "active":
                return

            reminder_minutes = get_reminder_minutes()
            now_ts = int(supply_core.now_msk().timestamp())
            reminder_ts = supply["target_ts"] - reminder_minutes * 60

            if reminder_minutes and not supply.get("reminder_sent") and reminder_ts > now_ts:
                await asyncio.sleep(reminder_ts - now_ts)
                await self._send_reminder(guild_id, supply_id)

            supply = supply_core.get_supply(guild_id, supply_id)
            if supply is None or supply["status"] != "active":
                return
            now_ts = int(supply_core.now_msk().timestamp())
            if supply["target_ts"] > now_ts:
                await asyncio.sleep(supply["target_ts"] - now_ts)

            lang = i18n.lang_for(guild_id)
            await self.finalize_supply(
                guild_id,
                supply_id,
                reason=i18n.t("supply.finalize.timer", lang),
                lang=lang,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Supply timer failed: %s", supply_id)

    async def _send_reminder(self, guild_id: int, supply_id: str):
        lang = i18n.lang_for(guild_id)
        supply = supply_core.get_supply(guild_id, supply_id)
        if supply is None or supply["status"] != "active" or supply.get("reminder_sent"):
            return
        supply_core.update_supply(guild_id, supply_id, reminder_sent=True)

        if not supply["participants"]:
            return

        channel = self.bot.get_channel(int(supply["channel_id"] or 0))
        if channel is None:
            return

        mentions = " ".join(f"<@{uid}>" for uid in supply["participants"])
        voice_channel_id = _config_int("SUPPLY_VOICE_CHANNEL_ID")
        voice_part = (
            i18n.t("supply.reminder_voice", lang, channel_id=voice_channel_id)
            if voice_channel_id else ""
        )
        try:
            await channel.send(i18n.t(
                "supply.reminder",
                lang,
                opponent=supply["opponent"],
                ts=supply["target_ts"],
                voice_part=voice_part,
                mentions=mentions,
            ))
        except discord.HTTPException:
            pass
        await send_dev_log(
            self.bot,
            i18n.t("supply.log.reminder", lang),
            i18n.t("supply.log.reminder_body", lang, initiator=supply["initiator_id"]),
            discord.Color.blue(),
        )

    async def finalize_supply(
        self,
        guild_id: int,
        supply_id: str,
        reason: str,
        status: str = "finished",
        *,
        lang: str | None = None,
    ) -> bool:
        lang = lang or i18n.lang_for(guild_id)
        supply = supply_core.close_supply(guild_id, supply_id, status=status)
        if supply is None:
            return False

        task = self._timers.pop((guild_id, supply_id), None)
        if task and task is not asyncio.current_task():
            task.cancel()

        channel = self.bot.get_channel(int(supply["channel_id"] or 0))
        message = None
        if channel is not None and supply["message_id"]:
            try:
                message = await channel.fetch_message(int(supply["message_id"]))
            except discord.HTTPException:
                message = None

        view = discord.ui.View(timeout=None)
        try:
            if message is not None:
                await message.edit(embed=generate_embed(supply, lang), view=view)

            if status == "finished" and channel is not None:
                if supply["participants"]:
                    mentions = "\n".join([f"- <@{uid}>" for uid in supply["participants"]])
                    final_text = i18n.t("supply.final_list", lang, mentions=mentions)
                else:
                    final_text = i18n.t("supply.final_empty", lang)
                await channel.send(content=final_text)

            title = (
                i18n.t("supply.log.finished", lang)
                if status == "finished"
                else i18n.t("supply.log.cancelled", lang)
            )
            await send_dev_log(
                self.bot,
                title,
                i18n.t(
                    "supply.log.close_body",
                    lang,
                    initiator=supply["initiator_id"],
                    reason=reason,
                    count=len(supply["participants"]),
                ),
                discord.Color.gold(),
            )
        except discord.HTTPException as e:
            await send_dev_log(
                self.bot,
                i18n.t("supply.log.close_error", lang),
                i18n.t(
                    "supply.log.close_error_body",
                    lang,
                    initiator=supply["initiator_id"],
                    error=e,
                ),
                discord.Color.dark_theme(),
            )
        return True

    async def publish_supply(
        self,
        guild_id: int,
        channel: discord.abc.Messageable,
        initiator_id: int,
        opponent: str,
        limit: int,
        time_str: str,
    ) -> dict:
        lang = i18n.lang_for(guild_id)
        supply = supply_core.create_supply(guild_id, initiator_id, opponent, limit, time_str)

        role_id = _config_int("SUPPLY_ROLE_ID")
        content = f"<@&{role_id}>" if role_id else None
        allowed = discord.AllowedMentions(roles=[discord.Object(id=role_id)]) if role_id else discord.AllowedMentions.none()

        self.view._set_button_labels(lang)
        message = await channel.send(
            content=content,
            embed=generate_embed(supply, lang),
            view=self.view,
            allowed_mentions=allowed,
        )
        supply = supply_core.update_supply(
            guild_id, supply["id"],
            channel_id=str(message.channel.id),
            message_id=str(message.id),
        )
        self.schedule_supply(supply)

        await send_dev_log(
            self.bot,
            i18n.t("supply.log.new", lang),
            i18n.t(
                "supply.log.new_body",
                lang,
                initiator=initiator_id,
                opponent=opponent,
                limit=limit,
                time=time_str,
            ),
            discord.Color.blue(),
        )
        return supply

    @app_commands.command(name="реаки-поставка", description="Создать сбор на поставку")
    @app_commands.describe(
        против="Фракция/цель, против которой идет поставка",
        лимит="Максимальное количество участников",
        время="Время сбора в формате ЧЧ:ММ (МСК, например 15:10)",
    )
    async def supply_collect(self, interaction: discord.Interaction, против: str, лимит: int, время: str):
        lang = i18n.lang_for(interaction.guild_id)
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            await send_dev_log(
                self.bot,
                i18n.t("supply.log.timeout", lang),
                i18n.t("supply.log.timeout_body", lang, user=interaction.user.id),
                discord.Color.dark_theme(),
            )
            return

        if not supply_core.is_valid_time(время):
            await send_dev_log(
                self.bot,
                i18n.t("supply.log.validation", lang),
                i18n.t("supply.log.validation_time", lang, user=interaction.user.id, time=время),
                discord.Color.red(),
            )
            return await interaction.followup.send(
                i18n.t("supply.error.time_format", lang), ephemeral=True,
            )

        if not 1 <= лимит <= 99:
            return await interaction.followup.send(
                i18n.t("supply.error.limit", lang), ephemeral=True,
            )

        try:
            supply = await self.publish_supply(
                interaction.guild_id, interaction.channel, interaction.user.id, против, лимит, время,
            )
            await interaction.followup.send(
                i18n.t("supply.created", lang, id=supply["id"]), ephemeral=True,
            )
        except Exception as e:
            await send_dev_log(
                self.bot,
                i18n.t("supply.log.critical", lang),
                i18n.t("supply.log.critical_body", lang, error=str(e)),
                discord.Color.dark_red(),
            )


async def setup(bot: commands.Bot):
    cog = SupplyCog(bot)
    slash_registry.register_supply(cog)
    await bot.add_cog(cog)
