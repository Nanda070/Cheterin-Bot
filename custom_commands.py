"""Custom commands / auto-replies cog."""

import logging

import discord
from discord.ext import commands

import embed_style
import custom_commands_core
import i18n
from message_template_core import normalize_embed_spec, substitute_embed_spec

logger = logging.getLogger("custom_commands")


def _embed_from_spec(spec: dict | None, lang: str) -> discord.Embed | None:
    if not spec:
        return None
    normalized = normalize_embed_spec(spec)
    rendered = substitute_embed_spec(normalized, {})
    color = embed_style.INFO
    raw_color = (rendered.get("color") or "").strip()
    if raw_color.startswith("#") and len(raw_color) == 7:
        try:
            color = discord.Color(int(raw_color[1:], 16))
        except ValueError:
            pass
    embed = discord.Embed(
        title=rendered.get("title") or None,
        description=rendered.get("description") or None,
        url=rendered.get("url") or None,
        color=color,
    )
    for field in rendered.get("fields") or []:
        if field.get("name") and field.get("value"):
            embed.add_field(name=field["name"], value=field["value"], inline=bool(field.get("inline")))
    footer = rendered.get("footer") or {}
    if footer.get("text"):
        embed.set_footer(text=footer["text"], icon_url=footer.get("icon_url") or None)
    return embed


class CustomCommandsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None:
            return
        cmd = custom_commands_core.match_message(message.guild.id, message.content or "")
        if cmd is None:
            return
        lang = i18n.lang_for(message.guild.id)
        embed = _embed_from_spec(cmd.get("embed"), lang)
        content = (cmd.get("reply_text") or "").strip() or None
        if not content and embed is None:
            return
        try:
            await message.channel.send(content=content, embed=embed)
        except discord.HTTPException:
            logger.warning("custom_commands reply failed guild=%s", message.guild.id)


async def setup(bot: commands.Bot):
    await bot.add_cog(CustomCommandsCog(bot))
