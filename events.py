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

import embed_style
import events_core
import i18n
import slash_registry
import settings_db

logger = logging.getLogger("chetbot.events")
EVENTS_FILE = "events_data.json"


def load_events(guild_id: int) -> dict:
    data = settings_db.get(guild_id, "events", {})
    if "events" not in data:
        data["events"] = {}
    return data


def save_events(guild_id: int, data: dict):
    settings_db.put(guild_id, "events", data)


def upsert_embed_field(embed: discord.Embed, name: str, value: str, inline: bool = False):
    for idx, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(idx, name=name, value=value, inline=inline)
            return
    embed.add_field(name=name, value=value, inline=inline)


def rebuild_event_embed(embed: discord.Embed, event_data: dict, lang: str) -> discord.Embed:
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
            upsert_embed_field(
                emb,
                i18n.t("events.field.limit", lang),
                i18n.t("events.field.limit_value", lang, current=current_count, max=max_limit),
                inline=True,
            )
        else:
            upsert_embed_field(emb, i18n.t("events.field.participants", lang), str(current_count), inline=True)
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
            upsert_embed_field(emb, opt, i18n.t("events.poll.bar", lang, bars=bars, pct=pct, count=c), inline=False)
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


class TextModal(discord.ui.Modal):
    def __init__(self, draft: DraftEvent, view, lang: str):
        super().__init__(title=i18n.t("events.modal.text.title", lang))
        self.draft = draft
        self.builder_view = view

        self.inp_title = discord.ui.TextInput(label=i18n.t("events.modal.text.title_label", lang), style=discord.TextStyle.short, default=draft.title, required=True, max_length=100)
        self.inp_desc = discord.ui.TextInput(label=i18n.t("events.modal.text.desc_label", lang), style=discord.TextStyle.paragraph, default=draft.description, required=True, max_length=2000)
        self.inp_banner = discord.ui.TextInput(label=i18n.t("events.modal.text.banner_label", lang), style=discord.TextStyle.short, default=draft.banner_url, required=False)
        self.add_item(self.inp_title)
        self.add_item(self.inp_desc)
        self.add_item(self.inp_banner)

    async def on_submit(self, interaction: discord.Interaction):
        self.draft.title = self.inp_title.value.strip()
        self.draft.description = self.inp_desc.value.strip()
        self.draft.banner_url = self.inp_banner.value.strip()
        await self.builder_view.refresh(interaction)


class LimitsModal(discord.ui.Modal):
    def __init__(self, draft: DraftEvent, view, lang: str):
        super().__init__(title=i18n.t("events.modal.limits.title", lang))
        self.draft = draft
        self.builder_view = view
        self.lang = lang

        self.inp_max = discord.ui.TextInput(label=i18n.t("events.modal.limits.max", lang), style=discord.TextStyle.short, default=str(draft.max_limit), required=True)
        self.inp_team = discord.ui.TextInput(label=i18n.t("events.modal.limits.team", lang), style=discord.TextStyle.short, default=str(draft.team_size), required=True)
        self.add_item(self.inp_max)
        if draft.mode != "solo":
            self.add_item(self.inp_team)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.draft.max_limit = max(0, int(self.inp_max.value.strip()))
            if self.draft.mode != "solo":
                self.draft.team_size = max(2, int(self.inp_team.value.strip()))
        except ValueError:
            await interaction.response.send_message(i18n.t("events.error.not_number", self.lang), ephemeral=True)
            return
        await self.builder_view.refresh(interaction)


class OptionsModal(discord.ui.Modal):
    def __init__(self, draft: DraftEvent, view, lang: str):
        super().__init__(title=i18n.t("events.modal.options.title", lang))
        self.draft = draft
        self.builder_view = view
        self.lang = lang

        self.inp_opts = discord.ui.TextInput(label=i18n.t("events.modal.options.label", lang), style=discord.TextStyle.paragraph, default="\n".join(draft.options), required=True, max_length=1000)
        self.add_item(self.inp_opts)

    async def on_submit(self, interaction: discord.Interaction):
        lines = [x.strip() for x in self.inp_opts.value.strip().split("\n") if x.strip()]
        if len(lines) > 10:
            lines = lines[:10]
        if len(lines) < 2:
            await interaction.response.send_message(i18n.t("events.error.min_options", self.lang), ephemeral=True)
            return
        self.draft.options = lines
        await self.builder_view.refresh(interaction)


