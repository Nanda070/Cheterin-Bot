import settings_db
import asyncio
import os

import discord
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, UserSelect

import bot_config
import i18n
import voice_db as db
import voice_logs as logs
from voice_logs import VCTheme, logger

MODULE_NAME = "voice_panel"  # должно совпадать с ключом в settings_migration.MODULE_FILE_MAP


def _main_guild_id() -> int:
    """Панель управления комнатами публикуется один раз на весь процесс бота
    (не per-guild), поэтому её настройки читаем с мейн-сервера через GUILD_ID —
    полноценный per-guild выбор см. Фазу 2.4 MULTIGUILD_PLAN.md."""
    return int(os.getenv("GUILD_ID", "0") or 0)


def _config_channel_id(guild_id: int, key: str) -> int:
    raw = bot_config.get(guild_id, key)
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 0


def load_panel_state() -> dict:
    """Состояние панели (id сообщения/канала) — синглтон мейн-сервера в settings_db
    (Фаза 2.2б MULTIGUILD_PLAN.md)."""
    return settings_db.get(_main_guild_id(), MODULE_NAME)


def save_panel_state(data: dict) -> None:
    settings_db.put(_main_guild_id(), MODULE_NAME, data)


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


async def ensure_owner(interaction: discord.Interaction, bot: commands.Bot, lang: str) -> discord.VoiceChannel | None:
    if not interaction.user.voice or not interaction.user.voice.channel:
        await safe_followup(interaction, i18n.t("voice_rooms.error.not_in_voice", lang))
        await logs.log_security(bot, interaction.guild.id, interaction.user, "Попытка использовать управление вне голосового канала.")
        return None

    channel = interaction.user.voice.channel
    if not isinstance(channel, discord.VoiceChannel):
        await safe_followup(interaction, i18n.t("voice_rooms.error.not_voice_channel", lang))
        await logs.log_security(bot, interaction.guild.id, interaction.user, "Попытка использовать управление вне voice-канала.")
        return None

    room = db.db_get_room(channel.id)
    if not room:
        await safe_followup(interaction, i18n.t("voice_rooms.error.not_registered", lang))
        await logs.log_security(bot, interaction.guild.id, interaction.user, "Попытка управлять незарегистрированной комнатой.", channel)
        return None

    if not is_room_owner(interaction.user.id, channel.id):
        await safe_followup(interaction, i18n.t("voice_rooms.error.not_owner", lang))
        await logs.log_security(bot, interaction.guild.id, interaction.user, "Попытка управлять чужой комнатой.", channel)
        return None

    return channel


async def select_member_ephemeral(interaction: discord.Interaction, bot: commands.Bot, placeholder: str, lang: str) -> discord.Member | None:
    view = View(timeout=30)
    select = UserSelect(placeholder=placeholder, min_values=1, max_values=1, custom_id="vc:user_select")
    view.add_item(select)

    prompt = i18n.t("voice_rooms.select.prompt", lang)
    if not interaction.response.is_done():
        await interaction.response.send_message(prompt, view=view, ephemeral=True)
    else:
        await interaction.followup.send(prompt, view=view, ephemeral=True)

    def check(i: discord.Interaction):
        return i.user.id == interaction.user.id and i.data and i.data.get("custom_id") == "vc:user_select"

    try:
        result: discord.Interaction = await bot.wait_for("interaction", timeout=30, check=check)
    except asyncio.TimeoutError:
        await interaction.followup.send(i18n.t("voice_rooms.select.timeout", lang), ephemeral=True)
        return None

    user_id = int(result.data["values"][0])
    member = interaction.guild.get_member(user_id) if interaction.guild else None
    await result.response.defer()
    return member


def build_embed(lang: str) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("voice_rooms.panel.title", lang),
        description=i18n.t("voice_rooms.panel.description", lang),
        color=VCTheme.COLOR
    )
    embed.add_field(
        name=i18n.t("voice_rooms.panel.access", lang),
        value=(
            f"{i18n.t('voice_rooms.panel.access_open', lang, emoji=VCTheme.EMO['openroom'])}\n"
            f"{i18n.t('voice_rooms.panel.access_close', lang, emoji=VCTheme.EMO['lock'])}\n"
            f"{i18n.t('voice_rooms.panel.access_allow', lang, emoji=VCTheme.EMO['lockuser'])}\n"
            f"{i18n.t('voice_rooms.panel.access_deny', lang, emoji=VCTheme.EMO['404'])}\n"
        ),
        inline=True
    )
    embed.add_field(
        name=i18n.t("voice_rooms.panel.manage", lang),
        value=(
            f"{i18n.t('voice_rooms.panel.manage_rename', lang, emoji=VCTheme.EMO['name'])}\n"
            f"{i18n.t('voice_rooms.panel.manage_limit', lang, emoji=VCTheme.EMO['limit'])}\n"
            f"{i18n.t('voice_rooms.panel.manage_transfer', lang, emoji=VCTheme.EMO['owner'])}\n"
            f"{i18n.t('voice_rooms.panel.manage_kick', lang, emoji=VCTheme.EMO['kick'])}\n"
        ),
        inline=True
    )
    embed.add_field(
        name=i18n.t("voice_rooms.panel.voice", lang),
        value=(
            f"{i18n.t('voice_rooms.panel.voice_mute', lang, emoji=VCTheme.EMO['miceoff'])}\n"
            f"{i18n.t('voice_rooms.panel.voice_unmute', lang, emoji=VCTheme.EMO['mice'])}\n"
        ),
        inline=False
    )
    thumb = bot_config.get(_main_guild_id(), "VOICE_PANEL_THUMB_URL")
    if thumb:
        embed.set_thumbnail(url=thumb)
    return embed


