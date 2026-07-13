import asyncio
import json
import os

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, UserSelect

import bot_config
import voice_db as db
import voice_logs as logs
from voice_logs import VCTheme, logger

PANEL_STATE_FILE = "voice_panel.json"


def _config_channel_id(key: str) -> int:
    raw = bot_config.get(key)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def load_panel_state() -> dict:
    if os.path.exists(PANEL_STATE_FILE):
        with open(PANEL_STATE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_panel_state(data: dict) -> None:
    with open(PANEL_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


async def set_open_state(channel: discord.VoiceChannel):
    everyone = channel.guild.default_role
    ow = channel.overwrites_for(everyone)
    ow.view_channel = True
    ow.connect = True
    await channel.set_permissions(everyone, overwrite=ow)
    db.db_update_room_closed(channel.id, False)


async def set_closed_state(channel: discord.VoiceChannel):
    everyone = channel.guild.default_role
    ow = channel.overwrites_for(everyone)
    ow.view_channel = True
    ow.connect = False
    await channel.set_permissions(everyone, overwrite=ow)
    db.db_update_room_closed(channel.id, True)


async def apply_owner_permissions(channel: discord.VoiceChannel, owner: discord.Member):
    ow = channel.overwrites_for(owner)
    ow.view_channel = True
    ow.connect = True
    ow.speak = True
    ow.manage_channels = True
    ow.manage_permissions = True
    ow.move_members = True
    ow.mute_members = False
    ow.deafen_members = False
    await channel.set_permissions(owner, overwrite=ow)


async def remove_owner_permissions(channel: discord.VoiceChannel, old_owner: discord.Member):
    ow = channel.overwrites_for(old_owner)
    ow.manage_channels = False
    ow.manage_permissions = False
    ow.move_members = False
    ow.mute_members = False
    ow.deafen_members = False
    await channel.set_permissions(old_owner, overwrite=ow)


async def set_member_allow(channel: discord.VoiceChannel, member: discord.Member):
    ow = channel.overwrites_for(member)
    ow.view_channel = True
    ow.connect = True
    await channel.set_permissions(member, overwrite=ow)
    db.db_set_access(channel.id, member.id, "allow")


async def set_member_deny(channel: discord.VoiceChannel, member: discord.Member):
    ow = channel.overwrites_for(member)
    ow.view_channel = True
    ow.connect = False
    await channel.set_permissions(member, overwrite=ow)
    db.db_set_access(channel.id, member.id, "deny")


def is_room_owner(user_id: int, channel_id: int) -> bool:
    return db.user_owned_channels.get(user_id) == channel_id


async def safe_followup(interaction: discord.Interaction, text: str):
    if not interaction.response.is_done():
        await interaction.response.send_message(text, ephemeral=True)
    else:
        await interaction.followup.send(text, ephemeral=True)


async def ensure_owner(interaction: discord.Interaction, bot: commands.Bot) -> discord.VoiceChannel | None:
    if not interaction.user.voice or not interaction.user.voice.channel:
        await safe_followup(interaction, "Вы не находитесь в голосовом канале.")
        await logs.log_security(bot, interaction.user, "Попытка использовать управление вне голосового канала.")
        return None

    channel = interaction.user.voice.channel
    if not isinstance(channel, discord.VoiceChannel):
        await safe_followup(interaction, "Это не голосовой канал.")
        await logs.log_security(bot, interaction.user, "Попытка использовать управление вне voice-канала.")
        return None

    room = db.db_get_room(channel.id)
    if not room:
        await safe_followup(interaction, "Эта комната не зарегистрирована как приватная.")
        await logs.log_security(bot, interaction.user, "Попытка управлять незарегистрированной комнатой.", channel)
        return None

    if not is_room_owner(interaction.user.id, channel.id):
        await safe_followup(interaction, "Вы не владелец этой комнаты.")
        await logs.log_security(bot, interaction.user, "Попытка управлять чужой комнатой.", channel)
        return None

    return channel


async def select_member_ephemeral(interaction: discord.Interaction, bot: commands.Bot, placeholder: str) -> discord.Member | None:
    view = View(timeout=30)
    select = UserSelect(placeholder=placeholder, min_values=1, max_values=1, custom_id="vc:user_select")
    view.add_item(select)

    if not interaction.response.is_done():
        await interaction.response.send_message("Выберите участника:", view=view, ephemeral=True)
    else:
        await interaction.followup.send("Выберите участника:", view=view, ephemeral=True)

    def check(i: discord.Interaction):
        return i.user.id == interaction.user.id and i.data and i.data.get("custom_id") == "vc:user_select"

    try:
        result: discord.Interaction = await bot.wait_for("interaction", timeout=30, check=check)
    except asyncio.TimeoutError:
        await interaction.followup.send("Время выбора истекло.", ephemeral=True)
        return None

    user_id = int(result.data["values"][0])
    member = interaction.guild.get_member(user_id) if interaction.guild else None
    await result.response.defer()
    return member


def build_embed() -> discord.Embed:
    embed = discord.Embed(
        title="Управление приватными комнатами",
        description="Нажмите кнопку для выполнения действия.\n_Откроется селектор пользователя или Модульное Окно._",
        color=VCTheme.COLOR
    )
    embed.add_field(
        name="Доступ:",
        value=(f"{VCTheme.EMO['openroom']} • Открыть комнату\n{VCTheme.EMO['lock']} • Закрыть комнату\n"
               f"{VCTheme.EMO['lockuser']} • Разрешить вход\n{VCTheme.EMO['404']} • Запретить вход\n"),
        inline=True
    )
    embed.add_field(
        name="Управление:",
        value=(f"{VCTheme.EMO['name']} • Переименовать\n{VCTheme.EMO['limit']} • Лимит участников\n"
               f"{VCTheme.EMO['owner']} • Передать комнату\n{VCTheme.EMO['kick']} • Выгнать участника\n"),
        inline=True
    )
    embed.add_field(
        name="Голос:",
        value=(f"{VCTheme.EMO['miceoff']} • Запретить говорить всем\n{VCTheme.EMO['mice']} • Разрешить говорить всем\n"),
        inline=False
    )
    thumb = bot_config.get("VOICE_PANEL_THUMB_URL")
    if thumb: embed.set_thumbnail(url=thumb)
    return embed


class RenameModal(Modal, title="Переименование канала"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    new_name = TextInput(label="Новое название", max_length=96)

    async def on_submit(self, interaction: discord.Interaction):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        value = self.new_name.value.strip()
        if not value:
            await interaction.response.send_message("Название не может быть пустым.", ephemeral=True)
            return
        old_name = channel.name
        await channel.edit(name=value)
        db.db_update_room_name(channel.id, value)
        await interaction.response.send_message(f"Название изменено: **{old_name} → {value}**", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, f"Переименовал комнату: {old_name} → {value}", channel, color=VCTheme.SUCCESS)


class SlotsModal(Modal, title="Лимит участников"):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
    slots = TextInput(label="Число мест (0 = без лимита)", max_length=3, placeholder="0-99")

    async def on_submit(self, interaction: discord.Interaction):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        try:
            value = int(self.slots.value.strip())
            if not 0 <= value <= 99: raise ValueError
        except ValueError:
            await interaction.response.send_message("Введите число от 0 до 99.", ephemeral=True)
            return
        await channel.edit(user_limit=value)
        db.db_update_room_limit(channel.id, value)
        await interaction.response.send_message("Лимит снят." if value == 0 else f"Лимит установлен: **{value}**", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, f"Изменил лимит комнаты на {value}", channel, color=VCTheme.SUCCESS)


class ChannelControlView(View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(emoji=VCTheme.EMO["openroom"], label="Открыть", style=discord.ButtonStyle.secondary, custom_id="vc:open", row=0)
    async def open_room(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        await set_open_state(channel)
        await interaction.followup.send("Комната открыта для всех.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Открыл комнату", channel, color=VCTheme.SUCCESS)

    @discord.ui.button(emoji=VCTheme.EMO["lock"], label="Закрыть", style=discord.ButtonStyle.secondary, custom_id="vc:close", row=0)
    async def close_room(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        await set_closed_state(channel)
        await interaction.followup.send("Комната закрыта. Канал виден всем, но вход запрещён.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Закрыл комнату", channel, color=VCTheme.WARN)

    @discord.ui.button(emoji=VCTheme.EMO["lockuser"], label="Разрешить вход", style=discord.ButtonStyle.secondary, custom_id="vc:allow_user", row=0)
    async def allow_user(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(interaction, self.bot, "Кому разрешить вход")
        if not target: return
        if target.bot:
            await interaction.followup.send("Нельзя выдавать доступ боту.", ephemeral=True)
            return await logs.log_security(self.bot, interaction.user, "Попытка выдать доступ боту.", channel)
        await set_member_allow(channel, target)
        await interaction.followup.send(f"{target.mention} теперь может заходить в эту комнату.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Выдал доступ к комнате", channel, target, VCTheme.SUCCESS)

    @discord.ui.button(emoji=VCTheme.EMO["404"], label="Запретить вход", style=discord.ButtonStyle.secondary, custom_id="vc:deny_user", row=0)
    async def deny_user(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(interaction, self.bot, "Кому запретить вход")
        if not target: return
        if target.id == interaction.user.id or target.bot:
            await interaction.followup.send("Неприменимое действие.", ephemeral=True)
            return await logs.log_security(self.bot, interaction.user, "Попытка блокировки себя/бота.", channel)
        await set_member_deny(channel, target)
        if target.voice and target.voice.channel and target.voice.channel.id == channel.id:
            await target.move_to(None)
        await interaction.followup.send(f"{target.mention} больше не сможет заходить в эту комнату.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Запретил вход в комнату", channel, target, VCTheme.ERROR)

    @discord.ui.button(emoji=VCTheme.EMO["name"], label="Переименовать", style=discord.ButtonStyle.secondary, custom_id="vc:rename", row=1)
    async def rename_room(self, interaction: discord.Interaction, _button: Button):
        if await ensure_owner(interaction, self.bot): await interaction.response.send_modal(RenameModal(self.bot))

    @discord.ui.button(emoji=VCTheme.EMO["limit"], label="Лимит", style=discord.ButtonStyle.secondary, custom_id="vc:limit", row=1)
    async def limit_room(self, interaction: discord.Interaction, _button: Button):
        if await ensure_owner(interaction, self.bot): await interaction.response.send_modal(SlotsModal(self.bot))

    @discord.ui.button(emoji=VCTheme.EMO["owner"], label="Передать", style=discord.ButtonStyle.secondary, custom_id="vc:transfer", row=1)
    async def transfer_room(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(interaction, self.bot, "Кому передать комнату")
        if not target: return
        if target.id == interaction.user.id or target.bot or not target.voice or target.voice.channel.id != channel.id:
            await interaction.followup.send("Неприменимое действие или цель вне канала.", ephemeral=True)
            return

        old_owner = interaction.user
        db.user_owned_channels.pop(old_owner.id, None)
        db.user_owned_channels[target.id] = channel.id
        await remove_owner_permissions(channel, old_owner)
        await apply_owner_permissions(channel, target)
        db.db_update_room_owner(channel.id, target.id)
        await interaction.followup.send(f"Комната передана {target.mention}.", ephemeral=True)
        await logs.log_action(self.bot, old_owner, "Передал комнату", channel, target, VCTheme.WARN)

    @discord.ui.button(emoji=VCTheme.EMO["kick"], label="Выгнать", style=discord.ButtonStyle.secondary, custom_id="vc:kick", row=1)
    async def kick_user(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(interaction, self.bot, "Кого выгнать")
        if not target: return
        if target.id == interaction.user.id or not target.voice or target.voice.channel.id != channel.id:
            await interaction.followup.send("Неприменимое действие или цель вне канала.", ephemeral=True)
            return
        await target.move_to(None)
        await interaction.followup.send(f"{target.mention} выгнан из комнаты.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Выгнал участника из комнаты", channel, target, VCTheme.ERROR)

    @discord.ui.button(emoji=VCTheme.EMO["miceoff"], label="Запретить говорить всем", style=discord.ButtonStyle.secondary, custom_id="vc:mute_all", row=2)
    async def mute_all(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)

        everyone_ow = channel.overwrites_for(interaction.guild.default_role)
        everyone_ow.speak = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=everyone_ow)

        for member in channel.members:
            if member.id == interaction.user.id: continue
            ow = channel.overwrites_for(member)
            ow.speak = False
            await channel.set_permissions(member, overwrite=ow)

        owner_ow = channel.overwrites_for(interaction.user)
        owner_ow.speak = True
        await channel.set_permissions(interaction.user, overwrite=owner_ow)

        await interaction.followup.send("Всем запрещено говорить, кроме владельца.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Отключил голос всем участникам", channel, color=VCTheme.WARN)

    @discord.ui.button(emoji=VCTheme.EMO["mice"], label="Разрешить говорить всем", style=discord.ButtonStyle.secondary, custom_id="vc:unmute_all", row=2)
    async def unmute_all(self, interaction: discord.Interaction, _button: Button):
        channel = await ensure_owner(interaction, self.bot)
        if not channel: return
        await interaction.response.defer(ephemeral=True)

        everyone_ow = channel.overwrites_for(interaction.guild.default_role)
        everyone_ow.speak = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=everyone_ow)

        for member in channel.members:
            ow = channel.overwrites_for(member)
            if ow.speak is not None:
                ow.speak = None
                await channel.set_permissions(member, overwrite=ow)

        await interaction.followup.send("Голос снова разрешён всем.", ephemeral=True)
        await logs.log_action(self.bot, interaction.user, "Вернул голос всем участникам", channel, color=VCTheme.SUCCESS)


class VoiceManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._recovered = False

    def get_channel_owner_id(self, channel_id: int) -> int | None:
        return next((uid for uid, cid in db.user_owned_channels.items() if cid == channel_id), None)

    @commands.Cog.listener()
    async def on_ready(self):
        if self._recovered:
            return
        self._recovered = True
        await self.recover_private_rooms()

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if not isinstance(after, discord.VoiceChannel):
            return

        owner_id = self.get_channel_owner_id(after.id)
        if not owner_id:
            return

        default_role = after.guild.default_role
        before_ow = before.overwrites_for(default_role)
        after_ow = after.overwrites_for(default_role)

        if after_ow.view_channel is False and before_ow.view_channel is not False:
            await asyncio.sleep(5)

            current_channel = self.bot.get_channel(after.id)
            if not current_channel:
                return

            current_ow = current_channel.overwrites_for(default_role)
            current_ow.view_channel = True
            current_ow.connect = False
            await current_channel.set_permissions(default_role, overwrite=current_ow)

            owner = current_channel.guild.get_member(owner_id)
            if owner:
                dm_text = (
                    f"{owner.mention}, мы понимаем, что вы желаете скрыть ваш канал от других игроков, "
                    f"однако на данный момент это нарушает политику использования наших ботов.\n\n"
                    f"Ваш канал снова публичный и виден всем, однако доступ на подключение для всех закрыт. "
                    f"Настройки доступа конкретных людей не затронуты."
                )
                try:
                    await owner.send(dm_text)
                except discord.Forbidden:
                    pass

                await logs.log_unhide_action(self.bot, owner, current_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            lobby_id = _config_channel_id("VOICE_LOBBY_CHANNEL_ID")
            if after.channel and after.channel.id == lobby_id:
                old_channel_id = db.user_owned_channels.get(member.id)
                if old_channel_id:
                    old_channel = member.guild.get_channel(old_channel_id)
                    if isinstance(old_channel, discord.VoiceChannel):
                        try:
                            await old_channel.delete(reason="Recreated private room")
                        except Exception as exc:
                            await logs.log_error(self.bot, "delete_old_room_before_create", exc)
                    db.user_owned_channels.pop(member.id, None)
                    db.db_delete_room(old_channel_id)

                guild = member.guild
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
                    member: discord.PermissionOverwrite(
                        view_channel=True, connect=True, speak=True,
                        manage_channels=True, manage_permissions=True,
                        move_members=True, mute_members=False, deafen_members=False
                    )
                }

                channel = await guild.create_voice_channel(
                    name=f"Комната • {member.display_name}",
                    overwrites=overwrites,
                    category=after.channel.category
                )

                await member.move_to(channel)
                db.user_owned_channels[member.id] = channel.id
                db.db_upsert_room(guild.id, channel.id, member.id, channel.name, is_closed=False, user_limit=0)
                await logs.log_action(self.bot, member, "Создал приватную комнату", channel, color=VCTheme.SUCCESS)

            if before.channel and isinstance(before.channel, discord.VoiceChannel):
                room = db.db_get_room(before.channel.id)
                if room and len(before.channel.members) == 0:
                    owner_id = self.get_channel_owner_id(before.channel.id)
                    if owner_id:
                        db.user_owned_channels.pop(owner_id, None)

                    room_name = before.channel.name
                    channel_id = before.channel.id

                    try:
                        await before.channel.delete(reason="Empty private room")
                    except Exception as exc:
                        await logs.log_error(self.bot, "delete_empty_private_room", exc)
                        return

                    db.db_delete_room(channel_id)
                    await logs.send_log_embed(
                        self.bot,
                        title="Комната удалена",
                        description=f"**Комната:** {room_name} (`{channel_id}`)\n**Причина:** Пустая приватная комната",
                        color=VCTheme.WARN
                    )

        except Exception as exc:
            logger.exception("on_voice_state_update failed")
            await logs.log_error(self.bot, "on_voice_state_update", exc)

    async def recover_private_rooms(self):
        rows = db.db_get_all_rooms()
        restored, removed = 0, 0

        for row in rows:
            guild = self.bot.get_guild(row["guild_id"])
            if not guild:
                db.db_delete_room(row["channel_id"])
                removed += 1
                continue

            channel = guild.get_channel(row["channel_id"])
            if not isinstance(channel, discord.VoiceChannel):
                db.db_delete_room(row["channel_id"])
                removed += 1
                continue

            owner = guild.get_member(row["owner_id"])
            if not owner:
                db.db_delete_room(row["channel_id"])
                try:
                    if len(channel.members) == 0:
                        await channel.delete(reason="Recovery cleanup: owner not found")
                except Exception as exc:
                    await logs.log_error(self.bot, "recover_private_rooms.delete_orphan", exc)
                removed += 1
                continue

            db.user_owned_channels[owner.id] = channel.id

            try:
                await apply_owner_permissions(channel, owner)
                everyone = guild.default_role
                everyone_ow = channel.overwrites_for(everyone)
                everyone_ow.view_channel = True
                everyone_ow.connect = not bool(row["is_closed"])
                await channel.set_permissions(everyone, overwrite=everyone_ow)

                for access in db.db_get_all_access(channel.id):
                    member = guild.get_member(access["user_id"])
                    if not member: continue
                    if access["access_type"] == "allow":
                        await set_member_allow(channel, member)
                    elif access["access_type"] == "deny":
                        await set_member_deny(channel, member)

                await channel.edit(name=row["room_name"], user_limit=row["user_limit"])
                restored += 1
            except Exception as exc:
                logger.exception("Failed to restore channel %s", channel.id)
                await logs.log_error(self.bot, f"recover_private_rooms.restore:{channel.id}", exc)

        logger.info("Recovery finished. Restored=%s Removed=%s", restored, removed)
        await logs.send_log_embed(
            self.bot,
            title="Recovery завершён",
            description=f"**Восстановлено:** {restored}\n**Удалено битых записей:** {removed}",
            color=VCTheme.SUCCESS if restored or removed == 0 else VCTheme.WARN
        )


class PanelManager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._panel_published = False

    @commands.Cog.listener()
    async def on_ready(self):
        if self._panel_published:
            return
        self._panel_published = True
        self.bot.add_view(ChannelControlView(self.bot))
        await self.publish_panel()

    async def publish_panel(self) -> int | None:
        """Публикует (или обновляет) панель управления. Возвращает id сообщения панели."""
        channel = self.bot.get_channel(_config_channel_id("VOICE_PANEL_CHANNEL_ID"))
        if not channel:
            logger.warning("Voice panel text channel not found")
            return None

        embed = build_embed()
        state = load_panel_state()
        panel_msg_id = int(state.get("message_id") or 0)
        if panel_msg_id:
            try:
                msg = await channel.fetch_message(panel_msg_id)
                await msg.edit(embed=embed, view=ChannelControlView(self.bot))
                logger.info("Panel updated: %s", msg.id)
                return msg.id
            except discord.NotFound:
                pass

        msg = await channel.send(embed=embed, view=ChannelControlView(self.bot))
        save_panel_state({"message_id": msg.id, "channel_id": channel.id})
        logger.info("Panel created: %s", msg.id)
        return msg.id


async def setup(bot: commands.Bot):
    db.db_init()
    await bot.add_cog(VoiceManager(bot))
    await bot.add_cog(PanelManager(bot))
