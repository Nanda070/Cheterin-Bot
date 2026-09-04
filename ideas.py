"""Guild-scoped Discord intake and publication flow for ideas."""

from __future__ import annotations

import discord
from discord.ext import commands

import i18n
import ideas_core


class IdeasCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def publish_case(self, guild: discord.Guild | None, case: dict) -> None:
        if guild is None:
            return
        settings = ideas_core.get_settings(guild.id)
        channel_id = settings["channel_id"]
        channel = guild.get_channel(int(channel_id)) if channel_id.isdigit() else None
        if not isinstance(channel, discord.TextChannel):
            return
        lang = i18n.lang_for(guild.id)
        member = guild.get_member(int(case["submitter_id"]))
        author = member.mention if member else f"<@{case['submitter_id']}>"
        embed = discord.Embed(description=case["text"], color=discord.Colour.blurple())
        embed.set_author(name=i18n.t("ideas.embed.author", lang, author=author))
        if case.get("attachment_url"):
            embed.set_image(url=case["attachment_url"])
        message = await channel.send(embed=embed)
        for emoji in settings["vote_emojis"]:
            try:
                await message.add_reaction(emoji)
            except discord.HTTPException:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        settings = ideas_core.get_settings(message.guild.id)
        if not settings["enabled"] or str(message.channel.id) != settings["intake_channel_id"]:
            return
        text = (message.content or "").strip()
        attachment = message.attachments[0].url if message.attachments else ""
        if not text and not attachment:
            return
        case = ideas_core.create_case(
            message.guild.id, message.author.id, text or "(attachment)", attachment
        )
        review_id = settings["review_channel_id"]
        review = message.guild.get_channel(int(review_id)) if review_id.isdigit() else None
        if isinstance(review, discord.TextChannel):
            lang = i18n.lang_for(message.guild.id)
            await review.send(
                i18n.t(
                    "ideas.review.notify",
                    lang,
                    case_id=case["case_id"],
                    author=message.author.mention,
                    text=case["text"],
                )
            )
        try:
            await message.delete()
        except discord.HTTPException:
            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(IdeasCog(bot))
