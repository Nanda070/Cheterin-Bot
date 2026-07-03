# pyrefly: ignore [missing-import]
import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import asyncio
import uuid
import logging
from typing import Optional
import random
import string

import events_core

logger = logging.getLogger("chetbot.events")
EVENTS_FILE = "events_data.json"


async def load_events() -> dict:
    def _read():
        if os.path.exists(EVENTS_FILE):
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    return {}
        return {}
    data = await asyncio.to_thread(_read)
    if "events" not in data:
        data["events"] = {}
    return data


async def save_events(data: dict):
    def _write():
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    await asyncio.to_thread(_write)


def upsert_embed_field(embed: discord.Embed, name: str, value: str, inline: bool = False):
    for idx, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(idx, name=name, value=value, inline=inline)
            return
    embed.add_field(name=name, value=value, inline=inline)


def rebuild_event_embed(embed: discord.Embed, event_data: dict) -> discord.Embed:
    emb = embed.copy()
    if event_data["type"] == "tournament":
        participants = event_data.get("participants", [])
        if event_data["mode"] == "team_code":
            teams = set(p.get("team_code") for p in participants if p.get("team_code"))
            current_count = len(teams)
        else:
            current_count = len(participants)
            
        max_limit = event_data.get("max_limit", 0)
        if max_limit > 0:
            upsert_embed_field(emb, "Лимит", f"{current_count} / {max_limit}", inline=True)
        else:
            upsert_embed_field(emb, "Участники", str(current_count), inline=True)
    else:
        votes = event_data.get("votes", {})
        opts = event_data.get("options", [])
        counts = [0] * len(opts)
        total = 0
        for uid, user_votes in votes.items():
            for v in user_votes:
                if v < len(counts):
                    counts[v] += 1
                    total += 1
        
        for idx, opt in enumerate(opts):
            c = counts[idx]
            pct = int((c / total * 100) if total > 0 else 0)
            bars = "🟩" * (pct // 10) + "⬛" * (10 - (pct // 10))
            upsert_embed_field(emb, opt, f"{bars} {pct}% ({c} гол.)", inline=False)
    return emb


# ==========================================
# BUILDER LOGIC
# ==========================================

class DraftEvent:
    def __init__(self, author_id: int):
        self.author_id = author_id
        self.type = "tournament"
        self.title = ""
        self.description = ""
        self.banner_url = ""
        
        self.mode = "solo"
        self.require_info = False
        self.max_limit = 0
        self.team_size = 5
        self.role_reward = None
        self.ping = "none"
        
        self.options = []
        self.multi_select = False


class TextModal(discord.ui.Modal, title="Текст события"):
    def __init__(self, draft: DraftEvent, view):
        super().__init__()
        self.draft = draft
        self.builder_view = view
        
        self.inp_title = discord.ui.TextInput(label="Заголовок", style=discord.TextStyle.short, default=draft.title, required=True, max_length=100)
        self.inp_desc = discord.ui.TextInput(label="Описание", style=discord.TextStyle.paragraph, default=draft.description, required=True, max_length=2000)
        self.inp_banner = discord.ui.TextInput(label="URL баннера (опционально)", style=discord.TextStyle.short, default=draft.banner_url, required=False)
        self.add_item(self.inp_title)
        self.add_item(self.inp_desc)
        self.add_item(self.inp_banner)

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.title = self.inp_title.value.strip()
        self.draft.description = self.inp_desc.value.strip()
        self.draft.banner_url = self.inp_banner.value.strip()
        await self.builder_view.refresh(interaction)


class LimitsModal(discord.ui.Modal, title="Настройка лимитов"):
    def __init__(self, draft: DraftEvent, view):
        super().__init__()
        self.draft = draft
        self.builder_view = view
        
        self.inp_max = discord.ui.TextInput(label="Макс. участников/команд (0 = безлимит)", style=discord.TextStyle.short, default=str(draft.max_limit), required=True)
        self.inp_team = discord.ui.TextInput(label="Размер команды", style=discord.TextStyle.short, default=str(draft.team_size), required=True)
        self.add_item(self.inp_max)
        if draft.mode != "solo":
            self.add_item(self.inp_team)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.draft.max_limit = max(0, int(self.inp_max.value.strip()))
            if self.draft.mode != "solo":
                self.draft.team_size = max(2, int(self.inp_team.value.strip()))
        except ValueError:
            await interaction.response.send_message("Ошибка: Введите число!", ephemeral=True)
            return
        await self.builder_view.refresh(interaction)


class OptionsModal(discord.ui.Modal, title="Варианты ответа (каждый с новой строки)"):
    def __init__(self, draft: DraftEvent, view):
        super().__init__()
        self.draft = draft
        self.builder_view = view
        
        self.inp_opts = discord.ui.TextInput(label="Варианты (Макс 10 строк)", style=discord.TextStyle.paragraph, default="\n".join(draft.options), required=True, max_length=1000)
        self.add_item(self.inp_opts)

    async def on_submit(self, interaction: discord.Interaction):
        lines = [x.strip() for x in self.inp_opts.value.strip().split("\n") if x.strip()]
        if len(lines) > 10:
            lines = lines[:10]
        if len(lines) < 2:
            await interaction.response.send_message("Нужно минимум 2 варианта ответа!", ephemeral=True)
            return
        self.draft.options = lines
        await self.builder_view.refresh(interaction)


class EventPublishSelect(discord.ui.ChannelSelect):
    def __init__(self, view):
        super().__init__(placeholder="🚀 Опубликовать (Выбрать канал)", channel_types=[discord.ChannelType.text, discord.ChannelType.news], min_values=1, max_values=1, row=4)
        self.builder_view = view

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        if not self.builder_view.draft.title or not self.builder_view.draft.description:
            await interaction.response.send_message("Сначала укажите название и описание!", ephemeral=True)
            return
        if self.builder_view.draft.type == "poll" and not self.builder_view.draft.options:
            await interaction.response.send_message("Для опроса нужны варианты ответа!", ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        await self.builder_view.publish(interaction, channel)


class EventBuilderView(discord.ui.View):
    def __init__(self, bot, author_id: int):
        super().__init__(timeout=600)
        self.bot = bot
        self.draft = DraftEvent(author_id)
        self.update_buttons()

    def build_embed(self) -> discord.Embed:
        d = self.draft
        emb = discord.Embed(title="🎛️ Конструктор событий", color=discord.Color.gold())
        emb.add_field(name="Тип события", value="Турнир/Регистрация" if d.type == "tournament" else "Опрос/Голосование", inline=False)
        emb.add_field(name="Название", value=d.title or "❌ Не задано", inline=True)
        desc = d.description[:100] + "..." if len(d.description) > 100 else d.description
        emb.add_field(name="Описание", value=desc or "❌ Не задано", inline=True)
        
        if d.type == "tournament":
            mode_str = {"solo": "Соло", "team_captain": "Командный (Капитан)", "team_code": "Командный (По коду)"}.get(d.mode)
            emb.add_field(name="Формат", value=mode_str, inline=True)
            emb.add_field(name="Анкета (Ники)", value="✅ Да" if d.require_info else "❌ Нет", inline=True)
            limits = f"{d.max_limit if d.max_limit > 0 else '♾️'}"
            if d.mode != "solo": limits += f" (команд по {d.team_size} чел)"
            emb.add_field(name="Лимиты", value=limits, inline=True)
            emb.add_field(name="Выдаваемая роль", value=f"<@&{d.role_reward}>" if d.role_reward else "❌ Нет", inline=True)
        else:
            opts = "\n".join(f"• {x}" for x in d.options) if d.options else "❌ Нет вариантов"
            emb.add_field(name="Варианты ответа", value=opts, inline=False)
            emb.add_field(name="Мульти-выбор", value="✅ Да" if d.multi_select else "❌ Нет", inline=True)
            
        ping_str = {"none": "❌ Нет", "everyone": "@everyone", "here": "@here"}.get(d.ping, f"<@&{d.ping}>")
        emb.add_field(name="Пинг", value=ping_str, inline=True)
        if d.banner_url:
            emb.set_thumbnail(url=d.banner_url)
        return emb

    def update_buttons(self):
        self.clear_items()
        d = self.draft
        
        btn_type = discord.ui.Button(label="Сменить тип", style=discord.ButtonStyle.primary, row=0)
        btn_type.callback = self.cb_type
        self.add_item(btn_type)
        
        btn_text = discord.ui.Button(label="Название и Текст", style=discord.ButtonStyle.secondary, row=0)
        btn_text.callback = self.cb_text
        self.add_item(btn_text)
        
        btn_ping = discord.ui.Button(label="Пинг: " + str(d.ping), style=discord.ButtonStyle.secondary, row=0)
        btn_ping.callback = self.cb_ping
        self.add_item(btn_ping)

        if d.type == "tournament":
            btn_mode = discord.ui.Button(label="Формат: " + d.mode, style=discord.ButtonStyle.secondary, row=1)
            btn_mode.callback = self.cb_mode
            self.add_item(btn_mode)
            
            btn_info = discord.ui.Button(label="Анкета: " + ("ВКЛ" if d.require_info else "ВЫКЛ"), style=discord.ButtonStyle.secondary, row=1)
            btn_info.callback = self.cb_info
            self.add_item(btn_info)
            
            btn_limits = discord.ui.Button(label="Лимиты", style=discord.ButtonStyle.secondary, row=1)
            btn_limits.callback = self.cb_limits
            self.add_item(btn_limits)
            
            role_select = discord.ui.RoleSelect(placeholder="🏷️ Выбрать роль для авто-выдачи", min_values=1, max_values=1, row=2)
            role_select.callback = self.cb_role
            self.add_item(role_select)
        else:
            btn_opts = discord.ui.Button(label="Варианты ответа", style=discord.ButtonStyle.secondary, row=1)
            btn_opts.callback = self.cb_opts
            self.add_item(btn_opts)
            
            btn_multi = discord.ui.Button(label="Мультивыбор: " + ("ВКЛ" if d.multi_select else "ВЫКЛ"), style=discord.ButtonStyle.secondary, row=1)
            btn_multi.callback = self.cb_multi
            self.add_item(btn_multi)

        self.add_item(EventPublishSelect(self))

    async def refresh(self, interaction: discord.Interaction):
        self.update_buttons()
        if not interaction.response.is_done():
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        else:
            await interaction.edit_original_response(embed=self.build_embed(), view=self)

    async def cb_type(self, interaction: discord.Interaction):
        self.draft.type = "poll" if self.draft.type == "tournament" else "tournament"
        await self.refresh(interaction)

    async def cb_text(self, interaction: discord.Interaction):
        await interaction.response.send_modal(TextModal(self.draft, self))

    async def cb_ping(self, interaction: discord.Interaction):
        cycles = ["none", "everyone", "here"]
        idx = cycles.index(self.draft.ping) if self.draft.ping in cycles else -1
        self.draft.ping = cycles[(idx + 1) % len(cycles)]
        await self.refresh(interaction)

    async def cb_mode(self, interaction: discord.Interaction):
        modes = ["solo", "team_captain", "team_code"]
        idx = modes.index(self.draft.mode)
        self.draft.mode = modes[(idx + 1) % len(modes)]
        await self.refresh(interaction)

    async def cb_info(self, interaction: discord.Interaction):
        self.draft.require_info = not self.draft.require_info
        await self.refresh(interaction)

    async def cb_limits(self, interaction: discord.Interaction):
        await interaction.response.send_modal(LimitsModal(self.draft, self))

    async def cb_role(self, interaction: discord.Interaction):
        self.draft.role_reward = interaction.data["values"][0]
        await self.refresh(interaction)

    async def cb_opts(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OptionsModal(self.draft, self))

    async def cb_multi(self, interaction: discord.Interaction):
        self.draft.multi_select = not self.draft.multi_select
        await self.refresh(interaction)

    async def publish(self, interaction: discord.Interaction, channel: discord.TextChannel):
        d = self.draft
        emb = discord.Embed(
            title=d.title,
            description=d.description,
            color=discord.Color.brand_red() if d.type == "tournament" else discord.Color.blurple()
        )
        if d.banner_url:
            emb.set_image(url=d.banner_url)
            
        if d.type == "tournament":
            mode_str = {"solo": "Соло", "team_captain": "Командный", "team_code": "Командный (по коду)"}.get(d.mode)
            emb.add_field(name="Формат", value=mode_str, inline=True)
            if d.max_limit > 0:
                emb.add_field(name="Лимит", value=f"0 / {d.max_limit}", inline=True)
            else:
                emb.add_field(name="Участники", value="0", inline=True)
        else:
            for opt in d.options:
                emb.add_field(name=opt, value="░░░░░░░░░░ 0% (0 гол.)", inline=False)
                
        emb.set_footer(text="🟢 Статус: Открыто")
        
        content = None
        if d.ping == "everyone": content = "@everyone"
        elif d.ping == "here": content = "@here"
        
        # ChannelSelect возвращает AppCommandChannel, у которого нет .send()
        # Нужно получить полный объект TextChannel
        resolved_channel = self.bot.get_channel(channel.id)
        if not resolved_channel:
            try:
                resolved_channel = await self.bot.fetch_channel(channel.id)
            except Exception:
                await interaction.edit_original_response(content="❌ Не удалось получить доступ к выбранному каналу.")
                return
        
        msg = await resolved_channel.send(content=content, embed=emb)
        
        data = await load_events()
        if "events" not in data:
            data["events"] = {}
            
        event_obj = {
            "type": d.type,
            "channel_id": resolved_channel.id,
            "author_id": d.author_id,
            "title": d.title,
            "description": d.description,
            "banner_url": d.banner_url,
            "mode": d.mode,
            "require_info": d.require_info,
            "max_limit": d.max_limit,
            "team_size": d.team_size,
            "role_reward": int(d.role_reward) if d.role_reward else None,
            "ping": d.ping,
            "status": "open",
            "participants": [],
            "options": d.options,
            "multi_select": d.multi_select,
            "votes": {}
        }
        data["events"][str(msg.id)] = event_obj
        await save_events(data)
        
        view = create_participation_view(str(msg.id), event_obj)
        await msg.edit(view=view)
        
        self.clear_items()
        await interaction.edit_original_response(
            content=f"✅ Успешно опубликовано в {resolved_channel.mention}!\nID сообщения: `{msg.id}`",
            embed=None, view=None
        )


# ==========================================
# REGISTRATION MODALS
# ==========================================

class RegisterSoloModal(discord.ui.Modal, title="Регистрация"):
    def __init__(self, message_id: str, require_info: bool):
        super().__init__()
        self.message_id = message_id
        self.require_info = require_info
        if require_info:
            self.inp_ign = discord.ui.TextInput(label="Ваш игровой ник", style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)
        else:
            self.inp_ign = discord.ui.TextInput(label="Подтверждение", style=discord.TextStyle.short, default="Участвую!", required=True, max_length=20)
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        ign = self.inp_ign.value.strip() if self.require_info else "—"
        await handle_registration(interaction, self.message_id, "solo", ign=ign)


class RegisterTeamCaptainModal(discord.ui.Modal, title="Регистрация команды"):
    def __init__(self, message_id: str, team_size: int, require_info: bool):
        super().__init__()
        self.message_id = message_id
        self.require_info = require_info
        self.inp_team = discord.ui.TextInput(label="Название команды", style=discord.TextStyle.short, required=True, max_length=50)
        self.inp_members = discord.ui.TextInput(label=f"Ники всех игроков (до {team_size} шт)", style=discord.TextStyle.paragraph, required=True, max_length=1000)
        self.add_item(self.inp_team)
        self.add_item(self.inp_members)

    async def on_submit(self, interaction: discord.Interaction):
        await handle_registration(
            interaction, self.message_id, "team_captain", 
            team_name=self.inp_team.value.strip(),
            members=self.inp_members.value.strip()
        )


class CreateTeamCodeModal(discord.ui.Modal, title="Создание команды"):
    def __init__(self, message_id: str, require_info: bool):
        super().__init__()
        self.message_id = message_id
        self.require_info = require_info
        self.inp_team = discord.ui.TextInput(label="Название команды", style=discord.TextStyle.short, required=True, max_length=50)
        self.add_item(self.inp_team)
        if require_info:
            self.inp_ign = discord.ui.TextInput(label="Ваш игровой ник (Капитан)", style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        ign = self.inp_ign.value.strip() if self.require_info else "—"
        await handle_registration(interaction, self.message_id, "create_team_code", team_name=self.inp_team.value.strip(), ign=ign)


class JoinTeamCodeModal(discord.ui.Modal, title="Вступление в команду"):
    def __init__(self, message_id: str, require_info: bool):
        super().__init__()
        self.message_id = message_id
        self.require_info = require_info
        self.inp_code = discord.ui.TextInput(label="Код команды", style=discord.TextStyle.short, required=True, max_length=20)
        self.add_item(self.inp_code)
        if require_info:
            self.inp_ign = discord.ui.TextInput(label="Ваш игровой ник", style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        ign = self.inp_ign.value.strip() if self.require_info else "—"
        await handle_registration(interaction, self.message_id, "join_team_code", team_code=self.inp_code.value.strip().upper(), ign=ign)


async def handle_registration(interaction: discord.Interaction, message_id: str, action: str, **kwargs):
    await interaction.response.defer(ephemeral=True)
    data = await load_events()
    ev = data.get("events", {}).get(message_id)
    if not ev:
        await interaction.followup.send("❌ Событие не найдено.", ephemeral=True)
        return
    if ev["status"] != "open":
        await interaction.followup.send("❌ Регистрация уже закрыта.", ephemeral=True)
        return

    uid = interaction.user.id
    parts = ev.setdefault("participants", [])

    if action in ["solo", "team_captain", "create_team_code"]:
        if any(p.get("user_id") == uid for p in parts):
            await interaction.followup.send("❌ Вы уже зарегистрированы!", ephemeral=True)
            return

    max_limit = ev.get("max_limit", 0)
    custom_success_msg = "✅ Вы успешно зарегистрированы!"
    
    if action == "solo":
        if max_limit > 0 and len(parts) >= max_limit:
            await interaction.followup.send("❌ Мест больше нет!", ephemeral=True)
            return
        parts.append({"user_id": uid, "ign": kwargs.get("ign")})
        
    elif action == "team_captain":
        if max_limit > 0 and len(parts) >= max_limit:
            await interaction.followup.send("❌ Мест для команд больше нет!", ephemeral=True)
            return
        parts.append({"user_id": uid, "team_name": kwargs.get("team_name"), "members": kwargs.get("members")})

    elif action == "create_team_code":
        teams = set(p.get("team_code") for p in parts if p.get("team_code"))
        if max_limit > 0 and len(teams) >= max_limit:
            await interaction.followup.send("❌ Мест для команд больше нет!", ephemeral=True)
            return
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        parts.append({"user_id": uid, "team_name": kwargs.get("team_name"), "team_code": code, "ign": kwargs.get("ign"), "is_captain": True})
        
        try:
            await interaction.user.send(f"✅ Команда **{kwargs.get('team_name')}** создана!\nСекретный код для вступления тиммейтов: `{code}`")
            custom_success_msg = f"✅ Команда **{kwargs.get('team_name')}** создана!\nСекретный код отправлен вам в ЛС."
        except discord.Forbidden:
            custom_success_msg = f"✅ Команда **{kwargs.get('team_name')}** создана!\nСекретный код для тиммейтов: `{code}`\n\n*(Сохраните его, ваши ЛС закрыты!)*"

    elif action == "join_team_code":
        if any(p.get("user_id") == uid for p in parts):
            await interaction.followup.send("❌ Вы уже зарегистрированы!", ephemeral=True)
            return
            
        code = kwargs.get("team_code")
        team_members = [p for p in parts if p.get("team_code") == code]
        if not team_members:
            await interaction.followup.send("❌ Команда с таким кодом не найдена.", ephemeral=True)
            return
            
        team_size = ev.get("team_size", 5)
        if len(team_members) >= team_size:
            await interaction.followup.send("❌ В этой команде уже нет мест!", ephemeral=True)
            return
            
        parts.append({"user_id": uid, "team_code": code, "ign": kwargs.get("ign"), "is_captain": False})

    # Add Role
    role_id = ev.get("role_reward")
    if role_id:
        role = interaction.guild.get_role(role_id)
        if role:
            try: await interaction.user.add_roles(role)
            except discord.Forbidden: pass

    await save_events(data)
    
    # Update Embed
    try:
        emb = rebuild_event_embed(interaction.message.embeds[0], ev)
        await interaction.message.edit(embed=emb)
    except Exception:
        pass
        
    await interaction.followup.send(custom_success_msg, ephemeral=True)


# ==========================================
# PARTICIPATION UI
# ==========================================

def create_participation_view(message_id: str, event_data: dict, disabled: bool = False) -> discord.ui.View:
    view = discord.ui.View(timeout=None)
    
    async def cb_reg_solo(interaction: discord.Interaction):
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if ev: await interaction.response.send_modal(RegisterSoloModal(message_id, ev.get("require_info", False)))

    async def cb_reg_captain(interaction: discord.Interaction):
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if ev: await interaction.response.send_modal(RegisterTeamCaptainModal(message_id, ev.get("team_size", 5), ev.get("require_info", False)))

    async def cb_create_code(interaction: discord.Interaction):
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if ev: await interaction.response.send_modal(CreateTeamCodeModal(message_id, ev.get("require_info", False)))

    async def cb_join_code(interaction: discord.Interaction):
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if ev: await interaction.response.send_modal(JoinTeamCodeModal(message_id, ev.get("require_info", False)))

    async def cb_leave(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if not ev: return
        uid = interaction.user.id
        
        parts = ev.get("participants", [])
        user_p = next((p for p in parts if p.get("user_id") == uid), None)
        if not user_p:
            await interaction.followup.send("❌ Вы не зарегистрированы.", ephemeral=True)
            return
            
        if user_p.get("is_captain"):
            code = user_p.get("team_code")
            team_members = [p for p in parts if p.get("team_code") == code]
            ev["participants"] = [p for p in parts if p.get("team_code") != code]
            await interaction.followup.send("Команда удалена, так как вы капитан.", ephemeral=True)
            
            # Remove roles from all team members
            role_id = ev.get("role_reward")
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    for tm in team_members:
                        if tm.get("user_id") != uid:
                            try:
                                m = interaction.guild.get_member(tm["user_id"])
                                if m: await m.remove_roles(role)
                            except Exception: pass
        else:
            ev["participants"] = [p for p in parts if p.get("user_id") != uid]
            await interaction.followup.send("✅ Вы покинули событие.", ephemeral=True)
            
        role_id = ev.get("role_reward")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                try: await interaction.user.remove_roles(role)
                except discord.Forbidden: pass

        await save_events(data)
        try:
            emb = rebuild_event_embed(interaction.message.embeds[0], ev)
            await interaction.message.edit(embed=emb)
        except Exception: pass

    async def cb_list(interaction: discord.Interaction):
        data = await load_events()
        ev = data.get("events", {}).get(message_id)
        if not ev: return
        parts = ev.get("participants", [])
        if not parts:
            await interaction.response.send_message("Список пуст.", ephemeral=True)
            return
            
        lines = []
        if ev["mode"] == "solo":
            for idx, p in enumerate(parts, 1):
                ign = f" [{p.get('ign')}]" if p.get('ign') and p.get('ign') != "—" else ""
                lines.append(f"{idx}. <@{p['user_id']}>{ign}")
        elif ev["mode"] == "team_captain":
            for idx, p in enumerate(parts, 1):
                lines.append(f"{idx}. Команда **{p.get('team_name')}** (Капитан: <@{p['user_id']}>)\n> {p.get('members')}")
        elif ev["mode"] == "team_code":
            teams = {}
            for p in parts:
                teams.setdefault(p.get("team_code"), []).append(p)
            idx = 1
            for code, members in teams.items():
                cap = next((m for m in members if m.get("is_captain")), members[0])
                lines.append(f"{idx}. Команда **{cap.get('team_name')}**")
                for m in members:
                    ign = f" [{m.get('ign')}]" if m.get('ign') and m.get('ign') != "—" else ""
                    lines.append(f"  - <@{m['user_id']}>{ign}")
                idx += 1
                
        text = "\n".join(lines)
        if len(text) > 2000:
            import io
            file = discord.File(io.BytesIO(text.encode('utf-8')), filename="participants.txt")
            await interaction.response.send_message(file=file, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    if event_data["type"] == "tournament":
        mode = event_data.get("mode")
        if mode == "solo":
            b = discord.ui.Button(label="Зарегистрироваться", style=discord.ButtonStyle.success, custom_id=f"ev_reg_{message_id}")
            b.callback = cb_reg_solo
            view.add_item(b)
        elif mode == "team_captain":
            b = discord.ui.Button(label="Регистрация команды", style=discord.ButtonStyle.success, custom_id=f"ev_reg_{message_id}")
            b.callback = cb_reg_captain
            view.add_item(b)
        elif mode == "team_code":
            b1 = discord.ui.Button(label="Создать команду", style=discord.ButtonStyle.primary, custom_id=f"ev_cre_{message_id}")
            b1.callback = cb_create_code
            view.add_item(b1)
            b2 = discord.ui.Button(label="Вступить по коду", style=discord.ButtonStyle.secondary, custom_id=f"ev_join_{message_id}")
            b2.callback = cb_join_code
            view.add_item(b2)
            
        bleave = discord.ui.Button(label="Покинуть", style=discord.ButtonStyle.danger, custom_id=f"ev_leave_{message_id}")
        bleave.callback = cb_leave
        view.add_item(bleave)
        
        blist = discord.ui.Button(label="Список", style=discord.ButtonStyle.secondary, custom_id=f"ev_list_{message_id}")
        blist.callback = cb_list
        view.add_item(blist)
        
    else: # poll
        for idx, opt in enumerate(event_data["options"]):
            b = discord.ui.Button(label=opt[:80], style=discord.ButtonStyle.primary, custom_id=f"ev_vote_{message_id}_{idx}")
            
            async def cb_vote(interaction: discord.Interaction, opt_idx=idx):
                await interaction.response.defer(ephemeral=True)
                data = await load_events()
                ev = data.get("events", {}).get(message_id)
                if not ev or ev["status"] != "open":
                    await interaction.followup.send("❌ Опрос закрыт.", ephemeral=True)
                    return
                    
                uid = str(interaction.user.id)
                votes = ev.setdefault("votes", {})
                user_votes = votes.setdefault(uid, [])
                
                if ev.get("multi_select"):
                    if opt_idx in user_votes: user_votes.remove(opt_idx)
                    else: user_votes.append(opt_idx)
                else:
                    user_votes.clear()
                    user_votes.append(opt_idx)
                    
                await save_events(data)
                try:
                    emb = rebuild_event_embed(interaction.message.embeds[0], ev)
                    await interaction.message.edit(embed=emb)
                except Exception: pass
                await interaction.followup.send("✅ Голос засчитан!", ephemeral=True)
                
            b.callback = cb_vote
            view.add_item(b)

    if disabled:
        for item in view.children:
            item.disabled = True
    return view


# ==========================================
# MANAGEMENT
# ==========================================

class EventNotifyModal(discord.ui.Modal, title="Рассылка участникам"):
    def __init__(self, bot, message_id: str):
        super().__init__()
        self.bot = bot
        self.message_id = message_id
        
        self.inp_text = discord.ui.TextInput(
            label="Текст сообщения", style=discord.TextStyle.paragraph,
            required=True, max_length=2000
        )
        self.add_item(self.inp_text)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        text = self.inp_text.value.strip()

        data = await load_events()
        ev = data.get("events", {}).get(self.message_id)
        if not ev:
            await interaction.followup.send("❌ Событие не найдено.", ephemeral=True)
            return
        if not ev.get("participants"):
            await interaction.followup.send("❌ Список участников пуст. Рассылать некому.", ephemeral=True)
            return

        user_ids = list(set(p.get("user_id") for p in ev.get("participants", []) if p.get("user_id")))
        await interaction.followup.send(
            f"Начинаю рассылку для {len(user_ids)} участников... Пожалуйста, подождите.", ephemeral=True
        )

        result = await events_core.notify_participants(self.bot, interaction.guild, self.message_id, text)

        await interaction.followup.send(
            f"✅ Рассылка завершена!\nУспешно: {result['success']}\nНе удалось (ЛС закрыты): {result['failed']}",
            ephemeral=True,
        )


class EventManageSelect(discord.ui.Select):
    def __init__(self, bot, options: list[discord.SelectOption]):
        super().__init__(placeholder="Выберите событие для управления...", min_values=1, max_values=1, options=options)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        msg_id = self.values[0]
        data = await load_events()
        ev = data.get("events", {}).get(msg_id)
        if not ev:
            await interaction.response.send_message("Событие не найдено.", ephemeral=True)
            return
            
        emb = discord.Embed(title=f"⚙️ Управление: {ev['title']}", color=discord.Color.orange())
        emb.add_field(name="Тип", value=ev['type'])
        emb.add_field(name="Статус", value="Открыто" if ev['status'] == 'open' else "Закрыто")
        emb.add_field(name="Участников/Голосов", value=str(len(ev.get('participants', [])) or len(ev.get('votes', {}))))
        
        view = discord.ui.View(timeout=None)
        
        btn_notify = discord.ui.Button(label="📢 Рассылка", style=discord.ButtonStyle.primary)
        btn_close = discord.ui.Button(label="🛑 Закрыть", style=discord.ButtonStyle.secondary)
        btn_delete = discord.ui.Button(label="🗑️ Удаление", style=discord.ButtonStyle.danger)
        
        async def cb_notify(i: discord.Interaction):
            await i.response.send_modal(EventNotifyModal(self.bot, msg_id))
            
        async def cb_close(i: discord.Interaction):
            await events_core.close_event(self.bot, msg_id)
            await i.response.send_message("✅ Событие закрыто.", ephemeral=True)

        async def cb_delete(i: discord.Interaction):
            await events_core.delete_event(self.bot, i.guild, msg_id)
            await i.response.send_message("🗑️ Событие удалено.", ephemeral=True)

        btn_notify.callback = cb_notify
        btn_close.callback = cb_close
        btn_delete.callback = cb_delete
        
        if ev['type'] == 'tournament': view.add_item(btn_notify)
        view.add_item(btn_close)
        view.add_item(btn_delete)
        
        await interaction.response.edit_message(embed=emb, view=view)


# ==========================================
# COG
# ==========================================

class Events(commands.Cog):
    event_group = app_commands.Group(
        name="event",
        description="Система турниров и событий",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_event_views_loaded", False): return
        data = await load_events()
        for msg_id, ev_data in data.get("events", {}).items():
            if ev_data.get("status") == "open":
                self.bot.add_view(create_participation_view(msg_id, ev_data), message_id=int(msg_id))
        self.bot._event_views_loaded = True

    @event_group.command(name="setup", description="Запустить конструктор событий/опросов")
    async def event_setup(self, interaction: discord.Interaction):
        view = EventBuilderView(self.bot, interaction.user.id)
        await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)

    @event_group.command(name="manage", description="Управление активными событиями")
    async def event_manage(self, interaction: discord.Interaction):
        data = await load_events()
        evs = data.get("events", {})
        opts = []
        for mid, ev in evs.items():
            status = "🟢" if ev["status"] == "open" else "🔴"
            opts.append(discord.SelectOption(label=ev["title"][:90], description=f"ID: {mid}", value=mid, emoji=status))
            
        if not opts:
            await interaction.response.send_message("Нет активных событий.", ephemeral=True)
            return
            
        view = discord.ui.View(timeout=600)
        view.add_item(EventManageSelect(self.bot, opts[:25]))
        await interaction.response.send_message("Выберите событие для управления:", view=view, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Events(bot))