class EventPublishSelect(discord.ui.ChannelSelect):
    def __init__(self, view, lang: str):
        super().__init__(placeholder=i18n.t("events.publish.placeholder", lang), channel_types=[discord.ChannelType.text, discord.ChannelType.news], min_values=1, max_values=1, row=4)
        self.builder_view = view
        self.lang = lang

    async def callback(self, interaction: discord.Interaction):
        channel = self.values[0]
        draft = self.builder_view.draft
        spec = {
            "type": draft.type,
            "title": draft.title,
            "description": draft.description,
            "banner_url": draft.banner_url,
            "mode": draft.mode,
            "require_info": draft.require_info,
            "max_limit": draft.max_limit,
            "team_size": draft.team_size,
            "role_reward": draft.role_reward,
            "ping": draft.ping,
            "options": draft.options,
            "multi_select": draft.multi_select,
        }
        error = events_core.validate_event_spec(spec)
        if error:
            await interaction.response.send_message(i18n.t("events.error.invalid_spec", self.lang), ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)
        await self.builder_view.publish(interaction, channel)


class EventBuilderView(discord.ui.View):
    def __init__(self, bot, author_id: int, lang: str):
        super().__init__(timeout=600)
        self.bot = bot
        self.lang = lang
        self.draft = DraftEvent(author_id)
        self.update_buttons()

    def build_embed(self) -> discord.Embed:
        d = self.draft
        lang = self.lang
        emb = discord.Embed(title=i18n.t("events.builder.title", lang), color=embed_style.GOLD)
        type_val = i18n.t("events.builder.type_tournament", lang) if d.type == "tournament" else i18n.t("events.builder.type_poll", lang)
        emb.add_field(name=i18n.t("events.builder.type", lang), value=type_val, inline=False)
        emb.add_field(name=i18n.t("events.builder.name", lang), value=d.title or i18n.t("events.builder.not_set", lang), inline=True)
        desc = d.description[:100] + "..." if len(d.description) > 100 else d.description
        emb.add_field(name=i18n.t("events.builder.description", lang), value=desc or i18n.t("events.builder.not_set", lang), inline=True)

        if d.type == "tournament":
            mode_str = {
                "solo": i18n.t("events.builder.mode.solo", lang),
                "team_captain": i18n.t("events.builder.mode.team_captain", lang),
                "team_code": i18n.t("events.builder.mode.team_code", lang),
            }.get(d.mode)
            emb.add_field(name=i18n.t("events.builder.format", lang), value=mode_str, inline=True)
            emb.add_field(name=i18n.t("events.builder.form", lang), value=i18n.t("events.builder.yes", lang) if d.require_info else i18n.t("events.builder.no", lang), inline=True)
            limits = f"{d.max_limit if d.max_limit > 0 else i18n.t('events.builder.unlimited', lang)}"
            if d.mode != "solo":
                limits += i18n.t("events.builder.team_size_suffix", lang, size=d.team_size)
            emb.add_field(name=i18n.t("events.builder.limits", lang), value=limits, inline=True)
            emb.add_field(name=i18n.t("events.builder.role", lang), value=f"<@&{d.role_reward}>" if d.role_reward else i18n.t("events.builder.no", lang), inline=True)
        else:
            opts = "\n".join(f"• {x}" for x in d.options) if d.options else i18n.t("events.builder.no_options", lang)
            emb.add_field(name=i18n.t("events.builder.options", lang), value=opts, inline=False)
            emb.add_field(name=i18n.t("events.builder.multi", lang), value=i18n.t("events.builder.yes", lang) if d.multi_select else i18n.t("events.builder.no", lang), inline=True)

        ping_str = {"none": i18n.t("events.builder.ping_none", lang), "everyone": "@everyone", "here": "@here"}.get(d.ping, f"<@&{d.ping}>")
        emb.add_field(name=i18n.t("events.builder.ping", lang), value=ping_str, inline=True)
        if d.banner_url:
            emb.set_thumbnail(url=d.banner_url)
        return emb

    def update_buttons(self):
        self.clear_items()
        d = self.draft
        lang = self.lang

        btn_type = discord.ui.Button(label=i18n.t("events.builder.btn.type", lang), style=discord.ButtonStyle.primary, row=0)
        btn_type.callback = self.cb_type
        self.add_item(btn_type)

        btn_text = discord.ui.Button(label=i18n.t("events.builder.btn.text", lang), style=discord.ButtonStyle.secondary, row=0)
        btn_text.callback = self.cb_text
        self.add_item(btn_text)

        btn_ping = discord.ui.Button(label=i18n.t("events.builder.btn.ping", lang, ping=str(d.ping)), style=discord.ButtonStyle.secondary, row=0)
        btn_ping.callback = self.cb_ping
        self.add_item(btn_ping)

        if d.type == "tournament":
            btn_mode = discord.ui.Button(label=i18n.t("events.builder.btn.mode", lang, mode=d.mode), style=discord.ButtonStyle.secondary, row=1)
            btn_mode.callback = self.cb_mode
            self.add_item(btn_mode)

            form_label = i18n.t("events.builder.btn.form_on", lang) if d.require_info else i18n.t("events.builder.btn.form_off", lang)
            btn_info = discord.ui.Button(label=form_label, style=discord.ButtonStyle.secondary, row=1)
            btn_info.callback = self.cb_info
            self.add_item(btn_info)

            btn_limits = discord.ui.Button(label=i18n.t("events.builder.btn.limits", lang), style=discord.ButtonStyle.secondary, row=1)
            btn_limits.callback = self.cb_limits
            self.add_item(btn_limits)

            role_select = discord.ui.RoleSelect(placeholder=i18n.t("events.builder.role_placeholder", lang), min_values=1, max_values=1, row=2)
            role_select.callback = self.cb_role
            self.add_item(role_select)
        else:
            btn_opts = discord.ui.Button(label=i18n.t("events.builder.btn.options", lang), style=discord.ButtonStyle.secondary, row=1)
            btn_opts.callback = self.cb_opts
            self.add_item(btn_opts)

            multi_label = i18n.t("events.builder.btn.multi_on", lang) if d.multi_select else i18n.t("events.builder.btn.multi_off", lang)
            btn_multi = discord.ui.Button(label=multi_label, style=discord.ButtonStyle.secondary, row=1)
            btn_multi.callback = self.cb_multi
            self.add_item(btn_multi)

        self.add_item(EventPublishSelect(self, lang))

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
        await interaction.response.send_modal(TextModal(self.draft, self, self.lang))

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
        await interaction.response.send_modal(LimitsModal(self.draft, self, self.lang))

    async def cb_role(self, interaction: discord.Interaction):
        self.draft.role_reward = interaction.data["values"][0]
        await self.refresh(interaction)

    async def cb_opts(self, interaction: discord.Interaction):
        await interaction.response.send_modal(OptionsModal(self.draft, self, self.lang))

    async def cb_multi(self, interaction: discord.Interaction):
        self.draft.multi_select = not self.draft.multi_select
        await self.refresh(interaction)

    async def publish(self, interaction: discord.Interaction, channel: discord.TextChannel):
        d = self.draft

        # ChannelSelect возвращает AppCommandChannel, у которого нет .send()
        # Нужно получить полный объект TextChannel
        resolved_channel = self.bot.get_channel(channel.id)
        if not resolved_channel:
            try:
                resolved_channel = await self.bot.fetch_channel(channel.id)
            except Exception:
                await interaction.edit_original_response(content=i18n.t("events.error.channel_access", self.lang))
                return

        spec = {
            "type": d.type,
            "title": d.title,
            "description": d.description,
            "banner_url": d.banner_url,
            "mode": d.mode,
            "require_info": d.require_info,
            "max_limit": d.max_limit,
            "team_size": d.team_size,
            "role_reward": d.role_reward,
            "ping": d.ping,
            "options": d.options,
            "multi_select": d.multi_select,
        }
        msg = await events_core.publish_event(self.bot, resolved_channel, spec, author_id=d.author_id)

        self.clear_items()
        await interaction.edit_original_response(
            content=i18n.t("events.published", self.lang, channel=resolved_channel.mention, message_id=msg.id),
            embed=None,
            view=None,
        )