class RenameModal(Modal):
    def __init__(self, bot, lang: str):
        super().__init__(title=i18n.t("voice_rooms.modal.rename.title", lang))
        self.bot = bot
        self.lang = lang
        self.new_name = TextInput(label=i18n.t("voice_rooms.modal.rename.label", lang), max_length=96)
        self.add_item(self.new_name)

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        value = self.new_name.value.strip()
        if not value:
            await interaction.response.send_message(i18n.t("voice_rooms.modal.rename.empty", lang), ephemeral=True)
            return
        old_name = channel.name
        await channel.edit(name=value)
        db.db_update_room_name(channel.id, value)
        await interaction.response.send_message(
            i18n.t("voice_rooms.modal.rename.done", lang, old=old_name, new=value),
            ephemeral=True,
        )
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, f"Переименовал комнату: {old_name} → {value}", channel, color=VCTheme.SUCCESS)


class SlotsModal(Modal):
    def __init__(self, bot, lang: str):
        super().__init__(title=i18n.t("voice_rooms.modal.limit.title", lang))
        self.bot = bot
        self.lang = lang
        self.slots = TextInput(
            label=i18n.t("voice_rooms.modal.limit.label", lang),
            max_length=3,
            placeholder=i18n.t("voice_rooms.modal.limit.placeholder", lang),
        )
        self.add_item(self.slots)

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        try:
            value = int(self.slots.value.strip())
            if not 0 <= value <= 99:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(i18n.t("voice_rooms.modal.limit.invalid", lang), ephemeral=True)
            return
        await channel.edit(user_limit=value)
        db.db_update_room_limit(channel.id, value)
        msg = (
            i18n.t("voice_rooms.modal.limit.removed", lang)
            if value == 0
            else i18n.t("voice_rooms.modal.limit.set", lang, value=value)
        )
        await interaction.response.send_message(msg, ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, f"Изменил лимит комнаты на {value}", channel, color=VCTheme.SUCCESS)


