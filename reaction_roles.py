import json
import logging
import os

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

CONFIG_FILE = "reaction_roles.json"


def load_config() -> dict:
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_config(data: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def get_pairs_for_message(message_id: str) -> list | None:
    config = load_config()
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

    pairs = get_pairs_for_message(str(payload.message_id))
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
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "add")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        await handle_reaction_change(self.bot, payload, "remove")


async def cleanup_missing_messages(bot, guild_id: int) -> int:
    """Removes config entries whose message or channel no longer exists.

    Returns the number of entries removed."""
    config = load_config()
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
        save_config(config)
    return removed


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))
    guild_id_raw = os.getenv("GUILD_ID")
    if guild_id_raw:
        await cleanup_missing_messages(bot, int(guild_id_raw))