# ==========================================
# REGISTRATION MODALS
# ==========================================

class RegisterSoloModal(discord.ui.Modal):
    def __init__(self, message_id: str, require_info: bool, lang: str):
        super().__init__(title=i18n.t("events.modal.register_solo.title", lang))
        self.message_id = message_id
        self.require_info = require_info
        if require_info:
            self.inp_ign = discord.ui.TextInput(label=i18n.t("events.modal.register_solo.ign", lang), style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)
        else:
            self.inp_ign = discord.ui.TextInput(
                label=i18n.t("events.modal.register_solo.confirm", lang),
                style=discord.TextStyle.short,
                default=i18n.t("events.modal.register_solo.confirm_default", lang),
                required=True,
                max_length=20,
            )
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        ign = self.inp_ign.value.strip() if self.require_info else i18n.t("events.ign_placeholder", lang)
        await handle_registration(interaction, self.message_id, "solo", ign=ign)


class RegisterTeamCaptainModal(discord.ui.Modal):
    def __init__(self, message_id: str, team_size: int, require_info: bool, lang: str):
        super().__init__(title=i18n.t("events.modal.register_team.title", lang))
        self.message_id = message_id
        self.require_info = require_info
        self.inp_team = discord.ui.TextInput(label=i18n.t("events.modal.register_team.name", lang), style=discord.TextStyle.short, required=True, max_length=50)
        self.inp_members = discord.ui.TextInput(label=i18n.t("events.modal.register_team.members", lang, size=team_size), style=discord.TextStyle.paragraph, required=True, max_length=1000)
        self.add_item(self.inp_team)
        self.add_item(self.inp_members)

    async def on_submit(self, interaction: discord.Interaction):
        await handle_registration(
            interaction, self.message_id, "team_captain",
            team_name=self.inp_team.value.strip(),
            members=self.inp_members.value.strip()
        )


