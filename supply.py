"""Ког «Сборы на поставку» (портировано из ChetSupply, функционал расширен).

Слэш-команда /реаки-поставка создаёт сбор с кнопками участия. Сборы хранятся
per-guild в settings_db и восстанавливаются после перезапуска бота: таймеры
пересоздаются, кнопки продолжают работать (persistent view).
"""

import asyncio
import logging
import os
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

import bot_config
import supply_core

logger = logging.getLogger("supply")


def _main_guild_id() -> int:
    """Данные сборов уже per-guild (settings_db, Фаза 2.2б). Конфиг когa (каналы/роли/
    напоминания) пока читается с мейн-сервера через GUILD_ID — перевод конфига на
    guild_id события относится к Фазе 2.4 MULTIGUILD_PLAN.md."""
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


async def send_dev_log(bot: commands.Bot, title: str, description: str, color: discord.Color):
    """Тихая отправка логов через Embed."""
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


def generate_embed(supply: dict) -> discord.Embed:
    unix_time = supply["target_ts"]
    is_closed = supply["status"] != "active"

    if supply["status"] == "cancelled":
        color = 0x2B2D31
        title = "🚫 Сбор отменён"
        timer_text = "Отменено"
    elif is_closed:
        color = 0x2B2D31
        title = "🛑 Сбор закрыт"
        timer_text = "Истекло"
    else:
        color = 0x5865F2
        title = "📦 Сбор на поставку"
        timer_text = f"<t:{unix_time}:R>"

    embed = discord.Embed(title=title, color=color)
    embed.add_field(name="Инициатор:", value=f"<@{supply['initiator_id']}>", inline=True)
    embed.add_field(name="Против:", value=f"**{supply['opponent']}**", inline=True)
    embed.add_field(name="Время Начала:", value=f"**{supply['time_str']}** (МСК) ➔ {timer_text}", inline=False)

    voice_channel_id = _config_int("SUPPLY_VOICE_CHANNEL_ID")
    if voice_channel_id:
        embed.add_field(name="Голосовой Канал:", value=f"<#{voice_channel_id}>", inline=False)

    participants = supply["participants"]
    if participants:
        users_list = "\n".join([f"`{i+1}.` <@{uid}>" for i, uid in enumerate(participants)])
    else:
        users_list = "—"

    if is_closed:
        users_list = f"~~{users_list.replace('~~', '')}~~"

    embed.add_field(name=f"Участники [{len(participants)}/{supply['limit']}]", value=users_list, inline=False)

    reserve = supply.get("reserve", [])
    if reserve:
        reserve_list = "\n".join([f"`{i+1}.` <@{uid}>" for i, uid in enumerate(reserve)])
        if is_closed:
            reserve_list = f"~~{reserve_list.replace('~~', '')}~~"
        embed.add_field(name=f"Резерв [{len(reserve)}]", value=reserve_list, inline=False)

    reminder = get_reminder_minutes()
    if not is_closed and reminder:
        embed.set_footer(text=f"Напоминание участникам за {reminder} мин до начала")
    return embed


