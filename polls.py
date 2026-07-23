"""Polls cog: create with buttons, end on timer, announce results."""

import logging
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

import i18n
import polls_db
import slash_registry

logger = logging.getLogger("polls")


class PollView(discord.ui.View):
    def __init__(self, poll_id: int, options: list[str]):
        super().__init__(timeout=None)
        self.poll_id = poll_id
        for i, opt in enumerate(options[:5]):
            button = discord.ui.Button(
                label=opt[:80],
                style=discord.ButtonStyle.primary,
                custom_id=f"poll:{poll_id}:{i}",
            )
            button.callback = self._make_cb(i)
            self.add_item(button)

    def _make_cb(self, index: int):
        async def callback(interaction: discord.Interaction):
            lang = i18n.lang_for(interaction.guild_id)
            ok = polls_db.vote(self.poll_id, interaction.user.id, index)
            if not ok:
                return await interaction.response.send_message(
                    i18n.t("polls.error.closed", lang), ephemeral=True
                )
            await interaction.response.send_message(
                i18n.t("polls.voted", lang, option=index + 1), ephemeral=True
            )

        return callback


def build_poll_embed(poll: dict, lang: str, *, results: list[int] | None = None) -> discord.Embed:
    embed = discord.Embed(
        title=i18n.t("polls.embed.title", lang),
        description=poll["question"],
        color=discord.Color.blurple() if not poll.get("ended") else discord.Color.green(),
        timestamp=discord.utils.utcnow(),
    )
    lines = []
    tallies = results if results is not None else polls_db.tallies(poll["id"])
    total = sum(tallies) or 1
    for i, opt in enumerate(poll["options"]):
        count = tallies[i] if i < len(tallies) else 0
        if poll.get("ended") or results is not None:
            pct = int(round(100 * count / total))
            lines.append(f"**{i + 1}.** {opt} — {count} ({pct}%)")
        else:
            lines.append(f"**{i + 1}.** {opt}")
    embed.add_field(name=i18n.t("polls.embed.options", lang), value="\n".join(lines), inline=False)
    if not poll.get("ended"):
        embed.set_footer(text=i18n.t("polls.embed.ends", lang, ends_at=poll["ends_at"]))
    return embed


class PollsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.end_loop.start()

    def cog_unload(self):
        self.end_loop.cancel()

    @app_commands.command(name="poll", description="Create a poll with up to 5 options")
    @app_commands.describe(
        question="Poll question",
        option1="Option 1",
        option2="Option 2",
        option3="Option 3 (optional)",
        option4="Option 4 (optional)",
        option5="Option 5 (optional)",
        minutes="Duration in minutes (default 60)",
    )
    @app_commands.default_permissions(manage_messages=True)
    async def poll_command(
        self,
        interaction: discord.Interaction,
        question: str,
        option1: str,
        option2: str,
        option3: str | None = None,
        option4: str | None = None,
        option5: str | None = None,
        minutes: app_commands.Range[int, 1, 10080] = 60,
    ):
        lang = i18n.lang_for(interaction.guild_id)
        options = [o.strip() for o in (option1, option2, option3, option4, option5) if o and o.strip()]
        if len(options) < 2:
            return await interaction.response.send_message(
                i18n.t("polls.error.min_options", lang), ephemeral=True
            )
        ends_at = (datetime.now(timezone.utc) + timedelta(minutes=int(minutes))).isoformat()
        poll = polls_db.create(
            interaction.guild.id,
            interaction.channel.id,
            question.strip()[:300],
            options,
            ends_at,
            created_by=interaction.user.id,
        )
        embed = build_poll_embed(poll, lang)
        view = PollView(poll["id"], options)
        await interaction.response.send_message(embed=embed, view=view)
        msg = await interaction.original_response()
        polls_db.set_message_id(poll["id"], msg.id)
        self.bot.add_view(view, message_id=msg.id)

    async def end_poll(self, poll: dict) -> None:
        if poll.get("ended"):
            return
        polls_db.mark_ended(poll["id"])
        poll = polls_db.get(poll["id"])
        if not poll:
            return
        lang = i18n.lang_for(poll["guild_id"])
        channel = self.bot.get_channel(poll["channel_id"])
        if channel is None:
            return
        tallies = polls_db.tallies(poll["id"])
        embed = build_poll_embed(poll, lang, results=tallies)
        try:
            if poll.get("message_id"):
                msg = await channel.fetch_message(poll["message_id"])
                await msg.edit(embed=embed, view=None)
            await channel.send(content=i18n.t("polls.ended", lang), embed=embed)
        except discord.HTTPException:
            logger.warning("poll end failed id=%s", poll["id"])

    @tasks.loop(minutes=1)
    async def end_loop(self):
        try:
            for poll in polls_db.due_to_end():
                await self.end_poll(poll)
        except Exception:
            logger.exception("polls end_loop error")

    @end_loop.before_loop
    async def before_end(self):
        await self.bot.wait_until_ready()
        # Re-attach views for active polls
        for guild in self.bot.guilds:
            for poll in polls_db.list_for_guild(guild.id, limit=20):
                if not poll["ended"] and poll.get("message_id"):
                    self.bot.add_view(PollView(poll["id"], poll["options"]), message_id=poll["message_id"])


async def setup(bot: commands.Bot):
    polls_db.init()
    cog = PollsCog(bot)
    slash_registry.register_polls(cog)
    await bot.add_cog(cog)
