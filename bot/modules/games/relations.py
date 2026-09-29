"""Relations cog: social actions, romance (marry/divorce), pair card, leaderboards."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

import bot.core.embed_style as embed_style
import bot.core.i18n as i18n
import bot.modules.games.relations_core as relations_core
import bot.modules.games.relations_db as relations_db
import bot.core.slash_registry as slash_registry

logger = logging.getLogger("chetbot.relations")

DATE_ACTION_ID = "date"


class ProposalView(discord.ui.View):
    def __init__(
        self,
        cog: "RelationsCog",
        *,
        guild_id: int,
        proposer_id: int,
        target_id: int,
        timeout: float,
        lang: str,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.guild_id = guild_id
        self.proposer_id = proposer_id
        self.target_id = target_id
        self.lang = lang
        self.message: discord.Message | None = None

        accept = discord.ui.Button(
            label=i18n.t("relations.propose.btn_accept", lang),
            style=discord.ButtonStyle.success,
        )
        decline = discord.ui.Button(
            label=i18n.t("relations.propose.btn_decline", lang),
            style=discord.ButtonStyle.danger,
        )
        accept.callback = self._accept  # type: ignore[method-assign]
        decline.callback = self._decline  # type: ignore[method-assign]
        self.add_item(accept)
        self.add_item(decline)

    async def _disable(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_timeout(self) -> None:
        relations_db.clear_proposal(self.guild_id, self.proposer_id, self.target_id)
        await self._disable()

    async def _accept(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.target_id:
            await interaction.response.send_message(
                i18n.t("relations.propose.only_target", self.lang), ephemeral=True
            )
            return
        await self.cog.finalize_proposal_accept(interaction, self)
        self.stop()
        await self._disable()

    async def _decline(self, interaction: discord.Interaction) -> None:
        if interaction.user.id not in (self.target_id, self.proposer_id):
            await interaction.response.send_message(
                i18n.t("relations.propose.only_parties", self.lang), ephemeral=True
            )
            return
        relations_db.clear_proposal(self.guild_id, self.proposer_id, self.target_id)
        lang = i18n.lang_for(self.guild_id)
        embed = embed_style.make_embed(
            title=i18n.t("relations.propose.declined_title", lang),
            description=i18n.t(
                "relations.propose.declined_body",
                lang,
                target=f"<@{self.target_id}>",
                proposer=f"<@{self.proposer_id}>",
            ),
            color=embed_style.DANGER,
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class DivorceView(discord.ui.View):
    def __init__(
        self,
        cog: "RelationsCog",
        *,
        guild_id: int,
        initiator_id: int,
        spouse_id: int,
        mutual: bool,
        timeout: float,
        lang: str,
    ):
        super().__init__(timeout=timeout)
        self.cog = cog
        self.guild_id = guild_id
        self.initiator_id = initiator_id
        self.spouse_id = spouse_id
        self.mutual = mutual
        self.lang = lang
        self.message: discord.Message | None = None

        if mutual:
            accept = discord.ui.Button(
                label=i18n.t("relations.divorce.btn_accept", lang),
                style=discord.ButtonStyle.danger,
            )
            cancel = discord.ui.Button(
                label=i18n.t("relations.divorce.btn_stay", lang),
                style=discord.ButtonStyle.secondary,
            )
            accept.callback = self._spouse_accept  # type: ignore[method-assign]
            cancel.callback = self._cancel  # type: ignore[method-assign]
            self.add_item(accept)
            self.add_item(cancel)
        else:
            confirm = discord.ui.Button(
                label=i18n.t("relations.divorce.btn_confirm", lang),
                style=discord.ButtonStyle.danger,
            )
            cancel = discord.ui.Button(
                label=i18n.t("relations.divorce.btn_cancel", lang),
                style=discord.ButtonStyle.secondary,
            )
            confirm.callback = self._solo_confirm  # type: ignore[method-assign]
            cancel.callback = self._cancel  # type: ignore[method-assign]
            self.add_item(confirm)
            self.add_item(cancel)

    async def _disable(self) -> None:
        for item in self.children:
            if isinstance(item, discord.ui.Button):
                item.disabled = True
        if self.message is not None:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def on_timeout(self) -> None:
        await self._disable()

    async def _spouse_accept(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.spouse_id:
            await interaction.response.send_message(
                i18n.t("relations.divorce.only_spouse", self.lang), ephemeral=True
            )
            return
        await self.cog.finalize_divorce(interaction, self.initiator_id, self.spouse_id)
        self.stop()

    async def _solo_confirm(self, interaction: discord.Interaction) -> None:
        if interaction.user.id != self.initiator_id:
            await interaction.response.send_message(
                i18n.t("relations.divorce.only_initiator", self.lang), ephemeral=True
            )
            return
        await self.cog.finalize_divorce(interaction, self.initiator_id, self.spouse_id)
        self.stop()

    async def _cancel(self, interaction: discord.Interaction) -> None:
        allowed = {self.initiator_id, self.spouse_id} if self.mutual else {self.initiator_id}
        if interaction.user.id not in allowed:
            await interaction.response.send_message(
                i18n.t("relations.divorce.only_parties", self.lang), ephemeral=True
            )
            return
        lang = i18n.lang_for(self.guild_id)
        embed = embed_style.make_embed(
            title=i18n.t("relations.divorce.cancelled_title", lang),
            description=i18n.t("relations.divorce.cancelled_body", lang),
            color=embed_style.INFO,
        )
        await interaction.response.edit_message(embed=embed, view=None)
        self.stop()


class RelationsCog(commands.Cog):
    relations_group = app_commands.Group(
        name="relations",
        description="Relationship actions, cards, marriage and romance",
        guild_only=True,
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def _day_key(self, guild_id: int) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def _color_danger(self):
        return embed_style.DANGER

    async def _sync_roles(self, member: discord.Member, settings: dict, level: int) -> None:
        deserved = relations_core.deserved_reward_role_ids(settings, level)
        managed = relations_core.all_reward_role_ids(settings)
        if not managed:
            return
        current = {r.id for r in member.roles}
        to_add = [rid for rid in deserved if rid not in current]
        to_remove = [rid for rid in managed if rid in current and rid not in deserved]
        lang = i18n.lang_for(member.guild.id)
        for rid in to_add:
            role = member.guild.get_role(rid)
            if role is None:
                continue
            try:
                await member.add_roles(role, reason=i18n.t("relations.role.add_reason", lang))
            except discord.HTTPException:
                logger.debug("relations add_role failed guild=%s role=%s", member.guild.id, rid)
        for rid in to_remove:
            role = member.guild.get_role(rid)
            if role is None:
                continue
            try:
                await member.remove_roles(role, reason=i18n.t("relations.role.remove_reason", lang))
            except discord.HTTPException:
                logger.debug("relations remove_role failed guild=%s role=%s", member.guild.id, rid)

    async def _sync_married_role(self, member: discord.Member, settings: dict) -> None:
        rid_s = settings.get("married_role_id") or ""
        if not rid_s.isdigit():
            return
        role = member.guild.get_role(int(rid_s))
        if role is None:
            return
        has = relations_db.marriage_count(member.guild.id, member.id) > 0
        lang = i18n.lang_for(member.guild.id)
        try:
            if has and role not in member.roles:
                await member.add_roles(role, reason=i18n.t("relations.marriage.role_add", lang))
            elif not has and role in member.roles:
                await member.remove_roles(role, reason=i18n.t("relations.marriage.role_remove", lang))
        except discord.HTTPException:
            logger.debug("relations married_role sync failed guild=%s", member.guild.id)

    async def _announce(
        self,
        guild: discord.Guild,
        settings: dict,
        *,
        title: str,
        description: str,
        color: int | None = None,
    ) -> None:
        ch_id = settings.get("announce_channel_id") or ""
        if not ch_id.isdigit():
            return
        channel = guild.get_channel(int(ch_id))
        if not isinstance(channel, discord.TextChannel):
            return
        embed = embed_style.make_embed(
            title=title,
            description=description,
            color=color or embed_style.SUCCESS,
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            logger.debug("relations announce failed guild=%s", guild.id)

    async def _announce_level(
        self,
        guild: discord.Guild,
        settings: dict,
        member_a: discord.Member,
        member_b: discord.Member,
        new_level: int,
        hp: int,
    ) -> None:
        lang = i18n.lang_for(guild.id)
        await self._announce(
            guild,
            settings,
            title=i18n.t("relations.announce.title", lang),
            description=i18n.t(
                "relations.announce.body",
                lang,
                a=member_a.mention,
                b=member_b.mention,
                level=new_level,
                hp=hp,
            ),
        )

    def _require_enabled(
        self, interaction: discord.Interaction
    ) -> tuple[discord.Guild, discord.Member, dict, str] | None:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return None
        settings = relations_core.get_settings(interaction.guild.id)
        lang = i18n.lang_for(interaction.guild.id)
        return interaction.guild, interaction.user, settings, lang

    async def _run_action(
        self,
        interaction: discord.Interaction,
        action_id: str,
        target: discord.Member,
    ) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return

        if target.id == actor.id:
            await interaction.response.send_message(
                i18n.t("relations.self", lang), ephemeral=True
            )
            return
        if target.bot:
            await interaction.response.send_message(
                i18n.t("relations.bot_target", lang), ephemeral=True
            )
            return

        action = relations_core.find_action(settings, action_id)
        if action is None or not action.get("enabled", True):
            await interaction.response.send_message(
                i18n.t("relations.action_disabled", lang), ephemeral=True
            )
            return

        day = self._day_key(guild.id)
        used = relations_db.daily_count(guild.id, actor.id, day)
        if used >= int(settings["max_actions_per_day"]):
            await interaction.response.send_message(
                i18n.t("relations.daily_limit", lang, limit=settings["max_actions_per_day"]),
                ephemeral=True,
            )
            return

        remaining = relations_db.cooldown_remaining(guild.id, actor.id, target.id, action_id)
        if remaining > 0:
            await interaction.response.send_message(
                i18n.t("relations.cooldown", lang, seconds=int(remaining) + 1),
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        hp_gain = int(action["hp_gain"])
        married = relations_db.are_married(guild.id, actor.id, target.id)
        bonus_note = ""
        if married and int(settings["married_hp_bonus_percent"]) > 0:
            boosted = relations_core.apply_married_bonus(
                hp_gain, int(settings["married_hp_bonus_percent"])
            )
            if boosted > hp_gain:
                bonus_note = i18n.t(
                    "relations.married_bonus_note",
                    lang,
                    pct=settings["married_hp_bonus_percent"],
                )
                hp_gain = boosted

        thresholds = settings["level_thresholds"]

        def _lvl(hp: int) -> int:
            return relations_core.level_for_hp(hp, thresholds)

        pair, old_level, new_level = relations_db.apply_action_hp(
            guild.id, actor.id, target.id, hp_gain, _lvl
        )
        relations_db.set_cooldown(
            guild.id, actor.id, target.id, action_id, int(action["cooldown_sec"])
        )
        relations_db.bump_daily(guild.id, actor.id, day)

        level, into, need = relations_core.progress_to_next(int(pair["hp"]), thresholds)
        progress = (
            i18n.t("relations.progress_max", lang)
            if need is None
            else i18n.t("relations.progress", lang, into=into, need=need)
        )
        body = i18n.t(
            "relations.action_body",
            lang,
            actor=actor.mention,
            target=target.mention,
            hp=hp_gain,
            total=pair["hp"],
            level=level,
            progress=progress,
        )
        if bonus_note:
            body = f"{body}\n{bonus_note}"
        embed = embed_style.make_embed(
            title=i18n.t(
                "relations.action_title",
                lang,
                emoji=action["emoji"],
                action=i18n.t(f"relations.action.{action_id}", lang),
            ),
            description=body,
            color=embed_style.INFO,
        )
        await interaction.followup.send(embed=embed)

        if new_level > old_level:
            for m in (actor, target):
                best = relations_db.max_level_for_user(guild.id, m.id)
                await self._sync_roles(m, settings, best)
            await self._announce_level(guild, settings, actor, target, new_level, int(pair["hp"]))

    async def finalize_proposal_accept(
        self, interaction: discord.Interaction, view: ProposalView
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        lang = i18n.lang_for(guild.id)
        settings = relations_core.get_settings(guild.id)
        if not settings["enabled"] or not settings["marriage_enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.marriage.disabled", lang), ephemeral=True
            )
            return

        proposal = relations_db.get_proposal(guild.id, view.proposer_id, view.target_id)
        if proposal is None or proposal["expires_at"] < time.time():
            relations_db.clear_proposal(guild.id, view.proposer_id, view.target_id)
            await interaction.response.send_message(
                i18n.t("relations.propose.expired", lang), ephemeral=True
            )
            return

        if not settings["allow_polygamy"]:
            if relations_db.marriage_count(guild.id, view.proposer_id) > 0:
                await interaction.response.send_message(
                    i18n.t("relations.marriage.proposer_taken", lang), ephemeral=True
                )
                return
            if relations_db.marriage_count(guild.id, view.target_id) > 0:
                await interaction.response.send_message(
                    i18n.t("relations.marriage.target_taken", lang), ephemeral=True
                )
                return

        relations_db.create_marriage(guild.id, view.proposer_id, view.target_id)
        proposer = guild.get_member(view.proposer_id)
        target = guild.get_member(view.target_id)
        if isinstance(proposer, discord.Member):
            await self._sync_married_role(proposer, settings)
        if isinstance(target, discord.Member):
            await self._sync_married_role(target, settings)

        embed = embed_style.make_embed(
            title=i18n.t("relations.marriage.wed_title", lang),
            description=i18n.t(
                "relations.marriage.wed_body",
                lang,
                a=f"<@{view.proposer_id}>",
                b=f"<@{view.target_id}>",
            ),
            color=embed_style.SUCCESS,
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await self._announce(
            guild,
            settings,
            title=i18n.t("relations.marriage.announce_title", lang),
            description=i18n.t(
                "relations.marriage.announce_body",
                lang,
                a=f"<@{view.proposer_id}>",
                b=f"<@{view.target_id}>",
            ),
        )

    async def finalize_divorce(
        self, interaction: discord.Interaction, user_a: int, user_b: int
    ) -> None:
        guild = interaction.guild
        if guild is None:
            return
        lang = i18n.lang_for(guild.id)
        settings = relations_core.get_settings(guild.id)
        ok = relations_db.dissolve_marriage(guild.id, user_a, user_b)
        if not ok:
            await interaction.response.send_message(
                i18n.t("relations.divorce.not_married", lang), ephemeral=True
            )
            return
        for uid in (user_a, user_b):
            m = guild.get_member(uid)
            if isinstance(m, discord.Member):
                await self._sync_married_role(m, settings)
        embed = embed_style.make_embed(
            title=i18n.t("relations.divorce.done_title", lang),
            description=i18n.t(
                "relations.divorce.done_body",
                lang,
                a=f"<@{user_a}>",
                b=f"<@{user_b}>",
            ),
            color=self._color_danger(),
        )
        await interaction.response.edit_message(embed=embed, view=None)
        await self._announce(
            guild,
            settings,
            title=i18n.t("relations.divorce.announce_title", lang),
            description=i18n.t(
                "relations.divorce.announce_body",
                lang,
                a=f"<@{user_a}>",
                b=f"<@{user_b}>",
            ),
            color=self._color_danger(),
        )

    async def _card(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None,
    ) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        other = member or actor
        if other.id == actor.id:
            await interaction.response.send_message(
                i18n.t("relations.card_need_other", lang), ephemeral=True
            )
            return
        pair = relations_db.get_pair(guild.id, actor.id, other.id)
        if pair is None:
            await interaction.response.send_message(
                i18n.t("relations.card_empty", lang, user=other.mention),
                ephemeral=True,
            )
            return
        th = settings["level_thresholds"]
        level, into, need = relations_core.progress_to_next(int(pair["hp"]), th)
        progress = (
            i18n.t("relations.progress_max", lang)
            if need is None
            else i18n.t("relations.progress", lang, into=into, need=need)
        )
        married = relations_db.get_marriage(guild.id, actor.id, other.id)
        marriage_line = ""
        if married:
            days = relations_core.days_together(married["married_at"])
            marriage_line = "\n" + i18n.t(
                "relations.card_married", lang, days=days
            )
        embed = embed_style.make_embed(
            title=i18n.t("relations.card_title", lang),
            description=i18n.t(
                "relations.card_body",
                lang,
                a=actor.mention,
                b=other.mention,
                hp=pair["hp"],
                level=level,
                progress=progress,
            )
            + marriage_line,
            color=embed_style.INFO,
        )
        await interaction.response.send_message(embed=embed)

    async def _top(self, interaction: discord.Interaction) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, _actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        rows = relations_db.top_pairs(guild.id, 15)
        if not rows:
            await interaction.response.send_message(
                i18n.t("relations.top_empty", lang), ephemeral=True
            )
            return
        lines: list[str] = []
        for i, row in enumerate(rows, start=1):
            a = guild.get_member(int(row["user_a"]))
            b = guild.get_member(int(row["user_b"]))
            an = a.display_name if a else str(row["user_a"])
            bn = b.display_name if b else str(row["user_b"])
            ring = " 💍" if relations_db.are_married(guild.id, row["user_a"], row["user_b"]) else ""
            lines.append(
                i18n.t(
                    "relations.top_line",
                    lang,
                    n=i,
                    a=an,
                    b=bn,
                    level=row["level"],
                    hp=row["hp"],
                )
                + ring
            )
        embed = embed_style.make_embed(
            title=i18n.t("relations.top_title", lang),
            description="\n".join(lines),
            color=embed_style.INFO,
        )
        await interaction.response.send_message(embed=embed)

    async def _marry(self, interaction: discord.Interaction, member: discord.Member) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        if not settings["marriage_enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.marriage.disabled", lang), ephemeral=True
            )
            return
        if member.id == actor.id:
            await interaction.response.send_message(
                i18n.t("relations.self", lang), ephemeral=True
            )
            return
        if member.bot:
            await interaction.response.send_message(
                i18n.t("relations.bot_target", lang), ephemeral=True
            )
            return
        if relations_db.are_married(guild.id, actor.id, member.id):
            await interaction.response.send_message(
                i18n.t("relations.marriage.already", lang, user=member.mention),
                ephemeral=True,
            )
            return

        relations_db.clear_expired_proposals(guild.id)

        if not settings["allow_polygamy"]:
            if relations_db.marriage_count(guild.id, actor.id) > 0:
                await interaction.response.send_message(
                    i18n.t("relations.marriage.you_taken", lang), ephemeral=True
                )
                return
            if relations_db.marriage_count(guild.id, member.id) > 0:
                await interaction.response.send_message(
                    i18n.t("relations.marriage.they_taken", lang, user=member.mention),
                    ephemeral=True,
                )
                return

        pair = relations_db.get_pair(guild.id, actor.id, member.id)
        level = int(pair["level"]) if pair else 1
        min_lvl = int(settings["min_level_to_marry"])
        if level < min_lvl:
            await interaction.response.send_message(
                i18n.t(
                    "relations.marriage.level_low",
                    lang,
                    level=level,
                    need=min_lvl,
                ),
                ephemeral=True,
            )
            return

        if relations_db.has_outgoing_proposal(guild.id, actor.id):
            await interaction.response.send_message(
                i18n.t("relations.propose.already_out", lang), ephemeral=True
            )
            return

        timeout = int(settings["proposal_timeout_sec"])
        relations_db.upsert_proposal(guild.id, actor.id, member.id, timeout)
        view = ProposalView(
            self,
            guild_id=guild.id,
            proposer_id=actor.id,
            target_id=member.id,
            timeout=float(timeout),
            lang=lang,
        )
        embed = embed_style.make_embed(
            title=i18n.t("relations.propose.title", lang),
            description=i18n.t(
                "relations.propose.body",
                lang,
                proposer=actor.mention,
                target=member.mention,
                seconds=timeout,
            ),
            color=embed_style.SUCCESS,
        )
        await interaction.response.send_message(
            content=member.mention, embed=embed, view=view
        )
        view.message = await interaction.original_response()

    async def _divorce(
        self, interaction: discord.Interaction, member: discord.Member | None
    ) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        if not settings["marriage_enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.marriage.disabled", lang), ephemeral=True
            )
            return

        spouses = relations_db.get_spouses(guild.id, actor.id)
        if not spouses:
            await interaction.response.send_message(
                i18n.t("relations.divorce.not_married_you", lang), ephemeral=True
            )
            return

        spouse_id: int | None = None
        if member is not None:
            if not relations_db.are_married(guild.id, actor.id, member.id):
                await interaction.response.send_message(
                    i18n.t("relations.divorce.not_with", lang, user=member.mention),
                    ephemeral=True,
                )
                return
            spouse_id = member.id
        elif len(spouses) == 1:
            spouse_id = int(spouses[0]["spouse_id"])
        else:
            await interaction.response.send_message(
                i18n.t("relations.divorce.pick_spouse", lang), ephemeral=True
            )
            return

        mutual = bool(settings["divorce_requires_accept"])
        timeout = float(settings["proposal_timeout_sec"])
        view = DivorceView(
            self,
            guild_id=guild.id,
            initiator_id=actor.id,
            spouse_id=spouse_id,
            mutual=mutual,
            timeout=timeout,
            lang=lang,
        )
        if mutual:
            desc = i18n.t(
                "relations.divorce.mutual_body",
                lang,
                initiator=actor.mention,
                spouse=f"<@{spouse_id}>",
            )
        else:
            desc = i18n.t(
                "relations.divorce.solo_body",
                lang,
                spouse=f"<@{spouse_id}>",
            )
        embed = embed_style.make_embed(
            title=i18n.t("relations.divorce.title", lang),
            description=desc,
            color=self._color_danger(),
        )
        content = f"<@{spouse_id}>" if mutual else None
        await interaction.response.send_message(content=content, embed=embed, view=view)
        view.message = await interaction.original_response()

    async def _spouse(
        self, interaction: discord.Interaction, member: discord.Member | None
    ) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        subject = member or actor
        spouses = relations_db.get_spouses(guild.id, subject.id)
        if not spouses:
            key = (
                "relations.spouse.none_self"
                if subject.id == actor.id
                else "relations.spouse.none_other"
            )
            await interaction.response.send_message(
                i18n.t(key, lang, user=subject.mention), ephemeral=True
            )
            return
        lines: list[str] = []
        for m in spouses:
            sid = int(m["spouse_id"])
            sp = guild.get_member(sid)
            name = sp.mention if sp else f"<@{sid}>"
            days = relations_core.days_together(m["married_at"])
            pair = relations_db.get_pair(guild.id, subject.id, sid)
            hp = int(pair["hp"]) if pair else 0
            level = int(pair["level"]) if pair else 1
            lines.append(
                i18n.t(
                    "relations.spouse.line",
                    lang,
                    spouse=name,
                    days=days,
                    level=level,
                    hp=hp,
                )
            )
        embed = embed_style.make_embed(
            title=i18n.t("relations.spouse.title", lang, user=subject.display_name),
            description="\n".join(lines),
            color=embed_style.SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    async def _marriages_top(self, interaction: discord.Interaction) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, _actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        if not settings["marriage_enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.marriage.disabled", lang), ephemeral=True
            )
            return
        rows = relations_db.top_marriages(guild.id, 15)
        if not rows:
            await interaction.response.send_message(
                i18n.t("relations.marriages_top.empty", lang), ephemeral=True
            )
            return
        lines: list[str] = []
        for i, row in enumerate(rows, start=1):
            a = guild.get_member(int(row["user_a"]))
            b = guild.get_member(int(row["user_b"]))
            an = a.display_name if a else str(row["user_a"])
            bn = b.display_name if b else str(row["user_b"])
            days = relations_core.days_together(row["married_at"])
            lines.append(
                i18n.t(
                    "relations.marriages_top.line",
                    lang,
                    n=i,
                    a=an,
                    b=bn,
                    days=days,
                    level=row["level"],
                    hp=row["hp"],
                )
            )
        embed = embed_style.make_embed(
            title=i18n.t("relations.marriages_top.title", lang),
            description="\n".join(lines),
            color=embed_style.SUCCESS,
        )
        await interaction.response.send_message(embed=embed)

    async def _ship(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        other: discord.Member | None,
    ) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        left = other or actor
        right = member
        if left.id == right.id:
            await interaction.response.send_message(
                i18n.t("relations.ship.same", lang), ephemeral=True
            )
            return
        score = relations_core.ship_score(left.id, right.id)
        tier = i18n.t(relations_core.ship_label_key(score), lang)
        bar_filled = score // 10
        bar = "❤️" * bar_filled + "🖤" * (10 - bar_filled)
        embed = embed_style.make_embed(
            title=i18n.t("relations.ship.title", lang),
            description=i18n.t(
                "relations.ship.body",
                lang,
                a=left.mention,
                b=right.mention,
                score=score,
                tier=tier,
                bar=bar,
            ),
            color=embed_style.INFO,
        )
        await interaction.response.send_message(embed=embed)

    async def _date(self, interaction: discord.Interaction, member: discord.Member) -> None:
        ctx = self._require_enabled(interaction)
        if ctx is None:
            await interaction.response.send_message("Guild only.", ephemeral=True)
            return
        guild, actor, settings, lang = ctx
        if not settings["enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.disabled", lang), ephemeral=True
            )
            return
        if not settings["marriage_enabled"]:
            await interaction.response.send_message(
                i18n.t("relations.marriage.disabled", lang), ephemeral=True
            )
            return
        if member.id == actor.id:
            await interaction.response.send_message(
                i18n.t("relations.self", lang), ephemeral=True
            )
            return
        if not relations_db.are_married(guild.id, actor.id, member.id):
            await interaction.response.send_message(
                i18n.t("relations.date.need_spouse", lang), ephemeral=True
            )
            return

        day = self._day_key(guild.id)
        used = relations_db.daily_count(guild.id, actor.id, day)
        if used >= int(settings["max_actions_per_day"]):
            await interaction.response.send_message(
                i18n.t("relations.daily_limit", lang, limit=settings["max_actions_per_day"]),
                ephemeral=True,
            )
            return

        remaining = relations_db.cooldown_remaining(
            guild.id, actor.id, member.id, DATE_ACTION_ID
        )
        if remaining > 0:
            await interaction.response.send_message(
                i18n.t("relations.cooldown", lang, seconds=int(remaining) + 1),
                ephemeral=True,
            )
            return

        await interaction.response.defer()
        hp_gain = int(settings["date_hp_gain"])
        if int(settings["married_hp_bonus_percent"]) > 0:
            hp_gain = relations_core.apply_married_bonus(
                hp_gain, int(settings["married_hp_bonus_percent"])
            )
        thresholds = settings["level_thresholds"]

        def _lvl(hp: int) -> int:
            return relations_core.level_for_hp(hp, thresholds)

        pair, old_level, new_level = relations_db.apply_action_hp(
            guild.id, actor.id, member.id, hp_gain, _lvl
        )
        relations_db.set_cooldown(
            guild.id, actor.id, member.id, DATE_ACTION_ID, int(settings["date_cooldown_sec"])
        )
        relations_db.bump_daily(guild.id, actor.id, day)

        level, into, need = relations_core.progress_to_next(int(pair["hp"]), thresholds)
        progress = (
            i18n.t("relations.progress_max", lang)
            if need is None
            else i18n.t("relations.progress", lang, into=into, need=need)
        )
        embed = embed_style.make_embed(
            title=i18n.t("relations.date.title", lang),
            description=i18n.t(
                "relations.date.body",
                lang,
                a=actor.mention,
                b=member.mention,
                hp=hp_gain,
                total=pair["hp"],
                level=level,
                progress=progress,
            ),
            color=embed_style.SUCCESS,
        )
        await interaction.followup.send(embed=embed)
        if new_level > old_level:
            for m in (actor, member):
                best = relations_db.max_level_for_user(guild.id, m.id)
                await self._sync_roles(m, settings, best)
            await self._announce_level(guild, settings, actor, member, new_level, int(pair["hp"]))

    # --- slash commands (group /relations) ---

    @relations_group.command(name="hug", description="Hug a member and gain relationship HP")
    @app_commands.describe(member="Who to hug")
    async def relations_hug(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "hug", member)

    @relations_group.command(name="kiss", description="Kiss a member and gain relationship HP")
    @app_commands.describe(member="Who to kiss")
    async def relations_kiss(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "kiss", member)

    @relations_group.command(name="slap", description="Slap a member and gain relationship HP")
    @app_commands.describe(member="Who to slap")
    async def relations_slap(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "slap", member)

    @relations_group.command(name="pat", description="Pat a member and gain relationship HP")
    @app_commands.describe(member="Who to pat")
    async def relations_pat(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "pat", member)

    @relations_group.command(name="highfive", description="High-five a member and gain relationship HP")
    @app_commands.describe(member="Who to high-five")
    async def relations_highfive(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "highfive", member)

    @relations_group.command(name="cuddle", description="Cuddle a member and gain relationship HP")
    @app_commands.describe(member="Who to cuddle")
    async def relations_cuddle(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "cuddle", member)

    @relations_group.command(name="poke", description="Poke a member and gain relationship HP")
    @app_commands.describe(member="Who to poke")
    async def relations_poke(self, interaction: discord.Interaction, member: discord.Member):
        await self._run_action(interaction, "poke", member)

    @relations_group.command(
        name="card",
        description="Pair card with a member, or your marriage status if omitted",
    )
    @app_commands.describe(member="Other member (omit to show your spouse / marriages)")
    async def relations_card(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ):
        # Merged former /spouse: no member → own marriages; with member → pair HP card.
        if member is None:
            await self._spouse(interaction, None)
        else:
            await self._card(interaction, member)

    @relations_group.command(name="top", description="Top relationship pairs on this server")
    async def relations_top(self, interaction: discord.Interaction):
        await self._top(interaction)

    @relations_group.command(name="marry", description="Propose marriage to a member")
    @app_commands.describe(member="Who to propose to")
    async def relations_marry(self, interaction: discord.Interaction, member: discord.Member):
        await self._marry(interaction, member)

    @relations_group.command(name="divorce", description="Start a divorce with your spouse")
    @app_commands.describe(member="Spouse (required if polygamy / multiple spouses)")
    async def relations_divorce(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ):
        await self._divorce(interaction, member)

    @relations_group.command(name="marriages-top", description="Longest marriages on this server")
    async def relations_marriages_top(self, interaction: discord.Interaction):
        await self._marriages_top(interaction)

    @relations_group.command(name="ship", description="Compatibility meter between two members")
    @app_commands.describe(
        member="First member",
        other="Second member (default: you)",
    )
    async def relations_ship(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        other: discord.Member | None = None,
    ):
        await self._ship(interaction, member, other)

    @relations_group.command(name="date", description="Go on a date with your spouse (bonus HP)")
    @app_commands.describe(member="Your spouse")
    async def relations_date(self, interaction: discord.Interaction, member: discord.Member):
        await self._date(interaction, member)


async def setup(bot: commands.Bot):
    relations_db.init()
    cog = RelationsCog(bot)
    slash_registry.register_relations(cog)
    await bot.add_cog(cog)