class ChannelControlView(View):
    def __init__(self, bot: commands.Bot, lang: str | None = None):
        super().__init__(timeout=None)
        self.bot = bot
        self.lang = lang or i18n.lang_for(_main_guild_id())
        self._add_buttons()

    def _add_buttons(self):
        buttons = [
            (VCTheme.EMO["openroom"], "voice_rooms.button.open", "vc:open", discord.ButtonStyle.secondary, 0, self.open_room),
            (VCTheme.EMO["lock"], "voice_rooms.button.close", "vc:close", discord.ButtonStyle.secondary, 0, self.close_room),
            (VCTheme.EMO["lockuser"], "voice_rooms.button.allow", "vc:allow_user", discord.ButtonStyle.secondary, 0, self.allow_user),
            (VCTheme.EMO["404"], "voice_rooms.button.deny", "vc:deny_user", discord.ButtonStyle.secondary, 0, self.deny_user),
            (VCTheme.EMO["name"], "voice_rooms.button.rename", "vc:rename", discord.ButtonStyle.secondary, 1, self.rename_room),
            (VCTheme.EMO["limit"], "voice_rooms.button.limit", "vc:limit", discord.ButtonStyle.secondary, 1, self.limit_room),
            (VCTheme.EMO["owner"], "voice_rooms.button.transfer", "vc:transfer", discord.ButtonStyle.secondary, 1, self.transfer_room),
            (VCTheme.EMO["kick"], "voice_rooms.button.kick", "vc:kick", discord.ButtonStyle.secondary, 1, self.kick_user),
            (VCTheme.EMO["miceoff"], "voice_rooms.button.mute_all", "vc:mute_all", discord.ButtonStyle.secondary, 2, self.mute_all),
            (VCTheme.EMO["mice"], "voice_rooms.button.unmute_all", "vc:unmute_all", discord.ButtonStyle.secondary, 2, self.unmute_all),
        ]
        for emoji, label_key, custom_id, style, row, callback in buttons:
            btn = Button(
                emoji=emoji,
                label=i18n.t(label_key, self.lang),
                style=style,
                custom_id=custom_id,
                row=row,
            )
            btn.callback = callback
            self.add_item(btn)

    async def open_room(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        await set_open_state(channel)
        await interaction.followup.send(i18n.t("voice_rooms.opened", lang), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Открыл комнату", channel, color=VCTheme.SUCCESS)

    async def close_room(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        await set_closed_state(channel)
        await interaction.followup.send(i18n.t("voice_rooms.closed", lang), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Закрыл комнату", channel, color=VCTheme.WARN)

    async def allow_user(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(
            interaction, self.bot, i18n.t("voice_rooms.select.allow", lang), lang
        )
        if not target:
            return
        if target.bot:
            await interaction.followup.send(i18n.t("voice_rooms.bot_forbidden", lang), ephemeral=True)
            return await logs.log_security(self.bot, interaction.guild.id, interaction.user, "Попытка выдать доступ боту.", channel)
        await set_member_allow(channel, target)
        await interaction.followup.send(i18n.t("voice_rooms.allowed", lang, mention=target.mention), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Выдал доступ к комнате", channel, target, VCTheme.SUCCESS)

    async def deny_user(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(
            interaction, self.bot, i18n.t("voice_rooms.select.deny", lang), lang
        )
        if not target:
            return
        if target.id == interaction.user.id or target.bot:
            await interaction.followup.send(i18n.t("voice_rooms.invalid_action", lang), ephemeral=True)
            return await logs.log_security(self.bot, interaction.guild.id, interaction.user, "Попытка блокировки себя/бота.", channel)
        await set_member_deny(channel, target)
        if target.voice and target.voice.channel and target.voice.channel.id == channel.id:
            await target.move_to(None)
        await interaction.followup.send(i18n.t("voice_rooms.denied", lang, mention=target.mention), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Запретил вход в комнату", channel, target, VCTheme.ERROR)

    async def rename_room(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        if await ensure_owner(interaction, self.bot, lang):
            await interaction.response.send_modal(RenameModal(self.bot, lang))

    async def limit_room(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        if await ensure_owner(interaction, self.bot, lang):
            await interaction.response.send_modal(SlotsModal(self.bot, lang))

    async def transfer_room(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(
            interaction, self.bot, i18n.t("voice_rooms.select.transfer", lang), lang
        )
        if not target:
            return
        if target.id == interaction.user.id or target.bot or not target.voice or target.voice.channel.id != channel.id:
            await interaction.followup.send(i18n.t("voice_rooms.invalid_target", lang), ephemeral=True)
            return

        old_owner = interaction.user
        db.user_owned_channels.pop(old_owner.id, None)
        db.user_owned_channels[target.id] = channel.id
        await remove_owner_permissions(channel, old_owner)
        await apply_owner_permissions(channel, target)
        db.db_update_room_owner(channel.id, target.id)
        await interaction.followup.send(i18n.t("voice_rooms.transferred", lang, mention=target.mention), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, old_owner, "Передал комнату", channel, target, VCTheme.WARN)

    async def kick_user(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)
        target = await select_member_ephemeral(
            interaction, self.bot, i18n.t("voice_rooms.select.kick", lang), lang
        )
        if not target:
            return
        if target.id == interaction.user.id or not target.voice or target.voice.channel.id != channel.id:
            await interaction.followup.send(i18n.t("voice_rooms.invalid_target", lang), ephemeral=True)
            return
        await target.move_to(None)
        await interaction.followup.send(i18n.t("voice_rooms.kicked", lang, mention=target.mention), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Выгнал участника из комнаты", channel, target, VCTheme.ERROR)

    async def mute_all(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)

        everyone_ow = channel.overwrites_for(interaction.guild.default_role)
        everyone_ow.speak = False
        await channel.set_permissions(interaction.guild.default_role, overwrite=everyone_ow)

        for member in channel.members:
            if member.id == interaction.user.id:
                continue
            ow = channel.overwrites_for(member)
            ow.speak = False
            await channel.set_permissions(member, overwrite=ow)

        owner_ow = channel.overwrites_for(interaction.user)
        owner_ow.speak = True
        await channel.set_permissions(interaction.user, overwrite=owner_ow)

        await interaction.followup.send(i18n.t("voice_rooms.muted_all", lang), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Отключил голос всем участникам", channel, color=VCTheme.WARN)

    async def unmute_all(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        channel = await ensure_owner(interaction, self.bot, lang)
        if not channel:
            return
        await interaction.response.defer(ephemeral=True)

        everyone_ow = channel.overwrites_for(interaction.guild.default_role)
        everyone_ow.speak = None
        await channel.set_permissions(interaction.guild.default_role, overwrite=everyone_ow)

        for member in channel.members:
            ow = channel.overwrites_for(member)
            if ow.speak is not None:
                ow.speak = None
                await channel.set_permissions(member, overwrite=ow)

        await interaction.followup.send(i18n.t("voice_rooms.unmuted_all", lang), ephemeral=True)
        await logs.log_action(self.bot, interaction.guild.id, interaction.user, "Вернул голос всем участникам", channel, color=VCTheme.SUCCESS)


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
                lang = i18n.lang_for(after.guild.id)
                try:
                    await owner.send(i18n.t("voice_rooms.unhide_dm", lang, mention=owner.mention))
                except discord.Forbidden:
                    pass

                await logs.log_unhide_action(self.bot, after.guild.id, owner, current_channel)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            lang = i18n.lang_for(member.guild.id)
            lobby_id = _config_channel_id(member.guild.id, "VOICE_LOBBY_CHANNEL_ID")
            if after.channel and after.channel.id == lobby_id:
                old_channel_id = db.user_owned_channels.get(member.id)
                if old_channel_id:
                    old_channel = member.guild.get_channel(old_channel_id)
                    if isinstance(old_channel, discord.VoiceChannel):
                        try:
                            await old_channel.delete(reason="Recreated private room")
                        except Exception as exc:
                            await logs.log_error(self.bot, member.guild.id, "delete_old_room_before_create", exc)
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
                    name=i18n.t("voice_rooms.room_name", lang, name=member.display_name),
                    overwrites=overwrites,
                    category=after.channel.category
                )

                await member.move_to(channel)
                db.user_owned_channels[member.id] = channel.id
                db.db_upsert_room(guild.id, channel.id, member.id, channel.name, is_closed=False, user_limit=0)
                await logs.log_action(self.bot, member.guild.id, member, "Создал приватную комнату", channel, color=VCTheme.SUCCESS)

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
                        await logs.log_error(self.bot, member.guild.id, "delete_empty_private_room", exc)
                        return

                    db.db_delete_room(channel_id)
                    await logs.send_log_embed(
                        self.bot,
                        member.guild.id,
                        title=i18n.t("voice_rooms.log.deleted_title", lang),
                        description=i18n.t("voice_rooms.log.deleted_body", lang, name=room_name, channel_id=channel_id),
                        color=VCTheme.WARN
                    )

        except Exception as exc:
            logger.exception("on_voice_state_update failed")
            await logs.log_error(self.bot, member.guild.id, "on_voice_state_update", exc)

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
                    await logs.log_error(self.bot, guild.id, "recover_private_rooms.delete_orphan", exc)
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
                    if not member:
                        continue
                    if access["access_type"] == "allow":
                        await set_member_allow(channel, member)
                    elif access["access_type"] == "deny":
                        await set_member_deny(channel, member)

                await channel.edit(name=row["room_name"], user_limit=row["user_limit"])
                restored += 1
            except Exception as exc:
                logger.exception("Failed to restore channel %s", channel.id)
                await logs.log_error(self.bot, guild.id, f"recover_private_rooms.restore:{channel.id}", exc)

        logger.info("Recovery finished. Restored=%s Removed=%s", restored, removed)
        guild_id = row["guild_id"] if rows else _main_guild_id()
        lang = i18n.lang_for(guild_id)
        await logs.send_log_embed(
            self.bot,
            guild_id,
            title=i18n.t("voice_rooms.log.recovery_title", lang),
            description=i18n.t("voice_rooms.log.recovery_body", lang, restored=restored, removed=removed),
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
        lang = i18n.lang_for(_main_guild_id())
        self.bot.add_view(ChannelControlView(self.bot, lang))
        await self.publish_panel()

    async def publish_panel(self) -> int | None:
        """Публикует (или обновляет) панель управления. Возвращает id сообщения панели."""
        channel = self.bot.get_channel(_config_channel_id(_main_guild_id(), "VOICE_PANEL_CHANNEL_ID"))
        if not channel:
            logger.warning("Voice panel text channel not found")
            return None

        lang = i18n.lang_for(_main_guild_id())
        embed = build_embed(lang)
        state = load_panel_state()
        panel_msg_id = int(state.get("message_id") or 0)
        if panel_msg_id:
            try:
                msg = await channel.fetch_message(panel_msg_id)
                await msg.edit(embed=embed, view=ChannelControlView(self.bot, lang))
                logger.info("Panel updated: %s", msg.id)
                return msg.id
            except discord.NotFound:
                pass

        msg = await channel.send(embed=embed, view=ChannelControlView(self.bot, lang))
        save_panel_state({"message_id": msg.id, "channel_id": channel.id})
        logger.info("Panel created: %s", msg.id)
        return msg.id


async def setup(bot: commands.Bot):
    db.db_init()
    await bot.add_cog(VoiceManager(bot))
    await bot.add_cog(PanelManager(bot))