class SupplyView(discord.ui.View):
    """Persistent view: кнопки работают и после перезапуска бота."""

    def __init__(self, cog: "SupplyCog"):
        super().__init__(timeout=None)
        self.cog = cog

    def _get_supply(self, interaction: discord.Interaction) -> dict | None:
        if interaction.message is None or interaction.guild_id is None:
            return None
        return supply_core.get_supply_by_message(interaction.guild_id, interaction.message.id)

    @discord.ui.button(label="Участвовать", style=discord.ButtonStyle.green, custom_id="supply:join")
    async def join_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message("Сбор не найден.", ephemeral=True)

        result = supply_core.join_supply(interaction.guild_id, supply["id"], interaction.user.id)
        if result == "already":
            return await interaction.response.send_message("Ты уже в списке.", ephemeral=True)
        if result == "closed":
            return await interaction.response.send_message("Сбор уже закрыт.", ephemeral=True)
        if result == "not_found":
            return await interaction.response.send_message("Сбор не найден.", ephemeral=True)

        supply = supply_core.get_supply(interaction.guild_id, supply["id"])
        await interaction.response.edit_message(embed=generate_embed(supply), view=self)

        if result == "reserve":
            await interaction.followup.send(
                "Основной состав заполнен — ты добавлен в **резерв**. "
                "Если кто-то отзовёт участие, ты автоматически займёшь его место.",
                ephemeral=True,
            )
            await send_dev_log(
                self.cog.bot,
                "🟡 Резерв",
                f"<@{interaction.user.id}> добавлен в резерв сбора.\n**Инициатор:** <@{supply['initiator_id']}>\n**Резерв:** {len(supply['reserve'])}",
                discord.Color.gold(),
            )
        else:
            await send_dev_log(
                self.cog.bot,
                "🟢 Участие",
                f"<@{interaction.user.id}> записался на поставку.\n**Инициатор:** <@{supply['initiator_id']}>\n**Мест:** {len(supply['participants'])}/{supply['limit']}",
                discord.Color.green(),
            )

    @discord.ui.button(label="Отозвать", style=discord.ButtonStyle.red, custom_id="supply:leave")
    async def leave_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message("Сбор не найден.", ephemeral=True)

        result, promoted = supply_core.leave_supply(interaction.guild_id, supply["id"], interaction.user.id)
        if result == "not_in_list":
            return await interaction.response.send_message("Тебя нет в списке.", ephemeral=True)
        if result in ("closed", "not_found"):
            return await interaction.response.send_message("Сбор уже закрыт.", ephemeral=True)

        supply = supply_core.get_supply(interaction.guild_id, supply["id"])
        await interaction.response.edit_message(embed=generate_embed(supply), view=self)
        await send_dev_log(
            self.cog.bot,
            "🔴 Отзыв",
            f"<@{interaction.user.id}> отозвал участие.\n**Инициатор:** <@{supply['initiator_id']}>\n**Мест:** {len(supply['participants'])}/{supply['limit']}",
            discord.Color.red(),
        )

        if promoted:
            guild = interaction.guild
            member = guild.get_member(int(promoted)) if guild else None
            if member:
                try:
                    await member.send(
                        f"Место освободилось — ты переведён из резерва в основной состав сбора на поставку "
                        f"против **{supply['opponent']}** ({supply['time_str']} МСК)."
                    )
                except discord.Forbidden:
                    pass
            await send_dev_log(
                self.cog.bot,
                "🟢 Продвижение из резерва",
                f"<@{promoted}> занял освободившееся место.\n**Инициатор:** <@{supply['initiator_id']}>",
                discord.Color.green(),
            )

    @discord.ui.button(label="Закрыть сбор", style=discord.ButtonStyle.grey, custom_id="supply:close")
    async def close_btn(self, interaction: discord.Interaction, _button: discord.ui.Button):
        supply = self._get_supply(interaction)
        if supply is None:
            return await interaction.response.send_message("Сбор не найден.", ephemeral=True)

        is_initiator = str(interaction.user.id) == supply["initiator_id"]
        is_moderator = isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_guild
        if not (is_initiator or is_moderator):
            return await interaction.response.send_message("Закрыть сбор может только инициатор или модератор.", ephemeral=True)

        await interaction.response.defer()
        await self.cog.finalize_supply(interaction.guild_id, supply["id"], reason="закрыт досрочно")


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
        """Пересоздаёт таймеры активных сборов после перезапуска (по всем серверам)."""
        recovered = 0
        for guild in self.bot.guilds:
            for supply in supply_core.list_active(guild.id):
                self.schedule_supply(supply)
                recovered += 1
        if recovered:
            await send_dev_log(
                self.bot,
                "♻️ Восстановление сборов",
                f"После перезапуска восстановлено активных сборов: **{recovered}**.",
                discord.Color.blue(),
            )

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

            await self.finalize_supply(guild_id, supply_id, reason="таймер истёк")
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Supply timer failed: %s", supply_id)

    async def _send_reminder(self, guild_id: int, supply_id: str):
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
        voice_part = f" Сбор в <#{voice_channel_id}>." if voice_channel_id else ""
        try:
            await channel.send(
                f"⏰ **Напоминание:** поставка против **{supply['opponent']}** начнётся "
                f"<t:{supply['target_ts']}:R>.{voice_part}\n{mentions}"
            )
        except discord.HTTPException:
            pass
        await send_dev_log(
            self.bot,
            "⏰ Напоминание отправлено",
            f"Сбор от <@{supply['initiator_id']}> — участники упомянуты.",
            discord.Color.blue(),
        )

    async def finalize_supply(self, guild_id: int, supply_id: str, reason: str, status: str = "finished") -> bool:
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
                await message.edit(embed=generate_embed(supply), view=view)

            if status == "finished" and channel is not None:
                if supply["participants"]:
                    mentions = "\n".join([f"- <@{uid}>" for uid in supply["participants"]])
                    final_text = f"**Итоговый список на поставку:**\n{mentions}\n================"
                else:
                    final_text = "**Сбор завершен.** Никто не записался.\n================"
                await channel.send(content=final_text)

            title = "🛑 Сбор завершён" if status == "finished" else "🚫 Сбор отменён"
            await send_dev_log(
                self.bot,
                title,
                f"Сбор от <@{supply['initiator_id']}> ({reason}).\n**Итого участников:** {len(supply['participants'])}",
                discord.Color.gold(),
            )
        except discord.HTTPException as e:
            await send_dev_log(
                self.bot,
                "⚠️ Ошибка закрытия",
                f"Не удалось обновить сообщение сбора от <@{supply['initiator_id']}>.\nОшибка: `{e}`",
                discord.Color.dark_theme(),
            )
        return True

    async def publish_supply(self, guild_id: int, channel: discord.abc.Messageable, initiator_id: int, opponent: str, limit: int, time_str: str) -> dict:
        """Создаёт сбор и публикует сообщение с кнопками. Используется командой и дашбордом."""
        supply = supply_core.create_supply(guild_id, initiator_id, opponent, limit, time_str)

        role_id = _config_int("SUPPLY_ROLE_ID")
        content = f"<@&{role_id}>" if role_id else None
        allowed = discord.AllowedMentions(roles=[discord.Object(id=role_id)]) if role_id else discord.AllowedMentions.none()

        message = await channel.send(
            content=content,
            embed=generate_embed(supply),
            view=self.view,
            allowed_mentions=allowed,
        )
        supply = supply_core.update_supply(guild_id, supply["id"], channel_id=str(message.channel.id), message_id=str(message.id))
        self.schedule_supply(supply)

        await send_dev_log(
            self.bot,
            "⚡ Новый сбор на поставку",
            f"**Инициатор:** <@{initiator_id}>\n**Против:** {opponent}\n**Лимит:** {limit}\n**Время:** {time_str} (МСК)",
            discord.Color.blue(),
        )
        return supply

    @app_commands.command(name="реаки-поставка", description="Создать сбор на поставку")
    @app_commands.describe(
        против="Фракция/цель, против которой идет поставка",
        лимит="Максимальное количество участников",
        время="Время сбора в формате ЧЧ:ММ (МСК, например 15:10)"
    )
    async def supply_collect(self, interaction: discord.Interaction, против: str, лимит: int, время: str):
        try:
            await interaction.response.defer()
        except discord.errors.NotFound:
            await send_dev_log(
                self.bot,
                "⚠️ Таймаут ответа",
                f"Вызов от <@{interaction.user.id}> отброшен из-за ошибки 10062.",
                discord.Color.dark_theme(),
            )
            return

        if not supply_core.is_valid_time(время):
            await send_dev_log(
                self.bot,
                "❌ Ошибка валидации",
                f"<@{interaction.user.id}> ввел неверный формат времени: `{время}`.",
                discord.Color.red(),
            )
            return await interaction.followup.send("❌ Ошибка: Формат времени должен быть ЧЧ:ММ (например, 15:10).", ephemeral=True)

        if not 1 <= лимит <= 99:
            return await interaction.followup.send("❌ Ошибка: лимит должен быть от 1 до 99.", ephemeral=True)

        try:
            supply = await self.publish_supply(interaction.guild_id, interaction.channel, interaction.user.id, против, лимит, время)
            await interaction.followup.send(f"Сбор №{supply['id']} создан.", ephemeral=True)
        except Exception as e:
            await send_dev_log(
                self.bot,
                "❌ Критическая ошибка",
                f"Ошибка при отправке сообщения сбора: `{str(e)}`",
                discord.Color.dark_red(),
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(SupplyCog(bot))
