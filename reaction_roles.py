import logging

import discord
from discord.ext import commands

import settings_db

logger = logging.getLogger(__name__)

MODULE_NAME = "reaction_roles"


def load_config(guild_id: int) -> dict:
    return settings_db.get(guild_id, MODULE_NAME)


def save_config(guild_id: int, data: dict) -> None:
    settings_db.put(guild_id, MODULE_NAME, data)


def get_pairs_for_message(guild_id: int, message_id: str) -> list | None:
    config = load_config(guild_id)
    entry = config.get(str(message_id))
    return entry["pairs"] if entry else None


def find_pair_by_emoji(pairs: list, emoji_str: str) -> dict | None:
    for pair in pairs:
        if pair["emoji"] == emoji_str:
            return pair
    return None


def has_duplicate_emoji(pairs: list) -> bool:
    emojis = [p["emoji"] for p in pairs]
    return len(emojis) != len(set(emojis))


async def resolve_reacting_member(guild, user_id: int):
    member = guild.get_member(user_id)
    if member is not None:
        return member
    try:
        return await guild.fetch_member(user_id)
    except discord.HTTPException:
        return None


def build_reason(action: str, message_id) -> str:
    return f"Reaction role: {action} — by reaction on message {message_id}"


async def handle_reaction_change(bot, payload, action: str) -> None:
    if payload.user_id == bot.user.id:
        return

    pairs = get_pairs_for_message(payload.guild_id, str(payload.message_id))
    if pairs is None:
        return

    pair = find_pair_by_emoji(pairs, str(payload.emoji))
    if pair is None:
        return

    guild = bot.get_guild(payload.guild_id)
    if guild is None:
        return

    role = guild.get_role(int(pair["role_id"]))
    if role is None:
        return

    if action == "add" and payload.member is not None:
        member = payload.member
    else:
        member = await resolve_reacting_member(guild, payload.user_id)
    if member is None:
        return

    reason = build_reason(action, payload.message_id)
    try:
        if action == "add":
            await member.add_roles(role, reason=reason)
        else:
            await member.remove_roles(role, reason=reason)
    except discord.HTTPException as exc:
        logger.warning(
            "Failed to %s role %s for member %s on reaction role message %s: %s",
            action, role.id, member.id, payload.message_id, exc,
        )
        return


class ReactionRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Фаза 2.4: чистим «мёртвые» записи по всем серверам, где есть бот
        # (раньше — только по мейн-серверу из GUILD_ID). Один раз за процесс.
        if getattr(self.bot, "_reaction_roles_cleaned", False):
            return
        self.bot._reaction_roles_cleaned = True
        for guild in self.bot.guilds:
            try:
                await cleanup_missing_messages(self.bot, guild.id)
            except Exception:
                logger.exception("reaction_roles: ошибка очистки для guild=%s", guild.id)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "remove")


async def cleanup_missing_messages(bot, guild_id: int) -> int:
    """Removes config entries whose message or channel no longer exists.

    Returns the number of entries removed."""
    config = load_config(guild_id)
    guild = bot.get_guild(guild_id)
    if guild is None:
        return 0

    removed = 0
    for message_id, entry in list(config.items()):
        channel = guild.get_channel(int(entry["channel_id"]))
        if channel is None:
            del config[message_id]
            removed += 1
            continue
        try:
            await channel.fetch_message(int(message_id))
        except discord.NotFound:
            del config[message_id]
            removed += 1
        except discord.HTTPException:
            continue

    if removed:
        save_config(guild_id, config)
    return removed


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
