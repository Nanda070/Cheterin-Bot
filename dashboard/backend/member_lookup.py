import discord


class MemberLookupResult:
    def __init__(self, member=None, not_found=False, service_error=False):
        self.member = member
        self.not_found = not_found
        self.service_error = service_error


async def resolve_guild_member(bot, guild_id: int, user_id: int) -> MemberLookupResult:
    guild = bot.get_guild(guild_id)
    if guild is None:
        return MemberLookupResult(service_error=True)

    member = guild.get_member(user_id)
    if member is not None:
        return MemberLookupResult(member=member)

    try:
        member = await guild.fetch_member(user_id)
        return MemberLookupResult(member=member)
    except discord.NotFound:
        return MemberLookupResult(not_found=True)
    except discord.HTTPException:
        return MemberLookupResult(service_error=True)
