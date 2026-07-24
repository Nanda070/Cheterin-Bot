"""Invite tracker cog: snapshot invites, attribute joins."""

import logging

import discord
from discord.ext import commands

import i18n
import invites_core
import invites_db

logger = logging.getLogger("invites")


class InvitesCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cache: dict[int, dict[str, int]] = {}  # guild_id -> {code: uses}

    async def _refresh_guild(self, guild: discord.Guild) -> None:
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            return
        except discord.HTTPException:
            logger.exception("Failed to fetch invites guild=%s", guild.id)
            return
        snapshot = {}
        for inv in invites:
            uses = inv.uses or 0
            snapshot[inv.code] = uses
            inviter_id = inv.inviter.id if inv.inviter else None
            invites_db.upsert_snapshot(guild.id, inv.code, inviter_id, uses)
        self._cache[guild.id] = snapshot

    @commands.Cog.listener()
    async def on_ready(self):
        invites_db.init()
        for guild in self.bot.guilds:
            if invites_core.get_settings(guild.id)["enabled"]:
                await self._refresh_guild(guild)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        if invites_core.get_settings(guild.id)["enabled"]:
            await self._refresh_guild(guild)

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild is None:
            return
        if not invites_core.get_settings(invite.guild.id)["enabled"]:
            return
        inviter_id = invite.inviter.id if invite.inviter else None
        invites_db.upsert_snapshot(invite.guild.id, invite.code, inviter_id, invite.uses or 0)
        self._cache.setdefault(invite.guild.id, {})[invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        settings = invites_core.get_settings(member.guild.id)
        if not settings["enabled"]:
            return

        before = self._cache.get(member.guild.id, {})
        used_code = None
        inviter_id = None
        try:
            invites = await member.guild.invites()
        except (discord.Forbidden, discord.HTTPException):
            invites = []

        after = {}
        for inv in invites:
            uses = inv.uses or 0
            after[inv.code] = uses
            prev = before.get(inv.code, 0)
            if uses > prev and used_code is None:
                used_code = inv.code
                inviter_id = inv.inviter.id if inv.inviter else None
            invites_db.upsert_snapshot(member.guild.id, inv.code, inv.inviter.id if inv.inviter else None, uses)

        self._cache[member.guild.id] = after
        invites_db.record_join(member.guild.id, member.id, inviter_id, used_code)

        if not (settings["welcome_mention"] or settings["log_channel_id"]):
            return

        lang = i18n.lang_for(member.guild.id)
        inviter_mention = f"<@{inviter_id}>" if inviter_id else i18n.t("invites.unknown", lang)
        total = 0
        if inviter_id is not None:
            for row in invites_db.inviter_stats(member.guild.id):
                if row["inviter_id"] == inviter_id:
                    total = int(row["joins"])
                    break

        channel_id = settings["log_channel_id"]
        channel = member.guild.get_channel(int(channel_id)) if channel_id else None
        if channel is None and settings["welcome_mention"]:
            channel = member.guild.system_channel
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=i18n.t("welcome.invite_log_title", lang),
            description=i18n.t(
                "welcome.invite_log_body",
                lang,
                inviter=inviter_mention,
                member=member.mention,
                code=used_code or "—",
                invites=total,
            ),
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    invites_db.init()
    await bot.add_cog(InvitesCog(bot))