class CreateTeamCodeModal(discord.ui.Modal):
    def __init__(self, message_id: str, require_info: bool, lang: str):
        super().__init__(title=i18n.t("events.modal.create_team.title", lang))
        self.message_id = message_id
        self.require_info = require_info
        self.inp_team = discord.ui.TextInput(label=i18n.t("events.modal.register_team.name", lang), style=discord.TextStyle.short, required=True, max_length=50)
        self.add_item(self.inp_team)
        if require_info:
            self.inp_ign = discord.ui.TextInput(label=i18n.t("events.modal.create_team.captain_ign", lang), style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        ign = self.inp_ign.value.strip() if self.require_info else i18n.t("events.ign_placeholder", lang)
        await handle_registration(interaction, self.message_id, "create_team_code", team_name=self.inp_team.value.strip(), ign=ign)


class JoinTeamCodeModal(discord.ui.Modal):
    def __init__(self, message_id: str, require_info: bool, lang: str):
        super().__init__(title=i18n.t("events.modal.join_team.title", lang))
        self.message_id = message_id
        self.require_info = require_info
        self.inp_code = discord.ui.TextInput(label=i18n.t("events.modal.join_team.code", lang), style=discord.TextStyle.short, required=True, max_length=20)
        self.add_item(self.inp_code)
        if require_info:
            self.inp_ign = discord.ui.TextInput(label=i18n.t("events.modal.join_team.ign", lang), style=discord.TextStyle.short, required=True, max_length=50)
            self.add_item(self.inp_ign)

    async def on_submit(self, interaction: discord.Interaction):
        lang = i18n.lang_for(interaction.guild_id)
        ign = self.inp_ign.value.strip() if self.require_info else i18n.t("events.ign_placeholder", lang)
        await handle_registration(interaction, self.message_id, "join_team_code", team_code=self.inp_code.value.strip().upper(), ign=ign)


async def handle_registration(interaction: discord.Interaction, message_id: str, action: str, **kwargs):
    await interaction.response.defer(ephemeral=True)
    lang = i18n.lang_for(interaction.guild_id)
    data = load_events(interaction.guild_id)
    ev = data.get("events", {}).get(message_id)
    if not ev:
        await interaction.followup.send(i18n.t("events.error.not_found", lang), ephemeral=True)
        return
    if ev["status"] != "open":
        await interaction.followup.send(i18n.t("events.error.registration_closed", lang), ephemeral=True)
        return

    uid = interaction.user.id
    parts = ev.setdefault("participants", [])
    ign_ph = i18n.t("events.ign_placeholder", lang)

    if action in ["solo", "team_captain", "create_team_code"]:
        if any(p.get("user_id") == uid for p in parts):
            await interaction.followup.send(i18n.t("events.error.already_registered", lang), ephemeral=True)
            return

    max_limit = ev.get("max_limit", 0)
    custom_success_msg = i18n.t("events.success.registered", lang)

    if action == "solo":
        if max_limit > 0 and len(parts) >= max_limit:
            await interaction.followup.send(i18n.t("events.error.no_slots", lang), ephemeral=True)
            return
        parts.append({"user_id": uid, "ign": kwargs.get("ign")})

    elif action == "team_captain":
        if max_limit > 0 and len(parts) >= max_limit:
            await interaction.followup.send(i18n.t("events.error.no_team_slots", lang), ephemeral=True)
            return
        parts.append({"user_id": uid, "team_name": kwargs.get("team_name"), "members": kwargs.get("members")})

    elif action == "create_team_code":
        teams = set(p.get("team_code") for p in parts if p.get("team_code"))
        if max_limit > 0 and len(teams) >= max_limit:
            await interaction.followup.send(i18n.t("events.error.no_team_slots", lang), ephemeral=True)
            return
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        parts.append({"user_id": uid, "team_name": kwargs.get("team_name"), "team_code": code, "ign": kwargs.get("ign"), "is_captain": True})

        try:
            await interaction.user.send(i18n.t("events.team.created_dm", lang, name=kwargs.get("team_name"), code=code))
            custom_success_msg = i18n.t("events.team.created_ephemeral", lang, name=kwargs.get("team_name"))
        except discord.Forbidden:
            custom_success_msg = i18n.t("events.team.created_no_dm", lang, name=kwargs.get("team_name"), code=code)

    elif action == "join_team_code":
        if any(p.get("user_id") == uid for p in parts):
            await interaction.followup.send(i18n.t("events.error.already_registered", lang), ephemeral=True)
            return

        code = kwargs.get("team_code")
        team_members = [p for p in parts if p.get("team_code") == code]
        if not team_members:
            await interaction.followup.send(i18n.t("events.error.team_not_found", lang), ephemeral=True)
            return

        team_size = ev.get("team_size", 5)
        if len(team_members) >= team_size:
            await interaction.followup.send(i18n.t("events.error.team_full", lang), ephemeral=True)
            return

        parts.append({"user_id": uid, "team_code": code, "ign": kwargs.get("ign"), "is_captain": False})

    # Add Role
    role_id = ev.get("role_reward")
    if role_id:
        role = interaction.guild.get_role(role_id)
        if role:
            try: await interaction.user.add_roles(role)
            except discord.Forbidden: pass

    save_events(interaction.guild_id, data)

    # Update Embed
    try:
        emb = rebuild_event_embed(interaction.message.embeds[0], ev, lang)
        await interaction.message.edit(embed=emb)
    except Exception:
        pass

    await interaction.followup.send(custom_success_msg, ephemeral=True)


# ==========================================
# PARTICIPATION UI
# ==========================================

def create_participation_view(message_id: str, event_data: dict, disabled: bool = False, lang: str | None = None) -> discord.ui.View:
    view = discord.ui.View(timeout=None)

    async def cb_reg_solo(interaction: discord.Interaction):
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if ev:
            await interaction.response.send_modal(RegisterSoloModal(message_id, ev.get("require_info", False), l))

    async def cb_reg_captain(interaction: discord.Interaction):
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if ev:
            await interaction.response.send_modal(RegisterTeamCaptainModal(message_id, ev.get("team_size", 5), ev.get("require_info", False), l))

    async def cb_create_code(interaction: discord.Interaction):
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if ev:
            await interaction.response.send_modal(CreateTeamCodeModal(message_id, ev.get("require_info", False), l))

    async def cb_join_code(interaction: discord.Interaction):
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if ev:
            await interaction.response.send_modal(JoinTeamCodeModal(message_id, ev.get("require_info", False), l))

    async def cb_leave(interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if not ev:
            return
        uid = interaction.user.id
        ign_ph = i18n.t("events.ign_placeholder", l)

        parts = ev.get("participants", [])
        user_p = next((p for p in parts if p.get("user_id") == uid), None)
        if not user_p:
            await interaction.followup.send(i18n.t("events.error.not_registered", l), ephemeral=True)
            return

        if user_p.get("is_captain"):
            code = user_p.get("team_code")
            team_members = [p for p in parts if p.get("team_code") == code]
            ev["participants"] = [p for p in parts if p.get("team_code") != code]
            await interaction.followup.send(i18n.t("events.team.disbanded", l), ephemeral=True)

            role_id = ev.get("role_reward")
            if role_id:
                role = interaction.guild.get_role(role_id)
                if role:
                    for tm in team_members:
                        if tm.get("user_id") != uid:
                            try:
                                m = interaction.guild.get_member(tm["user_id"])
                                if m:
                                    await m.remove_roles(role)
                            except Exception:
                                pass
        else:
            ev["participants"] = [p for p in parts if p.get("user_id") != uid]
            await interaction.followup.send(i18n.t("events.left", l), ephemeral=True)

        role_id = ev.get("role_reward")
        if role_id:
            role = interaction.guild.get_role(role_id)
            if role:
                try:
                    await interaction.user.remove_roles(role)
                except discord.Forbidden:
                    pass

        save_events(interaction.guild_id, data)
        try:
            emb = rebuild_event_embed(interaction.message.embeds[0], ev, l)
            await interaction.message.edit(embed=emb)
        except Exception:
            pass

    async def cb_list(interaction: discord.Interaction):
        l = i18n.lang_for(interaction.guild_id)
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(message_id)
        if not ev:
            return
        parts = ev.get("participants", [])
        if not parts:
            await interaction.response.send_message(i18n.t("events.list.empty", l), ephemeral=True)
            return

        ign_ph = i18n.t("events.ign_placeholder", l)
        lines = []
        if ev["mode"] == "solo":
            for idx, p in enumerate(parts, 1):
                ign = f" [{p.get('ign')}]" if p.get("ign") and p.get("ign") != ign_ph else ""
                lines.append(f"{idx}. <@{p['user_id']}>{ign}")
        elif ev["mode"] == "team_captain":
            for idx, p in enumerate(parts, 1):
                lines.append(i18n.t("events.list.team_captain", l, idx=idx, name=p.get("team_name"), user_id=p["user_id"], members=p.get("members")))
        elif ev["mode"] == "team_code":
            teams = {}
            for p in parts:
                teams.setdefault(p.get("team_code"), []).append(p)
            idx = 1
            for code, members in teams.items():
                cap = next((m for m in members if m.get("is_captain")), members[0])
                lines.append(i18n.t("events.list.team_code_header", l, idx=idx, name=cap.get("team_name")))
                for m in members:
                    ign = f" [{m.get('ign')}]" if m.get("ign") and m.get("ign") != ign_ph else ""
                    lines.append(f"  - <@{m['user_id']}>{ign}")
                idx += 1

        text = "\n".join(lines)
        if len(text) > 2000:
            import io
            file = discord.File(io.BytesIO(text.encode("utf-8")), filename=i18n.t("events.participants_file", l))
            await interaction.response.send_message(file=file, ephemeral=True)
        else:
            await interaction.response.send_message(text, ephemeral=True)

    btn_lang = lang or i18n.DEFAULT_LANGUAGE
    if event_data["type"] == "tournament":
        mode = event_data.get("mode")
        if mode == "solo":
            b = discord.ui.Button(label=i18n.t("events.button.register", btn_lang), style=discord.ButtonStyle.success, custom_id=f"ev_reg_{message_id}")
            b.callback = cb_reg_solo
            view.add_item(b)
        elif mode == "team_captain":
            b = discord.ui.Button(label=i18n.t("events.button.register_team", btn_lang), style=discord.ButtonStyle.success, custom_id=f"ev_reg_{message_id}")
            b.callback = cb_reg_captain
            view.add_item(b)
        elif mode == "team_code":
            b1 = discord.ui.Button(label=i18n.t("events.button.create_team", btn_lang), style=discord.ButtonStyle.primary, custom_id=f"ev_cre_{message_id}")
            b1.callback = cb_create_code
            view.add_item(b1)
            b2 = discord.ui.Button(label=i18n.t("events.button.join_code", btn_lang), style=discord.ButtonStyle.secondary, custom_id=f"ev_join_{message_id}")
            b2.callback = cb_join_code
            view.add_item(b2)

        bleave = discord.ui.Button(label=i18n.t("events.button.leave", btn_lang), style=discord.ButtonStyle.danger, custom_id=f"ev_leave_{message_id}")
        bleave.callback = cb_leave
        view.add_item(bleave)

        blist = discord.ui.Button(label=i18n.t("events.button.list", btn_lang), style=discord.ButtonStyle.secondary, custom_id=f"ev_list_{message_id}")
        blist.callback = cb_list
        view.add_item(blist)

    else:
        for idx, opt in enumerate(event_data["options"]):
            b = discord.ui.Button(label=opt[:80], style=discord.ButtonStyle.primary, custom_id=f"ev_vote_{message_id}_{idx}")

            async def cb_vote(interaction: discord.Interaction, opt_idx=idx):
                l = i18n.lang_for(interaction.guild_id)
                await interaction.response.defer(ephemeral=True)
                data = load_events(interaction.guild_id)
                ev = data.get("events", {}).get(message_id)
                if not ev or ev["status"] != "open":
                    await interaction.followup.send(i18n.t("events.error.poll_closed", l), ephemeral=True)
                    return

                uid = str(interaction.user.id)
                votes = ev.setdefault("votes", {})
                user_votes = votes.setdefault(uid, [])

                if ev.get("multi_select"):
                    if opt_idx in user_votes:
                        user_votes.remove(opt_idx)
                    else:
                        user_votes.append(opt_idx)
                else:
                    user_votes.clear()
                    user_votes.append(opt_idx)

                save_events(interaction.guild_id, data)
                try:
                    emb = rebuild_event_embed(interaction.message.embeds[0], ev, l)
                    await interaction.message.edit(embed=emb)
                except Exception:
                    pass
                await interaction.followup.send(i18n.t("events.vote.counted", l), ephemeral=True)

            b.callback = cb_vote
            view.add_item(b)

    if disabled:
        for item in view.children:
            item.disabled = True
    return view


# ==========================================
# MANAGEMENT
# ==========================================

class EventNotifyModal(discord.ui.Modal):
    def __init__(self, bot, message_id: str, lang: str):
        super().__init__(title=i18n.t("events.notify.modal.title", lang))
        self.bot = bot
        self.message_id = message_id
        self.lang = lang

        self.inp_text = discord.ui.TextInput(
            label=i18n.t("events.notify.modal.label", lang), style=discord.TextStyle.paragraph,
            required=True, max_length=2000
        )
        self.add_item(self.inp_text)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        lang = self.lang
        text = self.inp_text.value.strip()

        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(self.message_id)
        if not ev:
            await interaction.followup.send(i18n.t("events.error.not_found", lang), ephemeral=True)
            return
        if not ev.get("participants"):
            await interaction.followup.send(i18n.t("events.notify.empty", lang), ephemeral=True)
            return

        user_ids = list(set(p.get("user_id") for p in ev.get("participants", []) if p.get("user_id")))
        await interaction.followup.send(
            i18n.t("events.notify.start", lang, count=len(user_ids)), ephemeral=True
        )

        result = await events_core.notify_participants(self.bot, interaction.guild_id, self.message_id, text)

        await interaction.followup.send(
            i18n.t("events.notify.done", lang, success=result["success"], failed=result["failed"]),
            ephemeral=True,
        )


class EventManageSelect(discord.ui.Select):
    def __init__(self, bot, options: list[discord.SelectOption], lang: str):
        super().__init__(placeholder=i18n.t("events.manage.placeholder", lang), min_values=1, max_values=1, options=options)
        self.bot = bot
        self.lang = lang

    async def callback(self, interaction: discord.Interaction):
        lang = self.lang
        msg_id = self.values[0]
        data = load_events(interaction.guild_id)
        ev = data.get("events", {}).get(msg_id)
        if not ev:
            await interaction.response.send_message(i18n.t("events.manage.not_found", lang), ephemeral=True)
            return

        emb = discord.Embed(title=i18n.t("events.manage.title", lang, title=ev["title"]), color=embed_style.WARN)
        emb.add_field(name=i18n.t("events.manage.type", lang), value=ev["type"])
        status_val = i18n.t("events.manage.status_open", lang) if ev["status"] == "open" else i18n.t("events.manage.status_closed", lang)
        emb.add_field(name=i18n.t("events.manage.status", lang), value=status_val)
        emb.add_field(name=i18n.t("events.manage.count", lang), value=str(len(ev.get("participants", [])) or len(ev.get("votes", {}))))

        view = discord.ui.View(timeout=None)

        btn_notify = discord.ui.Button(label=i18n.t("events.manage.btn.notify", lang), style=discord.ButtonStyle.primary)
        btn_close = discord.ui.Button(label=i18n.t("events.manage.btn.close", lang), style=discord.ButtonStyle.secondary)
        btn_delete = discord.ui.Button(label=i18n.t("events.manage.btn.delete", lang), style=discord.ButtonStyle.danger)

        async def cb_notify(i: discord.Interaction):
            await i.response.send_modal(EventNotifyModal(self.bot, msg_id, lang))

        async def cb_close(i: discord.Interaction):
            await events_core.close_event(self.bot, i.guild_id, msg_id)
            await i.response.send_message(i18n.t("events.manage.closed", lang), ephemeral=True)

        async def cb_delete(i: discord.Interaction):
            await events_core.delete_event(self.bot, i.guild_id, msg_id)
            await i.response.send_message(i18n.t("events.manage.deleted", lang), ephemeral=True)

        btn_notify.callback = cb_notify
        btn_close.callback = cb_close
        btn_delete.callback = cb_delete

        if ev["type"] == "tournament":
            view.add_item(btn_notify)
        view.add_item(btn_close)
        view.add_item(btn_delete)

        await interaction.response.edit_message(embed=emb, view=view)


# ==========================================
# COG
# ==========================================

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        if getattr(self.bot, "_event_views_loaded", False):
            return
        for guild in self.bot.guilds:
            lang = i18n.lang_for(guild.id)
            data = load_events(guild.id)
            for msg_id, ev_data in data.get("events", {}).items():
                if ev_data.get("status") == "open":
                    self.bot.add_view(create_participation_view(msg_id, ev_data, lang=lang), message_id=int(msg_id))
        self.bot._event_views_loaded = True

    @app_commands.command(name="event", description="Система турниров и событий")
    @app_commands.describe(action="Действие: setup / manage")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="setup", value="setup"),
            app_commands.Choice(name="manage", value="manage"),
        ]
    )
    @app_commands.default_permissions(manage_guild=True)
    async def event_command(self, interaction: discord.Interaction, action: app_commands.Choice[str]):
        lang = i18n.lang_for(interaction.guild_id)
        if action.value == "setup":
            view = EventBuilderView(self.bot, interaction.user.id, lang)
            await interaction.response.send_message(embed=view.build_embed(), view=view, ephemeral=True)
            return

        data = load_events(interaction.guild_id)
        evs = data.get("events", {})
        opts = []
        for mid, ev in evs.items():
            status = "🟢" if ev["status"] == "open" else "🔴"
            opts.append(discord.SelectOption(label=ev["title"][:90], description=f"ID: {mid}", value=mid, emoji=status))

        if not opts:
            await interaction.response.send_message(i18n.t("events.manage.none", lang), ephemeral=True)
            return

        view = discord.ui.View(timeout=600)
        view.add_item(EventManageSelect(self.bot, opts[:25], lang))
        await interaction.response.send_message(i18n.t("events.manage.prompt", lang), view=view, ephemeral=True)


async def setup(bot):
    cog = Events(bot)
    slash_registry.register_events(cog)
    await bot.add_cog(cog)
